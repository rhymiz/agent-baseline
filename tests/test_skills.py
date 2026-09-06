from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_baseline.skills import Agent, Scope, SkillFile, install_at, install_skill


class SkillTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def invoke(self, *args: str, expected: int = 0) -> str:
        result = subprocess.run(
            [sys.executable, "-m", "agent_baseline", "skill", *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout

    def install(self, agent: str = "codex", expected: int = 0) -> str:
        return self.invoke(
            "install",
            "--agent",
            agent,
            "--scope",
            "project",
            "--project",
            str(self.root),
            expected=expected,
        )

    def test_show_includes_guidance_and_references_without_writes(self) -> None:
        text = self.invoke("show")
        for name in (
            "SKILL.md",
            "references/project-record.md",
            "references/evaluate.md",
        ):
            self.assertIn("# File: " + name, text)
        self.assertIn("uvx agent-baseline@0.2.0", text)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_project_install_copies_complete_linked_guidance_for_both_hosts(
        self,
    ) -> None:
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
                self.assertEqual(
                    Path(str(report["destination"])),
                    Path(home).resolve()
                    / agent.directory
                    / "skills"
                    / "baseline-project",
                )
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
        self.invoke(
            "install",
            "--agent",
            "codex",
            "--scope",
            "user",
            "--project",
            str(self.root),
            expected=2,
        )
        self.invoke(
            "install",
            "--agent",
            "codex",
            "--scope",
            "project",
            "--project",
            str(self.root / "missing"),
            expected=2,
        )
        self.assertEqual(list(self.root.iterdir()), [])

    def test_managed_upgrade_replaces_old_bundle_and_is_repeatable(self) -> None:
        destination = self.root / "baseline-project"
        before = (
            SkillFile("SKILL.md", b"old guidance"),
            SkillFile("references/old.md", b"old reference"),
        )
        after = (
            SkillFile("SKILL.md", b"new guidance"),
            SkillFile("references/new.md", b"new reference"),
        )
        with patch("agent_baseline.skills.skill_files", return_value=before):
            install_at(destination)
        with patch("agent_baseline.skills.skill_files", return_value=after):
            self.assertEqual(
                install_at(destination, upgrade=True)["status"], "upgraded"
            )
            self.assertEqual(install_at(destination, upgrade=True)["status"], "current")
        self.assertFalse((destination / "references/old.md").exists())
        self.assertEqual(
            (destination / "references/new.md").read_bytes(), b"new reference"
        )

    def test_upgrade_preserves_local_edits_and_unmanaged_installations(self) -> None:
        destination = self.root / "baseline-project"
        install_at(destination)
        changed = (SkillFile("SKILL.md", b"a new release"),)
        (destination / "SKILL.md").write_text("local changes")
        with patch("agent_baseline.skills.skill_files", return_value=changed):
            with self.assertRaisesRegex(ValueError, "Local skill edits"):
                install_at(destination, upgrade=True)
            (destination / ".agent-baseline-install.json").unlink()
            with self.assertRaisesRegex(ValueError, "No installation receipt"):
                install_at(destination, upgrade=True)
        self.assertEqual((destination / "SKILL.md").read_text(), "local changes")

    def test_failed_upgrade_restores_previous_directory(self) -> None:
        destination = self.root / "baseline-project"
        install_at(destination)
        original = {
            p.relative_to(destination).as_posix(): p.read_bytes()
            for p in destination.rglob("*")
            if p.is_file()
        }
        rename = Path.rename

        def fail_install(path: Path, target: Path) -> Path:
            if path.name == "new":
                raise OSError("simulated filesystem failure")
            return rename(path, target)

        with (
            patch(
                "agent_baseline.skills.skill_files",
                return_value=(SkillFile("SKILL.md", b"next release"),),
            ),
            patch.object(Path, "rename", fail_install),
        ):
            with self.assertRaises(OSError):
                install_at(destination, upgrade=True)
        restored = {
            p.relative_to(destination).as_posix(): p.read_bytes()
            for p in destination.rglob("*")
            if p.is_file()
        }
        self.assertEqual(original, restored)

    def test_project_install_cannot_follow_a_parent_link_outside_project(self) -> None:
        with tempfile.TemporaryDirectory() as outside:
            (self.root / ".agents").symlink_to(outside, target_is_directory=True)
            self.install(expected=2)
            self.assertEqual(list(Path(outside).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
