import json
import os
import subprocess
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import pytest

import generate_marketplaces

DECLARED: dict[str, list[str]] = {}


def declared_reader(repository, revision, names):
    return {name: DECLARED.get(name, []) for name in names}


def declare(plugins):
    DECLARED.clear()
    entries = []
    for plugin in plugins:
        plugin = dict(plugin)
        DECLARED[plugin["name"]] = plugin.pop("requires", [])
        entries.append(plugin)
    return entries


def committed_reader(repository, revision, names):
    catalog = json.loads((generate_marketplaces.OUTPUTS["claude"]).read_text(encoding="utf-8"))
    entries = {entry["name"]: entry.get("dependencies", []) for entry in catalog["plugins"]}
    return {name: entries[name] for name in names}


class RootFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        root_patch = patch.object(generate_marketplaces, "ROOT", self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)


class InstructionPairTests(RootFixtureTests):
    def test_agents_without_claude_fails(self):
        (self.root / "AGENTS.md").write_text("# Instructions\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "sibling CLAUDE.md"):
            generate_marketplaces.validate_instruction_pairs()

    def test_claude_without_agents_fails_even_in_hidden_directory(self):
        directory = self.root / ".claude"
        directory.mkdir()
        (directory / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "sibling AGENTS.md"):
            generate_marketplaces.validate_instruction_pairs()

    def test_only_the_pointer_is_accepted(self):
        (self.root / "AGENTS.md").write_text("# Instructions\n", encoding="utf-8")
        claude = self.root / "CLAUDE.md"
        claude.write_text("duplicated instructions\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "must contain only"):
            generate_marketplaces.validate_instruction_pairs()
        claude.write_text("@AGENTS.md\n", encoding="utf-8")
        generate_marketplaces.validate_instruction_pairs()


class PluginsFixtureTests(RootFixtureTests):
    def write_plugins_file(self, plugins):
        roster = {
            "name": "tj-agents",
            "description": "Test marketplace",
            "owner": "Tommy Seery",
            "plugins": [{"revision": "a" * 40, "kind": "shared", **plugin} for plugin in declare(plugins)],
        }
        (self.root / "plugins.json").write_text(json.dumps(roster), encoding="utf-8")


class ValidationErrorTests(PluginsFixtureTests):
    def test_duplicate_plugin_name_fails(self):
        self.write_plugins_file([
            {"name": "base", "repository": "core"},
            {"name": "base", "repository": "other"},
        ])
        with self.assertRaisesRegex(ValueError, "Duplicate plugin: base"):
            generate_marketplaces.build(declared_reader)

    def test_legacy_release_fields_are_rejected(self):
        for field, value in (("release", "pkg@1.2.3"), ("commit", "a" * 40), ("version", "1.2.3")):
            with self.subTest(field=field, value=value):
                self.write_plugins_file([{"name": "base", "repository": "core", field: value}])
                with self.assertRaisesRegex(ValueError, f"Unknown fields in plugin entry.*{field}"):
                    generate_marketplaces.build(declared_reader)

    def test_unknown_dependency_fails(self):
        self.write_plugins_file([{"name": "engineering", "repository": "core", "requires": ["base"]}])
        with self.assertRaisesRegex(ValueError, "engineering depends on 'base', which is not in the roster"):
            generate_marketplaces.build(declared_reader)

    def test_hand_written_requires_is_rejected(self):
        roster = {"name": "tj-agents", "description": "Test marketplace", "owner": "Tommy Seery", "plugins": [
            {"name": "base", "repository": "core", "revision": "a" * 40, "kind": "shared", "requires": []}]}
        (self.root / "plugins.json").write_text(json.dumps(roster), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Unknown fields in plugin entry.*requires"):
            generate_marketplaces.build(declared_reader)

    def test_each_pinned_revision_is_read_once_for_all_its_plugins(self):
        self.write_plugins_file([
            {"name": "base", "repository": "core"},
            {"name": "engineering", "repository": "core", "requires": ["base"]},
            {"name": "cli", "repository": "cli", "requires": ["base"]},
        ])
        calls = []

        def reader(repository, revision, names):
            calls.append((repository, revision, sorted(names)))
            return declared_reader(repository, revision, names)

        generate_marketplaces.build(reader)
        self.assertEqual(
            sorted([("cli", "a" * 40, ["cli"]), ("core", "a" * 40, ["base", "engineering"])]), sorted(calls)
        )

    def test_external_runtime_does_not_inherit_engineering_from_its_repository(self):
        self.write_plugins_file([
            {"name": "base", "repository": "core"},
            {"name": "engineering", "repository": "core", "requires": ["base"]},
            {"name": "cli", "repository": "cli", "requires": ["base"]},
        ])
        outputs = generate_marketplaces.build(declared_reader)
        entries = {entry["name"]: entry for entry in json.loads(outputs["claude"])["plugins"]}
        self.assertEqual(["base"], entries["cli"]["dependencies"])

    def test_transitive_engineering_requirement_is_accepted(self):
        self.write_plugins_file([
            {"name": "engineering", "repository": "core"},
            {"name": "dotnet", "repository": "dotnet", "requires": ["engineering"]},
            {"name": "efcore", "repository": "dotnet", "requires": ["dotnet"]},
        ])
        generate_marketplaces.build(declared_reader)

    def test_dependency_cycle_fails(self):
        self.write_plugins_file([
            {"name": "base", "repository": "core", "requires": ["workflow"]},
            {"name": "workflow", "repository": "core", "requires": ["base"]},
        ])
        with self.assertRaisesRegex(ValueError, "form a cycle"):
            generate_marketplaces.build(declared_reader)


class OutputShapeTests(PluginsFixtureTests):
    def setUp(self):
        super().setUp()
        self.write_plugins_file([
            {"name": "base", "repository": "core"},
            {"name": "engineering", "repository": "core", "requires": ["base"]},
            {"name": "nvim", "repository": "nvim", "requires": ["engineering"]},
        ])
        self.outputs = generate_marketplaces.build(declared_reader)
        self.claude = json.loads(self.outputs["claude"])
        self.codex = json.loads(self.outputs["codex"])

    def test_every_entry_pins_its_revision_in_both_manifests(self):
        for manifest in (self.claude, self.codex):
            for entry in manifest["plugins"]:
                self.assertEqual(entry["source"]["sha"], "a" * 40)
                self.assertNotIn("ref", entry["source"])

    def test_every_codex_entry_is_available(self):
        for entry in self.codex["plugins"]:
            self.assertEqual(entry["policy"]["installation"], "AVAILABLE")

    def test_claude_entries_have_no_policy_key(self):
        for entry in self.claude["plugins"]:
            self.assertNotIn("policy", entry)

    def test_claude_entries_declare_manifest_dependencies(self):
        dependencies = {entry["name"]: entry.get("dependencies") for entry in self.claude["plugins"]}
        self.assertEqual({"base": None, "engineering": ["base"], "nvim": ["engineering"]}, dependencies)

    def test_codex_entries_have_no_dependencies_key(self):
        for entry in self.codex["plugins"]:
            self.assertNotIn("dependencies", entry)

    def test_marketplace_name_is_tj_agents(self):
        self.assertEqual(self.claude["name"], "tj-agents")
        self.assertEqual(self.codex["name"], "tj-agents")

    def test_emission_is_byte_stable(self):
        self.assertEqual(generate_marketplaces.build(declared_reader), self.outputs)


class ManifestDependencyTests(unittest.TestCase):
    def test_bare_and_marketplace_qualified_dependencies_are_names(self):
        document = {"name": "work", "dependencies": ["base@tj-agents", "teams"]}
        self.assertEqual(["base", "teams"], generate_marketplaces.manifest_dependency_names(document, "work", "work"))

    def test_a_manifest_without_dependencies_has_none(self):
        self.assertEqual([], generate_marketplaces.manifest_dependency_names({"name": "docs"}, "docs", "core"))

    def test_a_dependency_from_another_marketplace_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside the tj-agents marketplace"):
            generate_marketplaces.manifest_dependency_names({"name": "work", "dependencies": ["x@other"]}, "work", "work")

    def test_a_manifest_for_another_plugin_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must name work"):
            generate_marketplaces.manifest_dependency_names({"name": "teams"}, "work", "work")


class RealRosterTests(unittest.TestCase):
    def test_build_reproduces_the_committed_catalogs_from_the_real_roster(self):
        outputs = generate_marketplaces.build(committed_reader)
        for host, path in generate_marketplaces.OUTPUTS.items():
            self.assertEqual(path.read_bytes(), outputs[host])
        roster = json.loads((generate_marketplaces.ROOT / "plugins.json").read_text(encoding="utf-8"))
        by_name = {plugin["name"]: plugin for plugin in roster["plugins"]}
        for output in outputs.values():
            for entry in json.loads(output)["plugins"]:
                self.assertEqual(entry["source"]["sha"], by_name[entry["name"]]["revision"])
                self.assertEqual(entry["source"]["path"], f"./plugins/{entry['name']}")


def write_roster(root: Path, plugins: list[dict[str, object]]) -> None:
    roster = {
        "name": "tj-agents",
        "description": "Test marketplace",
        "owner": "Tommy Seery",
        "plugins": [{"revision": "a" * 40, "kind": "shared", **plugin} for plugin in declare(plugins)],
    }
    (root / "plugins.json").write_text(json.dumps(roster), encoding="utf-8")


@pytest.fixture
def roster_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(generate_marketplaces, "ROOT", tmp_path)
    return tmp_path


def test_build_accepts_an_organization_extending_and_requiring_a_profile(roster_root: Path) -> None:
    write_roster(roster_root, [
        {"name": "work", "repository": "work", "kind": "profile"},
        {"name": "acme", "repository": "acme", "requires": ["work"], "kind": "organization", "extends": "work"},
    ])
    generate_marketplaces.build(declared_reader)


@pytest.mark.parametrize(
    ("plugins", "message"),
    [
        (
            [{"name": "work", "repository": "work", "kind": None}],
            "Plugin kind must be one of shared, profile, organization: work",
        ),
        (
            [{"name": "work", "repository": "work", "kind": "generic"}],
            "Plugin kind must be one of shared, profile, organization: work",
        ),
        (
            [
                {"name": "work", "repository": "work", "kind": "profile"},
                {"name": "teams", "repository": "work", "extends": "work"},
            ],
            "Only an organization can use extends: teams",
        ),
        (
            [{"name": "acme", "repository": "acme", "kind": "organization"}],
            "Organization acme must extend a profile",
        ),
        (
            [
                {"name": "engineering", "repository": "core"},
                {"name": "acme", "repository": "acme", "requires": ["engineering"], "kind": "organization",
                 "extends": "engineering"},
            ],
            "Organization acme must extend a profile",
        ),
        (
            [
                {"name": "work", "repository": "work", "kind": "profile"},
                {"name": "acme", "repository": "acme", "kind": "organization", "extends": "work"},
            ],
            "Organization acme must depend on work, the profile it extends",
        ),
    ],
)
def test_build_rejects_an_invalid_kind(
    roster_root: Path, plugins: list[dict[str, object]], message: str
) -> None:
    write_roster(roster_root, plugins)
    with pytest.raises(ValueError, match=message):
        generate_marketplaces.build(declared_reader)


@pytest.mark.parametrize("field", ["profile", "generic_profile"])
def test_build_rejects_the_replaced_profile_fields(roster_root: Path, field: str) -> None:
    write_roster(roster_root, [{"name": "work", "repository": "work", "kind": "profile", field: True}])
    with pytest.raises(ValueError, match=rf"Unknown fields in plugin entry: \['{field}'\]"):
        generate_marketplaces.build(declared_reader)


def test_build_requires_every_entry_to_declare_its_kind(roster_root: Path) -> None:
    roster = {
        "name": "tj-agents", "description": "Test marketplace", "owner": "Tommy Seery",
        "plugins": [{"name": "base", "repository": "core", "revision": "a" * 40}],
    }
    (roster_root / "plugins.json").write_text(json.dumps(roster), encoding="utf-8")
    with pytest.raises(ValueError, match="Plugin kind must be one of shared, profile, organization: base"):
        generate_marketplaces.build(declared_reader)


def test_real_roster_declares_profile_kinds() -> None:
    roster = json.loads((generate_marketplaces.ROOT / "plugins.json").read_text(encoding="utf-8"))
    kinds = {plugin["name"]: plugin["kind"] for plugin in roster["plugins"]}
    assert {name for name, kind in kinds.items() if kind == "profile"} == {"personal", "work"}


@pytest.mark.parametrize(
    ("dependencies", "message"),
    [
        ("base", "must be a list"),
        ([42], "must be a plugin identity"),
        ([""], "not a plugin identity"),
        (["base@"], "not a plugin identity"),
        (["base@tj-agents", "base"], "repeats dependency"),
    ],
)
def test_invalid_manifest_dependencies_fail(dependencies: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        generate_marketplaces.manifest_dependency_names(
            {"name": "work", "dependencies": dependencies}, "work", "work"
        )


def test_manifest_reader_uses_the_pinned_commit_and_rejects_missing_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GIT_CONFIG_COUNT", "0")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    producer = tmp_path / "producer"
    producer.mkdir()

    def git(*arguments: str) -> str:
        return subprocess.run(
            ["git", "-C", str(producer), *arguments],
            check=True, capture_output=True, text=True, encoding="utf-8", timeout=15,
        ).stdout.strip()

    git("init", "--quiet")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "commit.gpgsign", "false")
    manifest = producer / "plugins/work/.claude-plugin/plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text('{"name":"work","dependencies":["base@tj-agents"]}', encoding="utf-8")
    dependency = producer / "plugins/base/.claude-plugin/plugin.json"
    dependency.parent.mkdir(parents=True)
    dependency.write_text('{"name":"base"}', encoding="utf-8")
    git("add", ".")
    git("commit", "--quiet", "-m", "Published payload")
    revision = git("rev-parse", "HEAD")
    manifest.write_text('{"name":"work","dependencies":["docs@tj-agents"]}', encoding="utf-8")
    git("commit", "--quiet", "-am", "Newer payload")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", f"url.{producer.as_uri()}.insteadOf")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "https://github.com/tj-agents/work.git")
    assert generate_marketplaces.read_manifest_dependencies("work", revision, ["work", "base"]) == {
        "work": ["base"], "base": [],
    }
    with pytest.raises(ValueError, match=f"tj-agents/work@{revision} plugins/absent/"):
        generate_marketplaces.read_manifest_dependencies("work", revision, ["absent"])


if __name__ == "__main__":
    unittest.main()
