from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class PortableProjectTests(unittest.TestCase):
    def test_bootstrap_and_verification_do_not_require_a_project_language_runtime(self):
        fixtures = {
            "python": (
                "pyproject.toml",
                '[project]\nname = "example"\nversion = "1.0"\n',
            ),
            "rust": ("Cargo.toml", '[package]\nname = "example"\nversion = "1.0.0"\n'),
            "java": (
                "pom.xml",
                "<project><artifactId>example</artifactId></project>\n",
            ),
            "monorepo": ("packages/library/package.json", '{"name":"library"}\n'),
            "documentation": ("contract.md", "# Commands\nNo application runtime.\n"),
        }
        for kind, (manifest, content) in fixtures.items():
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "project with spaces"
                root.mkdir()
                source = root / manifest
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_text(content)
                original = f"# Project\nUse the [contract]({manifest}).\n"
                (root / "AGENTS.md").write_text(original)
                self.run_cli(root, "init", "--agent", "codex", "--agent", "claude")
                self.assertEqual((root / "AGENTS.md").read_text(), original)
                config = {
                    "schema_version": 2,
                    "artifacts": [{"path": "AGENTS.md", "sources": [manifest]}],
                    "checks": [],
                }
                (root / ".agent-baseline.json").write_text(json.dumps(config))
                doctor = self.run_cli(
                    root, "doctor", "--agent", "codex", "--agent", "claude"
                )
                self.assertEqual(len(doctor["skills"]), 1)
                self.assertEqual(
                    set(doctor["skills"][0]["locations"]), {"codex", "claude"}
                )
                self.run_cli(root, "record")
                report = self.run_cli(root, "verify")
                self.assertEqual(report["project_checks_declared"], 0)
                self.assertEqual(report["guidance"]["status"], "passed")
                # Bootstrap is idempotent even after a project record is configured.
                before = (root / ".agent-baseline.json").read_bytes()
                self.run_cli(root, "init", "--agent", "codex", "--agent", "claude")
                self.assertEqual((root / ".agent-baseline.json").read_bytes(), before)
                self.run_cli(root, "check")

    def run_cli(self, root, command, *options):
        result = subprocess.run(
            [sys.executable, "-m", "agent_baseline", command, str(root), *options],
            text=True,
            capture_output=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)


if __name__ == "__main__":
    unittest.main()
