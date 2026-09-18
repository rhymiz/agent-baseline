from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
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

    def test_interrupted_verify_reaps_check_process_group(self) -> None:
        if os.name != "posix":
            self.skipTest("process-group cleanup is supported on POSIX")
        program = """
import os
import subprocess
import sys
import time
from pathlib import Path

root = Path.cwd()
nested = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
(root / "check.pid").write_text(str(os.getpid()))
(root / "nested.pid").write_text(str(nested.pid))
(root / "ready").write_text("ready")
time.sleep(60)
"""
        self.config["checks"] = [self.command("interrupt", program, timeout=60)]
        self.write_config()
        self.invoke("record")
        verifier = subprocess.Popen(
            [*CLI, "verify", str(self.root)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.addCleanup(self._cleanup_process, verifier)
        self.addCleanup(self._cleanup_recorded_check_processes)
        ready = self.root / "ready"
        deadline = time.monotonic() + 10
        while not ready.exists() and time.monotonic() < deadline:
            if verifier.poll() is not None:
                stdout, stderr = verifier.communicate()
                self.fail(f"verifier exited before check was ready: {stdout}{stderr}")
            time.sleep(0.05)
        self.assertTrue(ready.exists(), "check process did not report readiness")
        check_pid = int((self.root / "check.pid").read_text())
        nested_pid = int((self.root / "nested.pid").read_text())

        verifier.send_signal(signal.SIGINT)
        stdout, stderr = verifier.communicate(timeout=10)
        self.assertNotEqual(verifier.returncode, 0, stdout + stderr)
        self.assertNotIn('"status": "passed"', stdout)
        self.assertProcessExited(check_pid)
        self.assertProcessExited(nested_pid)

    def _cleanup_process(self, process: subprocess.Popen[str]) -> None:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)

    def _cleanup_recorded_check_processes(self) -> None:
        check_pid = self._read_pid("check.pid")
        if check_pid is not None:
            try:
                os.killpg(check_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except PermissionError:
                pass
        for name in ("check.pid", "nested.pid"):
            pid = self._read_pid(name)
            if pid is None:
                continue
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except PermissionError:
                pass

    def _read_pid(self, name: str) -> int | None:
        path = self.root / name
        if not path.exists():
            return None
        return int(path.read_text())

    def assertProcessExited(self, pid: int) -> None:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return
            time.sleep(0.05)
        self.fail(f"process {pid} survived interrupted verification")

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
        git_env = {
            key: value
            for key, value in os.environ.items()
            if key not in {"GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE"}
        }
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, env=git_env)
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


class PackageImportTests(unittest.TestCase):
    def test_sibling_modules_do_not_reexport_names(self) -> None:
        root = Path(__file__).resolve().parents[1] / "src" / "agent_baseline"
        pattern = re.compile(r"^from \.\w+ import (\w+) as \1\s*$", re.MULTILINE)
        for path in sorted(root.glob("*.py")):
            self.assertIsNone(pattern.search(path.read_text()), path.name)

    def test_invalid_baseline_is_imported_from_errors(self) -> None:
        root = Path(__file__).resolve().parents[1] / "src" / "agent_baseline"
        for path in sorted(root.glob("*.py")):
            if path.name == "errors.py":
                continue
            for line in path.read_text().splitlines():
                stripped = line.strip()
                if stripped.startswith("from ") and "InvalidBaseline" in stripped:
                    self.assertEqual(
                        stripped,
                        "from .errors import InvalidBaseline",
                        path.name,
                    )


if __name__ == "__main__":
    unittest.main()
