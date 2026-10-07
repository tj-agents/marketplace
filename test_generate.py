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


class CatalogFixtureTests(RootFixtureTests):
    def write_catalog(self, plugins):
        catalog = {
            "name": "tj-agents",
            "description": "Test marketplace",
            "owner": "Tommy Seery",
            "plugins": plugins,
        }
        (self.root / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")


class ValidationErrorTests(CatalogFixtureTests):
    def test_missing_revision_fails(self):
        self.write_catalog([{"name": "base", "repository": "core"}])
        with self.assertRaisesRegex(ValueError, "Invalid revision"):
            generate.build()

    def test_invalid_revision_string_fails(self):
        self.write_catalog([{"name": "base", "repository": "core", "revision": "develop"}])
        with self.assertRaisesRegex(ValueError, "Invalid revision"):
            generate.build()

    def test_release_with_main_revision_fails(self):
        self.write_catalog([{
            "name": "base",
            "repository": "core",
            "revision": "main",
            "release": "base-agents@2.1.15",
        }])
        with self.assertRaisesRegex(ValueError, "release is not allowed with revision main"):
            generate.build()

    def test_vtag_release_version_mismatch_fails(self):
        self.write_catalog([{
            "name": "base",
            "repository": "core",
            "revision": "v2.1.15",
            "release": "base-agents@2.1.16",
        }])
        with self.assertRaisesRegex(ValueError, "does not match release version"):
            generate.build()

    def test_mismatched_revisions_in_same_repository_fails(self):
        self.write_catalog([
            {"name": "base", "repository": "core", "revision": "v2.1.15", "release": "base-agents@2.1.15"},
            {"name": "engineering", "repository": "core", "revision": "v2.1.16", "release": "base-agents@2.1.16"},
        ])
        with self.assertRaisesRegex(ValueError, "mismatched release/revision"):
            generate.build()

    def test_unknown_requires_name_fails(self):
        self.write_catalog([{
            "name": "engineering",
            "repository": "core",
            "revision": "v2.1.15",
            "release": "base-agents@2.1.15",
            "requires": ["base"],
        }])
        with self.assertRaisesRegex(ValueError, "Unknown required plugin"):
            generate.build()

    def test_zero_padded_version_fails(self):
        self.write_catalog([{
            "name": "base",
            "repository": "core",
            "revision": "v2.01.15",
            "release": "base-agents@2.01.15",
        }])
        with self.assertRaisesRegex(ValueError, "Invalid revision"):
            generate.build()

    def test_zero_padded_release_fails(self):
        self.write_catalog([{
            "name": "base",
            "repository": "core",
            "revision": "0" * 40,
            "release": "base-agents@2.01.15",
        }])
        with self.assertRaisesRegex(ValueError, "Invalid release"):
            generate.build()

    def test_requires_must_be_a_list(self):
        self.write_catalog([
            {"name": "base", "repository": "core", "revision": "main"},
            {"name": "engineering", "repository": "core", "revision": "main", "requires": "base"},
        ])
        with self.assertRaisesRegex(ValueError, "requires must be a list"):
            generate.build()

    def test_requires_cycle_fails(self):
        self.write_catalog([
            {"name": "base", "repository": "core", "revision": "main", "requires": ["machine"]},
            {"name": "machine", "repository": "core", "revision": "main", "requires": ["base"]},
        ])
        with self.assertRaisesRegex(ValueError, "form a cycle"):
            generate.build()


class OutputShapeTests(CatalogFixtureTests):
    def setUp(self):
        super().setUp()
        self.write_catalog([
            {"name": "base", "repository": "core", "revision": "v2.1.15", "release": "base-agents@2.1.15"},
            {"name": "engineering", "repository": "core", "revision": "v2.1.15", "release": "base-agents@2.1.15", "requires": ["base"]},
            {"name": "nvim", "repository": "nvim", "revision": "main"},
        ])
        self.outputs = generate.build()
        self.claude = json.loads(self.outputs["claude"])
        self.codex = json.loads(self.outputs["codex"])

    def test_pinned_entry_ref_equals_revision_in_both_manifests(self):
        for manifest in (self.claude, self.codex):
            entry = next(p for p in manifest["plugins"] if p["name"] == "base")
            self.assertEqual(entry["source"]["ref"], "v2.1.15")

    def test_main_entry_ref_is_main_in_both_manifests(self):
        for manifest in (self.claude, self.codex):
            entry = next(p for p in manifest["plugins"] if p["name"] == "nvim")
            self.assertEqual(entry["source"]["ref"], "main")

    def test_every_codex_entry_is_available(self):
        for entry in self.codex["plugins"]:
            self.assertEqual(entry["policy"]["installation"], "AVAILABLE")

    def test_claude_entries_have_no_policy_key(self):
        for entry in self.claude["plugins"]:
            self.assertNotIn("policy", entry)

    def test_marketplace_name_is_tj_agents(self):
        self.assertEqual(self.claude["name"], "tj-agents")
        self.assertEqual(self.codex["name"], "tj-agents")

    def test_emission_is_byte_stable(self):
        self.assertEqual(generate.build(), self.outputs)


class RealRosterTests(unittest.TestCase):
    def test_build_succeeds_on_the_real_roster(self):
        outputs = generate.build()
        catalog = json.loads((generate.ROOT / "catalog.json").read_text(encoding="utf-8"))
        plugins = catalog["plugins"]
        names = {plugin["name"] for plugin in plugins}
        for plugin in plugins:
            for required in plugin.get("requires", []):
                self.assertIn(required, names)
        by_repository: dict[str, tuple] = {}
        for plugin in plugins:
            pair = (plugin.get("release"), plugin["revision"])
            repository = plugin["repository"]
            if repository in by_repository:
                self.assertEqual(by_repository[repository], pair)
            else:
                by_repository[repository] = pair
        core_entries = {plugin["name"]: plugin for plugin in plugins if plugin["repository"] == "core"}
        self.assertEqual(set(core_entries), {"base", "engineering", "machine"})
        for plugin in core_entries.values():
            self.assertNotEqual(plugin["revision"], "main")
        self.assertIn("claude", outputs)
        self.assertIn("codex", outputs)


if __name__ == "__main__":
    unittest.main()
