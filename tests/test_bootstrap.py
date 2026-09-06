from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class BootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="baseline project ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def invoke(self, *args: str, expected: int = 0) -> dict[str, object]:
        result = subprocess.run(
            [sys.executable, "-m", "agent_baseline", *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        payload: object = json.loads(result.stdout)
        if not isinstance(payload, dict):
            self.fail("Expected JSON report")
        return {str(key): value for key, value in payload.items()}

    def test_fresh_project_bootstrap_is_not_falsely_reviewed(self) -> None:
        self.invoke("init", ".", "--agent", "codex", "--agent", "claude")
        self.assertFalse((self.root / ".agent-baseline.lock.json").exists())
        self.assertFalse((self.root / "AGENTS.md").exists())
        self.assertEqual(
            self.invoke("record", ".", expected=2)["status"], "unconfigured"
        )
        self.assertEqual(
            self.invoke("verify", ".", expected=2)["status"], "unconfigured"
        )
        self.invoke("doctor", ".", "--agent", "codex", "--agent", "claude")
        before = (self.root / ".agent-baseline.json").read_bytes()
        self.invoke("init", ".", "--agent", "codex", "--agent", "claude")
        self.assertEqual((self.root / ".agent-baseline.json").read_bytes(), before)

    def test_existing_project_rules_and_config_survive(self) -> None:
        rules = "# Project rules\nKeep the authoritative domain contracts.\n"
        (self.root / "AGENTS.md").write_text(rules)
        config = '{"schema_version":2,"artifacts":[],"checks":[]}\n'
        (self.root / ".agent-baseline.json").write_text(config)
        self.invoke("init", ".", "--agent", "claude")
        self.assertEqual((self.root / "AGENTS.md").read_text(), rules)
        self.assertEqual((self.root / ".agent-baseline.json").read_text(), config)
        self.assertEqual((self.root / "CLAUDE.md").read_text(), "@AGENTS.md\n")

    def test_conflicting_destination_is_found_before_installation(self) -> None:
        target = self.root / ".claude/skills/baseline-project"
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("User-owned guidance")
        self.invoke("init", ".", "--agent", "claude", expected=2)
        self.assertFalse((self.root / ".agents").exists())
        self.assertFalse((self.root / ".agent-baseline.json").exists())
        self.assertEqual((target / "SKILL.md").read_text(), "User-owned guidance")

    def test_arbitrary_canonical_skill_can_be_linked_without_copying(self) -> None:
        source = self.root / "tooling/skills/team-engineering"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text(
            "---\nname: team-engineering\ndescription: Implement project-specific work.\n---\n[Guide](guide.md)\n"
        )
        (source / "guide.md").write_text("Use the existing owners.\n")
        self.invoke(
            "skill",
            "link",
            "tooling/skills/team-engineering",
            "--agent",
            "codex",
            "--agent",
            "claude",
        )
        for host in (".agents", ".claude"):
            self.assertEqual(
                (self.root / host / "skills/team-engineering").resolve(), source
            )
        (source / "guide.md").write_text("Updated canonical guidance.\n")
        self.assertEqual(
            (self.root / ".claude/skills/team-engineering/guide.md").read_text(),
            "Updated canonical guidance.\n",
        )

    def test_unsafe_relocation_rolls_back_created_aliases(self) -> None:
        source = self.root / "canonical/team-engineering"
        source.mkdir(parents=True)
        (self.root / "contract.md").write_text("Contract")
        (source / "SKILL.md").write_text(
            "---\nname: team-engineering\ndescription: Implement project-specific work.\n---\n[Contract](../../contract.md)\n"
        )
        self.invoke(
            "skill",
            "link",
            "canonical/team-engineering",
            "--agent",
            "codex",
            expected=2,
        )
        self.assertFalse((self.root / ".agents/skills/team-engineering").exists())
        self.assertTrue((source / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
