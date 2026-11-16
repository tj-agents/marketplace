import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import pytest

import generate


class RootFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        root_patch = patch.object(generate, "ROOT", self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)


class InstructionPairTests(RootFixtureTests):
    def test_agents_without_claude_fails(self):
        (self.root / "AGENTS.md").write_text("# Instructions\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "sibling CLAUDE.md"):
            generate.validate_instruction_pairs()

    def test_claude_without_agents_fails_even_in_hidden_directory(self):
        directory = self.root / ".claude"
        directory.mkdir()
        (directory / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "sibling AGENTS.md"):
            generate.validate_instruction_pairs()

    def test_only_the_pointer_is_accepted(self):
        (self.root / "AGENTS.md").write_text("# Instructions\n", encoding="utf-8")
        claude = self.root / "CLAUDE.md"
        claude.write_text("duplicated instructions\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "must contain only"):
            generate.validate_instruction_pairs()
        claude.write_text("@AGENTS.md\n", encoding="utf-8")
        generate.validate_instruction_pairs()


class PluginsFixtureTests(RootFixtureTests):
    def write_plugins_file(self, plugins):
        roster = {
            "name": "tj-agents",
            "description": "Test marketplace",
            "owner": "Tommy Seery",
            "plugins": [{"revision": "a" * 40, "kind": "shared", **plugin} for plugin in plugins],
        }
        (self.root / "plugins.json").write_text(json.dumps(roster), encoding="utf-8")


class ValidationErrorTests(PluginsFixtureTests):
    def test_duplicate_plugin_name_fails(self):
        self.write_plugins_file([
            {"name": "base", "repository": "core"},
            {"name": "base", "repository": "other"},
        ])
        with self.assertRaisesRegex(ValueError, "Duplicate plugin: base"):
            generate.build()

    def test_legacy_release_fields_are_rejected(self):
        for field, value in (("release", "pkg@1.2.3"), ("commit", "a" * 40), ("version", "1.2.3")):
            with self.subTest(field=field, value=value):
                self.write_plugins_file([{"name": "base", "repository": "core", field: value}])
                with self.assertRaisesRegex(ValueError, f"Unknown fields in plugin entry.*{field}"):
                    generate.build()

    def test_unknown_requires_name_fails(self):
        self.write_plugins_file([{"name": "engineering", "repository": "core", "requires": ["base"]}])
        with self.assertRaisesRegex(ValueError, "Unknown required plugin"):
            generate.build()

    def test_requires_must_be_a_list(self):
        self.write_plugins_file([
            {"name": "base", "repository": "core"},
            {"name": "engineering", "repository": "core", "requires": "base"},
        ])
        with self.assertRaisesRegex(ValueError, "requires must be a list"):
            generate.build()

    def test_external_runtime_does_not_inherit_engineering_from_its_repository(self):
        self.write_plugins_file([
            {"name": "base", "repository": "core"},
            {"name": "engineering", "repository": "core", "requires": ["base"]},
            {"name": "cli", "repository": "cli", "requires": ["base"]},
        ])
        outputs = generate.build()
        entries = {entry["name"]: entry for entry in json.loads(outputs["claude"])["plugins"]}
        self.assertEqual(["base"], entries["cli"]["dependencies"])

    def test_transitive_engineering_requirement_is_accepted(self):
        self.write_plugins_file([
            {"name": "engineering", "repository": "core"},
            {"name": "dotnet", "repository": "dotnet", "requires": ["engineering"]},
            {"name": "efcore", "repository": "dotnet", "requires": ["dotnet"]},
        ])
        generate.build()

    def test_requires_cycle_fails(self):
        self.write_plugins_file([
            {"name": "base", "repository": "core", "requires": ["workflow"]},
            {"name": "workflow", "repository": "core", "requires": ["base"]},
        ])
        with self.assertRaisesRegex(ValueError, "form a cycle"):
            generate.build()


class OutputShapeTests(PluginsFixtureTests):
    def setUp(self):
        super().setUp()
        self.write_plugins_file([
            {"name": "base", "repository": "core"},
            {"name": "engineering", "repository": "core", "requires": ["base"]},
            {"name": "nvim", "repository": "nvim", "requires": ["engineering"]},
        ])
        self.outputs = generate.build()
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

    def test_claude_entries_declare_requires_as_dependencies(self):
        dependencies = {entry["name"]: entry.get("dependencies") for entry in self.claude["plugins"]}
        self.assertEqual({"base": None, "engineering": ["base"], "nvim": ["engineering"]}, dependencies)

    def test_codex_entries_have_no_dependencies_key(self):
        for entry in self.codex["plugins"]:
            self.assertNotIn("dependencies", entry)

    def test_marketplace_name_is_tj_agents(self):
        self.assertEqual(self.claude["name"], "tj-agents")
        self.assertEqual(self.codex["name"], "tj-agents")

    def test_emission_is_byte_stable(self):
        self.assertEqual(generate.build(), self.outputs)


class RealRosterTests(unittest.TestCase):
    def test_build_succeeds_on_the_real_roster(self):
        outputs = generate.build()
        roster = json.loads((generate.ROOT / "plugins.json").read_text(encoding="utf-8"))
        plugins = roster["plugins"]
        expected_requires = {
            "agent-store": ["base"],
            "agent": ["base", "agent-store", "cli"],
            "codex": ["agent"],
            "cli": ["base"],
            "workflow": ["base", "agent-store", "agent"],
            "engineering": ["base", "workflow", "agent-store", "agent"],
            "gpp": ["cpp"],
            "msvc": ["cpp"], "win32": ["cpp"], "efcore": ["dotnet"],
            "cpp": ["engineering"], "dotnet": ["engineering"], "react": ["engineering"], "nvim": ["engineering"],
            "rust": ["engineering"], "tauri": ["rust"], "rust-sqlx": ["rust"], "seaorm": ["rust"], "python": ["engineering"], "github": ["base"], "github-actions": ["engineering"],
            "azure": ["engineering"], "template": ["engineering", "skill"], "skill": ["engineering"],
            "learning": ["base"],
            "personal": ["engineering", "agent", "docs"], "work": ["engineering", "teams"],
        }
        expected_names = {
            "base", "agent-store", "agent", "codex", "cli", "workflow", "engineering", "docs", "cpp", "gpp", "msvc", "win32",
            "dotnet", "efcore", "react", "nvim", "rust", "python", "github", "github-actions", "azure",
        }
        by_name = {plugin["name"]: plugin for plugin in plugins}
        self.assertEqual(expected_names, set(by_name))
        self.assertEqual(expected_requires, {name: plugin["requires"] for name, plugin in by_name.items() if "requires" in plugin})
        for output in outputs.values():
            manifest = json.loads(output)
            self.assertEqual({entry["name"] for entry in manifest["plugins"]}, expected_names)
            for entry in manifest["plugins"]:
                self.assertEqual(entry["source"]["sha"], by_name[entry["name"]]["revision"])
                self.assertNotIn("ref", entry["source"])
                self.assertEqual(entry["source"]["path"], f"./plugins/{entry['name']}")
        self.assertIn("claude", outputs)
        self.assertIn("codex", outputs)


def write_roster(root: Path, plugins: list[dict[str, object]]) -> None:
    roster = {
        "name": "tj-agents",
        "description": "Test marketplace",
        "owner": "Tommy Seery",
        "plugins": [{"revision": "a" * 40, "kind": "shared", **plugin} for plugin in plugins],
    }
    (root / "plugins.json").write_text(json.dumps(roster), encoding="utf-8")


@pytest.fixture
def roster_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(generate, "ROOT", tmp_path)
    return tmp_path


def test_build_accepts_an_organization_extending_and_requiring_a_profile(roster_root: Path) -> None:
    write_roster(roster_root, [
        {"name": "work", "repository": "work", "kind": "profile"},
        {"name": "acme", "repository": "acme", "requires": ["work"], "kind": "organization", "extends": "work"},
    ])
    generate.build()


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
            "Organization acme must require work, the profile it extends",
        ),
    ],
)
def test_build_rejects_an_invalid_kind(
    roster_root: Path, plugins: list[dict[str, object]], message: str
) -> None:
    write_roster(roster_root, plugins)
    with pytest.raises(ValueError, match=message):
        generate.build()


@pytest.mark.parametrize("field", ["profile", "generic_profile"])
def test_build_rejects_the_replaced_profile_fields(roster_root: Path, field: str) -> None:
    write_roster(roster_root, [{"name": "work", "repository": "work", "kind": "profile", field: True}])
    with pytest.raises(ValueError, match=rf"Unknown fields in plugin entry: \['{field}'\]"):
        generate.build()


def test_build_requires_every_entry_to_declare_its_kind(roster_root: Path) -> None:
    roster = {
        "name": "tj-agents", "description": "Test marketplace", "owner": "Tommy Seery",
        "plugins": [{"name": "base", "repository": "core", "revision": "a" * 40}],
    }
    (roster_root / "plugins.json").write_text(json.dumps(roster), encoding="utf-8")
    with pytest.raises(ValueError, match="Plugin kind must be one of shared, profile, organization: base"):
        generate.build()


    roster = json.loads((generate.ROOT / "plugins.json").read_text(encoding="utf-8"))
    kinds = {plugin["name"]: plugin["kind"] for plugin in roster["plugins"]}
    assert {name for name, kind in kinds.items() if kind == "profile"} == {"personal", "work"}


if __name__ == "__main__":
    unittest.main()
