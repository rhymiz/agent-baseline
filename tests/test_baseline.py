from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CLI = [sys.executable, "-m", "agent_baseline"]


class BaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "AGENTS.md").write_text("Run the declared checks.\n")
        (self.root / "contract.txt").write_text("Input must be validated.\n")
        self.config: dict[str, object] = {
            "schema_version": 1,
            "artifacts": [{"path": "AGENTS.md", "sources": ["contract.txt"]}],
            "checks": [self.command("ok", "print('verified')")],
        }
        self.write_config()

    def command(
        self, name: str, program: str, cwd: str = ".", timeout: int = 5
    ) -> dict[str, object]:
        return {
            "name": name,
            "argv": [sys.executable, "-c", program],
            "cwd": cwd,
            "timeout_seconds": timeout,
        }

    def write_config(self) -> None:
        (self.root / ".agent-baseline.json").write_text(json.dumps(self.config))

    def invoke(self, command: str, expected_code: int = 0) -> dict[str, object]:
        result = subprocess.run(
            [*CLI, command, str(self.root)], capture_output=True, text=True, timeout=15
        )
        self.assertEqual(
            result.returncode, expected_code, result.stdout + result.stderr
        )
        payload: object = json.loads(result.stdout)
        if not isinstance(payload, dict):
            self.fail("Expected a JSON report")
        report: dict[str, object] = {}
        for key, value in payload.items():
            if not isinstance(key, str):
                self.fail("Expected string keys")
            report[key] = value
        return report

    def test_record_current_and_verify(self) -> None:
        self.assertEqual(self.invoke("record")["status"], "recorded")
        self.assertEqual(self.invoke("check")["status"], "current")
        report = self.invoke("verify")
        self.assertEqual(report["status"], "passed")
        self.assertIn("verified", str(report["checks"]))

    def test_changed_source_requires_review_and_does_not_run_checks(self) -> None:
        self.config["checks"] = [
            self.command("sentinel", "from pathlib import Path; Path('ran').touch()")
        ]
        self.write_config()
        self.invoke("record")
        (self.root / "contract.txt").write_text("Changed contract\n")
        report = self.invoke("verify", 1)
        self.assertEqual(report["changed"], ["contract.txt"])
        self.assertFalse((self.root / "ran").exists())

    def test_artifact_and_command_drift(self) -> None:
        self.invoke("record")
        (self.root / "AGENTS.md").write_text("Different guidance\n")
        self.assertEqual(self.invoke("check", 1)["changed"], ["AGENTS.md"])
        self.invoke("record")
        self.config["checks"] = [self.command("new-check", "print('new')")]
        self.write_config()
        self.assertEqual(self.invoke("check", 1)["changed"], [".agent-baseline.json"])

    def test_missing_lock_and_missing_evidence_are_not_success(self) -> None:
        self.assertEqual(self.invoke("check", 2)["status"], "invalid")
        self.invoke("record")
        (self.root / "contract.txt").unlink()
        report = self.invoke("check", 1)
        self.assertEqual(report["status"], "needs_review")
        self.assertEqual(report["missing"], ["contract.txt"])
        self.assertEqual(
            report["affected_artifacts"],
            [
                {
                    "path": "AGENTS.md",
                    "changed_evidence": ["contract.txt"],
                    "configuration_changed": False,
                }
            ],
        )
        self.invoke("record", 2)

    def test_invalid_schema_unknown_keys_and_empty_checks(self) -> None:
        for replacement in (True, 3, "1"):
            with self.subTest(replacement=replacement):
                self.config["schema_version"] = replacement
                self.write_config()
                self.invoke("record", 2)
        self.config["schema_version"] = 1
        self.config["unrecognized"] = "typo"
        self.write_config()
        self.invoke("record", 2)
        del self.config["unrecognized"]
        self.config["checks"] = []
        self.write_config()
        self.invoke("record", 2)

    def test_outside_source_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as external:
            target = Path(external) / "source"
            target.write_text("external")
            (self.root / "outside").symlink_to(target)
            self.config["artifacts"] = [{"path": "AGENTS.md", "sources": ["outside"]}]
            self.write_config()
            self.assertIn("leaves the project", str(self.invoke("record", 2)["error"]))

    def test_path_traversal_is_rejected(self) -> None:
        self.config["artifacts"] = [{"path": "AGENTS.md", "sources": ["../outside"]}]
        self.write_config()
        self.invoke("record", 2)

    def test_failure_blocked_and_timeout_have_distinct_results(self) -> None:
        missing = {
            "name": "missing",
            "argv": ["/no/such/baseline-test-executable"],
            "cwd": ".",
            "timeout_seconds": 1,
        }
        self.config["checks"] = [
            self.command("failure", "raise SystemExit(7)"),
            missing,
            self.command("timeout", "import time; time.sleep(10)", timeout=1),
        ]
        self.write_config()
        self.invoke("record")
        report = self.invoke("verify", 1)
        self.assertEqual(report["status"], "not_passed")
        for status in ("failed", "blocked", "timed_out"):
            self.assertIn(status, str(report["checks"]))

    def test_check_is_read_only_and_uses_no_project_commands(self) -> None:
        self.config["checks"] = [
            self.command("sentinel", "from pathlib import Path; Path('ran').touch()")
        ]
        self.write_config()
        self.invoke("record")
        self.invoke("check")
        self.assertFalse((self.root / "ran").exists())

    def test_configured_working_directory_and_literal_arguments(self) -> None:
        (self.root / "package").mkdir()
        self.config["checks"] = [
            self.command(
                "cwd",
                "from pathlib import Path; assert Path.cwd().name == 'package'",
                cwd="package",
            ),
            {
                "name": "argv",
                "argv": [
                    sys.executable,
                    "-c",
                    "import sys; assert sys.argv[1] == '$(touch injected)'",
                    "$(touch injected)",
                ],
                "cwd": ".",
                "timeout_seconds": 5,
            },
        ]
        self.write_config()
        self.invoke("record")
        self.invoke("verify")
        self.assertFalse((self.root / "injected").exists())

    def test_mutation_during_verify_cannot_pass(self) -> None:
        self.config["checks"] = [
            self.command(
                "mutation",
                "from pathlib import Path; Path('contract.txt').write_text('changed')",
            )
        ]
        self.write_config()
        self.invoke("record")
        report = self.invoke("verify", 1)
        self.assertTrue(report["monitored_inputs_changed"])

    def test_inspect_respects_git_ignored_dependencies(self) -> None:
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / ".gitignore").write_text("ignored/\n")
        (self.root / "ignored").mkdir()
        (self.root / "ignored" / "AGENTS.md").write_text("ignore")
        (self.root / "package.json").write_text("{}")
        report = self.invoke("inspect")
        self.assertIn("package.json", str(report["candidates"]))
        self.assertNotIn("ignored/AGENTS.md", str(report["candidates"]))

    def test_structural_guidance_failure_prevents_project_command_execution(
        self,
    ) -> None:
        (self.root / "AGENTS.md").write_text("[Missing contract](removed.md)\n")
        self.config["checks"] = [
            self.command("sentinel", "from pathlib import Path; Path('ran').touch()")
        ]
        self.write_config()
        self.invoke("record")
        report = self.invoke("verify", 1)
        self.assertEqual(report["status"], "not_passed")
        self.assertFalse((self.root / "ran").exists())
        self.assertIn("broken_link", str(report["guidance"]))

    def test_invalidated_configuration_during_verification_preserves_check_results(
        self,
    ) -> None:
        self.config["checks"] = [
            self.command(
                "mutation",
                "from pathlib import Path; Path('.agent-baseline.json').write_text('invalid')",
            )
        ]
        self.write_config()
        self.invoke("record")
        report = self.invoke("verify", 1)
        self.assertTrue(report["monitored_inputs_changed"])
        self.assertIn("mutation", str(report["checks"]))
        self.assertIn("post_verification_error", report)


if __name__ == "__main__":
    unittest.main()
