import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

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
            "plugins": plugins,
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
        for field, value in (("revision", "main"), ("release", "pkg@1.2.3"), ("commit", "a" * 40), ("version", "1.2.3")):
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

    def test_every_entry_uses_main_without_sha_in_both_manifests(self):
        for manifest in (self.claude, self.codex):
            for entry in manifest["plugins"]:
                self.assertEqual(entry["source"]["ref"], "main")
                self.assertNotIn("sha", entry["source"])

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
            "rust": ["engineering"], "tauri": ["rust"], "rust-sqlx": ["rust"], "python": ["engineering"], "github-actions": ["engineering"],
            "azure": ["engineering"], "template": ["engineering"],
            "personal": ["engineering", "agent"], "work": ["engineering"],
            "infonetica": ["work", "base", "engineering"],
        }
        expected_names = {
            "base", "agent-store", "agent", "codex", "cli", "workflow", "engineering", "cpp", "gpp", "msvc", "win32",
            "dotnet", "efcore", "react", "nvim", "rust", "python", "github-actions", "azure",
            "template", "personal", "work", "infonetica", "tauri", "rust-sqlx",
        }
        by_name = {plugin["name"]: plugin for plugin in plugins}
        self.assertEqual(expected_names, set(by_name))
        self.assertEqual(expected_requires, {name: plugin["requires"] for name, plugin in by_name.items() if "requires" in plugin})
        for output in outputs.values():
            manifest = json.loads(output)
            self.assertEqual({entry["name"] for entry in manifest["plugins"]}, expected_names)
            for entry in manifest["plugins"]:
                self.assertEqual(entry["source"]["ref"], "main")
                self.assertNotIn("sha", entry["source"])
                self.assertEqual(entry["source"]["path"], f"./plugins/{entry['name']}")
        self.assertIn("claude", outputs)
        self.assertIn("codex", outputs)


if __name__ == "__main__":
    unittest.main()
