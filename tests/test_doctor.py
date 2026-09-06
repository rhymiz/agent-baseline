from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_baseline.execution import project_paths


class DoctorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def write(self, path: str, text: str) -> Path:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        return target

    def invoke(self, *args: str, expected: int = 0) -> dict[str, object]:
        result = subprocess.run(
            [sys.executable, "-m", "agent_baseline", "doctor", str(self.root), *args],
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        payload: object = json.loads(result.stdout)
        if not isinstance(payload, dict):
            self.fail("Expected doctor report")
        return {str(key): value for key, value in payload.items()}

    def skill(
        self,
        base: str = ".agents",
        name: str = "build-project",
        description: str = "description: >\n  Build the project\n  using its checks.",
    ) -> Path:
        return self.write(
            f"{base}/skills/{name}/SKILL.md",
            f"---\nname: {name}\n{description}\n---\n\nUse project evidence.\n",
        ).parent

    def test_markdown_grammar_handles_references_spaces_and_code_examples(self) -> None:
        self.write(
            "AGENTS.md",
            """# Project
[guide][workflow]

[workflow]: <docs/guide (v1).md> "A title"

`[sample](missing-inline.md)`

```md
[example](missing-example.md)
```
""",
        )
        self.write(
            "docs/guide (v1).md", "[root](../AGENTS.md)\n![diagram](diagram.png)\n"
        )
        self.write("docs/diagram.png", "fixture")
        report = self.invoke()
        self.assertEqual(report["documents_checked"], 2)
        self.assertEqual(report["links_checked"], 3)
        self.assertEqual(report["issues"], [])

    def test_broken_relative_reference_is_actionable_and_nothing_is_written(
        self,
    ) -> None:
        original = "[contract](docs/removed.md)\n"
        self.write("AGENTS.md", original)
        report = self.invoke(expected=1)
        self.assertIn("broken_link", str(report["issues"]))
        self.assertIn("docs/removed.md", str(report["issues"]))
        self.assertEqual((self.root / "AGENTS.md").read_text(), original)
        self.assertEqual(len(list(self.root.iterdir())), 1)

    def test_skill_block_yaml_and_canonical_aliases(self) -> None:
        self.write("AGENTS.md", "Read project instructions.\n")
        self.write("CLAUDE.md", "Keep these local rules.\n\n@AGENTS.md\n")
        self.skill()
        alias = self.root / ".claude/skills/build-project"
        alias.parent.mkdir(parents=True)
        alias.symlink_to("../../.agents/skills/build-project", target_is_directory=True)
        report = self.invoke("--agent", "codex", "--agent", "claude")
        self.assertEqual(report["issues"], [])
        self.assertIn("build-project", str(report["skills"]))

    def test_missing_host_and_commented_import_do_not_pass(self) -> None:
        self.write("AGENTS.md", "Project rules.\n")
        self.write("CLAUDE.md", "`@AGENTS.md`\n\n```\n@AGENTS.md\n```\n")
        self.skill()
        report = self.invoke("--agent", "claude", expected=1)
        for code in ("root_not_routed", "skill_not_discoverable"):
            self.assertIn(code, str(report["issues"]))

    def test_configured_artifacts_do_not_hide_installed_skills_from_host_checks(
        self,
    ) -> None:
        self.write("AGENTS.md", "Project rules.\n")
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("contract.txt", "Source evidence.\n")
        self.write(
            ".agent-baseline.json",
            json.dumps(
                {
                    "schema_version": 2,
                    "artifacts": [{"path": "AGENTS.md", "sources": ["contract.txt"]}],
                    "checks": [],
                }
            ),
        )
        self.skill()
        report = self.invoke("--agent", "claude", expected=1)
        self.assertIn("skill_not_discoverable", str(report["issues"]))
        self.assertIn("build-project", str(report["skills"]))
        # An explicit path remains a deliberately scoped inspection.
        scoped = self.invoke("--path", "AGENTS.md", "--agent", "claude")
        self.assertEqual(scoped["skills"], [])

    def test_invalid_skill_values_and_unsafe_yaml_are_rejected(self) -> None:
        for description in (
            "description: false",
            "description: ''",
            "description: !!python/object/apply:os.system ['touch injected']",
        ):
            with self.subTest(description=description):
                self.skill(description=description)
                self.assertIn("invalid_skill", str(self.invoke(expected=1)["issues"]))
                self.assertFalse((self.root / "injected").exists())

    def test_alias_links_are_resolved_from_the_host_location(self) -> None:
        self.write(
            "canonical/build-project/SKILL.md",
            "---\nname: build-project\ndescription: Build this project.\n---\n[contract](../../contract.md)\n",
        )
        self.write("contract.md", "The actual contract.\n")
        alias = self.root / ".agents/skills/build-project"
        alias.parent.mkdir(parents=True)
        alias.symlink_to("../../canonical/build-project", target_is_directory=True)
        self.invoke("--path", "canonical/build-project/SKILL.md")
        self.assertIn(
            "broken_link",
            str(
                self.invoke(
                    "--path", ".agents/skills/build-project/SKILL.md", expected=1
                )["issues"]
            ),
        )

    def test_outside_symlink_is_not_read(self) -> None:
        with tempfile.TemporaryDirectory() as outside:
            (Path(outside) / "private.md").write_text("[another](absent.md)")
            (self.root / "linked.md").symlink_to(Path(outside) / "private.md")
            self.write("AGENTS.md", "[contract](linked.md)")
            report = self.invoke(expected=1)
            self.assertEqual(report["documents_checked"], 1)
            self.assertIn("outside the project", str(report["issues"]))

    def test_missing_git_has_a_real_filesystem_fallback(self) -> None:
        self.write("AGENTS.md", "Project guidance.")
        self.write("node_modules/dependency/AGENTS.md", "Dependency guidance.")
        with patch(
            "agent_baseline.execution.subprocess.run",
            side_effect=FileNotFoundError("git"),
        ):
            paths, method = project_paths(self.root)
        self.assertEqual(paths, ["AGENTS.md"])
        self.assertIn("filesystem", method)

    def test_no_guidance_is_not_success(self) -> None:
        self.assertIn("no_guidance", str(self.invoke(expected=1)["issues"]))

    def test_broken_claude_import_is_detected_without_a_host_flag(self) -> None:
        self.write("CLAUDE.md", "@deleted.md\n")
        self.assertIn("broken_import", str(self.invoke(expected=1)["issues"]))


if __name__ == "__main__":
    unittest.main()
