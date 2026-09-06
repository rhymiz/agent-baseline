from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from baseline import Agent, Scope, install_skill


class SkillTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def invoke(self, *args: str, expected: int = 0) -> str:
        result = subprocess.run([sys.executable, "-m", "baseline", "skill", *args], cwd=self.root, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout

    def install(self, agent: str = "codex", expected: int = 0) -> str:
        return self.invoke("install", "--agent", agent, "--scope", "project", "--project", str(self.root), expected=expected)

    def test_show_includes_guidance_and_references_without_writes(self) -> None:
        text = self.invoke("show")
        for name in ("SKILL.md", "references/project-record.md", "references/evaluate.md"):
            self.assertIn("# File: " + name, text)
        self.assertIn("uvx agent-baseline@0.1.1", text)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_project_install_copies_complete_linked_guidance_for_both_hosts(self) -> None:
        for agent, directory in (("codex", ".agents"), ("claude", ".claude")):
            report = json.loads(self.install(agent))
            destination = self.root / directory / "skills" / "baseline-project"
            self.assertEqual(report["status"], "installed")
            self.assertEqual(Path(report["destination"]), destination)
            skill = destination / "SKILL.md"
            for link in re.findall(r"\]\(([^)]+)\)", skill.read_text()):
                self.assertTrue((destination / link).is_file(), link)
            self.assertFalse(any(path.is_symlink() for path in destination.rglob("*")))
            self.assertEqual(json.loads(self.install(agent))["status"], "current")

    def test_user_scope_uses_home_and_leaves_project_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            for agent in Agent:
                with patch("pathlib.Path.home", return_value=Path(home)):
                    report = install_skill(agent, Scope.USER, self.root)
                self.assertEqual(Path(str(report["destination"])), Path(home) / agent.directory / "skills" / "baseline-project")
            self.assertEqual(list(self.root.iterdir()), [])

    def test_local_edits_and_extra_files_are_preserved(self) -> None:
        self.install()
        destination = self.root / ".agents/skills/baseline-project"
        original = (destination / "SKILL.md").read_bytes()
        (destination / "SKILL.md").write_text("local changes")
        self.install(expected=2)
        self.assertEqual((destination / "SKILL.md").read_text(), "local changes")
        (destination / "SKILL.md").write_bytes(original)
        (destination / "custom.md").write_text("custom reference")
        self.install(expected=2)
        self.assertEqual((destination / "custom.md").read_text(), "custom reference")

    def test_linked_destinations_and_references_are_preserved(self) -> None:
        self.install()
        destination = self.root / ".agents/skills/baseline-project"
        external = self.root / "external"
        destination.rename(external)
        destination.symlink_to(external, target_is_directory=True)
        self.install(expected=2)
        destination.unlink()
        external.rename(destination)
        reference = destination / "references/project-record.md"
        reference.unlink()
        reference.symlink_to(self.root / "missing")
        self.install(expected=2)
        self.assertTrue(reference.is_symlink())

    def test_scope_and_agent_are_explicit_and_invalid_root_is_rejected(self) -> None:
        self.invoke("install", expected=2)
        self.invoke("install", "--agent", "codex", expected=2)
        self.invoke("install", "--agent", "codex", "--scope", "user", "--project", str(self.root), expected=2)
        self.invoke("install", "--agent", "codex", "--scope", "project", "--project", str(self.root / "missing"), expected=2)
        self.assertEqual(list(self.root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
