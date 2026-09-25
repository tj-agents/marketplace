import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import generate


class InstructionPairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        root_patch = patch.object(generate, "ROOT", self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)

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


if __name__ == "__main__":
    unittest.main()
