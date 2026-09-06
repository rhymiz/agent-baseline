from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class SelectedEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "AGENTS.md").write_text("Use the declared test command.\n")
        self.config = {
            "schema_version": 2,
            "artifacts": [
                {
                    "path": "AGENTS.md",
                    "sources": [{"path": "manifest.json", "json_pointer": "/scripts"}],
                }
            ],
            "checks": [],
        }
        self.manifest = {"scripts": {"test": "pytest"}, "description": "A project"}
        self.write()

    def write(self) -> None:
        (self.root / ".agent-baseline.json").write_text(json.dumps(self.config))
        (self.root / "manifest.json").write_text(json.dumps(self.manifest))

    def invoke(self, command: str, expected: int = 0) -> dict[str, object]:
        result = subprocess.run(
            [sys.executable, "-m", "agent_baseline", command, str(self.root)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        payload: object = json.loads(result.stdout)
        if not isinstance(payload, dict):
            self.fail("Expected report")
        return {str(key): value for key, value in payload.items()}

    def test_json_evidence_ignores_unrelated_fields_and_routes_real_drift(self) -> None:
        self.invoke("record")
        self.manifest["description"] = "Unrelated metadata"
        self.write()
        self.invoke("check")
        self.manifest["scripts"] = {"test": "a-different-test-command"}
        self.write()
        report = self.invoke("check", 1)
        self.assertEqual(report["changed"], ["manifest.json"])
        self.assertEqual(
            report["affected_artifacts"],
            [
                {
                    "path": "AGENTS.md",
                    "changed_evidence": [
                        {"path": "manifest.json", "json_pointer": "/scripts"}
                    ],
                    "configuration_changed": False,
                }
            ],
        )

    def test_json_pointer_escaped_keys_and_array_elements(self) -> None:
        self.config["artifacts"] = [
            {
                "path": "AGENTS.md",
                "sources": [
                    {"path": "manifest.json", "json_pointer": "/a~1b/~0list/0"}
                ],
            }
        ]
        self.manifest = {"a/b": {"~list": ["first", "second"]}}
        self.write()
        self.invoke("record")
        self.manifest = {"a/b": {"~list": ["first", "changed sibling"]}}
        self.write()
        self.invoke("check")

    def test_missing_pointer_duplicate_keys_and_invalid_pointer_never_record(
        self,
    ) -> None:
        for pointer in ("/absent", "/scripts/~9bad", "scripts", "/scripts/-"):
            self.config["artifacts"] = [
                {
                    "path": "AGENTS.md",
                    "sources": [{"path": "manifest.json", "json_pointer": pointer}],
                }
            ]
            self.write()
            self.invoke("record", 2)
            self.assertFalse((self.root / ".agent-baseline.lock.json").exists())
        self.config["artifacts"] = [
            {
                "path": "AGENTS.md",
                "sources": [{"path": "manifest.json", "json_pointer": "/scripts"}],
            }
        ]
        self.write()
        (self.root / "manifest.json").write_text('{"scripts":1,"scripts":2}')
        self.invoke("record", 2)

    def test_markdown_section_tracks_children_but_not_adjacent_sections(self) -> None:
        self.config["artifacts"] = [
            {
                "path": "AGENTS.md",
                "sources": [{"path": "contract.md", "heading": "Commands"}],
            }
        ]
        (self.root / "contract.md").write_text(
            "# Project\n## Commands\nRun tests.\n### Setup\nInstall deps.\n## Other\nFirst text.\n"
        )
        self.write()
        self.invoke("record")
        path = self.root / "contract.md"
        path.write_text(path.read_text().replace("First text", "Different text"))
        self.invoke("check")
        path.write_text(
            path.read_text().replace("Install deps", "Initialize test database")
        )
        self.invoke("check", 1)

    def test_ambiguous_heading_cannot_be_recorded(self) -> None:
        self.config["artifacts"] = [
            {
                "path": "AGENTS.md",
                "sources": [{"path": "contract.md", "heading": "Rules"}],
            }
        ]
        self.write()
        (self.root / "contract.md").write_text("# Rules\nFirst\n# Rules\nSecond\n")
        report = self.invoke("record", 2)
        self.assertIn("found 2", str(report["error"]))

    def test_zero_project_checks_is_explicit_guidance_only_verification(self) -> None:
        self.invoke("record")
        report = self.invoke("verify")
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["checks"], [])
        self.assertEqual(report["project_checks_declared"], 0)
        self.assertIn("guidance", report)

    def test_non_markdown_without_checks_cannot_claim_verification(self) -> None:
        (self.root / "instructions.txt").write_text("Run tests.\n")
        self.config["artifacts"] = [
            {"path": "instructions.txt", "sources": ["manifest.json"]}
        ]
        self.write()
        self.invoke("record")
        self.invoke("check")
        report = self.invoke("verify", 1)
        self.assertEqual(report["checks"], [])
        self.assertIn("No verification applies", str(report["note"]))

    def test_markdown_selector_ignores_metadata_and_code_headings(self) -> None:
        self.config["artifacts"] = [
            {
                "path": "AGENTS.md",
                "sources": [{"path": "contract.md", "heading": "Commands"}],
            }
        ]
        self.write()
        path = self.root / "contract.md"
        path.write_text(
            "---\n# Commands\ntitle: example\n---\n"
            "```md\n# Commands\n```\n# Commands\nRun tests.\n# Other\nText.\n"
        )
        self.invoke("record")
        path.write_text(path.read_text().replace("title: example", "title: changed"))
        self.invoke("check")
        path.write_text(path.read_text().replace("Run tests.", "Run lint."))
        self.invoke("check", 1)


if __name__ == "__main__":
    unittest.main()
