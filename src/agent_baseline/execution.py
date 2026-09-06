"""Project inventory and declared command execution."""

from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import tempfile
from pathlib import Path

from .doctor import scan_paths
from .records import (
    EXCLUDED,
    INSTRUCTIONS,
    MANIFESTS,
    Check,
    InvalidBaseline,
    drift,
    load_baseline,
    save_snapshot,
    serialize_snapshot,
    snapshot,
    within,
)
from .sources import Source


def project_paths(root: Path) -> tuple[list[str], str]:
    if not root.is_dir():
        raise InvalidBaseline(f"Project directory does not exist: {root}")
    try:
        git = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        git = None
    if git is not None and git.returncode == 0:
        paths = sorted(set(git.stdout.decode("utf-8").split("\x00")) - {""})
        method = "git tracked and non-ignored untracked files"
    else:
        paths = []
        for directory, subdirs, files in os.walk(root, followlinks=False):
            subdirs[:] = sorted(name for name in subdirs if name not in EXCLUDED)
            paths.extend(
                (Path(directory) / name).relative_to(root).as_posix() for name in files
            )
        paths.sort()
        method = "filesystem walk with common dependency/build directories excluded; ignore files not interpreted"
    return paths, method


def inventory(root: Path) -> dict[str, object]:
    paths, method = project_paths(root)
    groups: dict[str, list[str]] = {
        "manifests": [],
        "instructions": [],
        "ci": [],
        "contracts": [],
    }
    for path in paths:
        parts = Path(path).parts
        if any(part in EXCLUDED for part in parts):
            continue
        name = Path(path).name
        if name in MANIFESTS:
            groups["manifests"].append(path)
        if name in INSTRUCTIONS or path.startswith(".cursor/rules/"):
            groups["instructions"].append(path)
        if path.startswith(".github/workflows/") or name in {
            ".gitlab-ci.yml",
            "Jenkinsfile",
        }:
            groups["ci"].append(path)
        if name.endswith((".md", ".json", ".yaml", ".yml")) and any(
            part in {"contracts", "schemas", "openspec"} for part in parts
        ):
            groups["contracts"].append(path)
    return {
        "status": "inventory",
        "root": str(root),
        "method": method,
        "file_count": len(paths),
        "candidates": {name: entries[:200] for name, entries in groups.items()},
        "truncated_groups": [
            name for name, entries in groups.items() if len(entries) > 200
        ],
        "note": "Paths are candidates, not verified sources of authority. No project commands were executed.",
    }


def run_check(root: Path, check: Check) -> dict[str, object]:
    with tempfile.TemporaryFile() as output:
        try:
            process = subprocess.Popen(
                check.argv,
                cwd=within(root, check.cwd),
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        except OSError as error:
            return {"name": check.name, "status": "blocked", "error": str(error)}
        try:
            code = process.wait(timeout=check.timeout_seconds)
            status = "passed" if code == 0 else "failed"
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass  # It exited between the wait timeout and process-group cleanup.
            process.wait()
            code = process.returncode
            status = "timed_out"
        output.seek(0, os.SEEK_END)
        length = output.tell()
        output.seek(max(0, length - 8000))
        tail = output.read().decode("utf-8", errors="replace")
    return {
        "name": check.name,
        "argv": list(check.argv),
        "cwd": check.cwd,
        "status": status,
        "exit_code": code,
        "output_tail": tail,
        "output_truncated": length > 8000,
    }


def execute(command: str, root: Path) -> tuple[dict[str, object], int]:
    if not root.is_dir():
        raise InvalidBaseline(f"Project directory does not exist: {root}")
    if command == "inspect":
        return inventory(root), 0
    baseline = load_baseline(root, require_evidence=command == "record")
    if not baseline.artifacts:
        return {
            "status": "unconfigured",
            "note": "Use baseline-project to inspect the repository and configure artifacts, supporting evidence, and applicable checks. No reviewed baseline exists yet.",
        }, 2
    if command == "record":
        save_snapshot(root, baseline)
        return {
            "status": "recorded",
            "note": "Evidence snapshot recorded. This does not run checks or certify the guidance.",
        }, 0
    before = snapshot(root, baseline)
    changed = drift(root, before)
    if changed:
        return {
            "status": "needs_review",
            "changed": sorted({item.path for item in changed}),
            "evidence_changed": [item.to_json() for item in changed],
            "affected_artifacts": [
                {
                    "path": artifact.path,
                    "changed_evidence": [
                        item.to_json()
                        for item in changed
                        if item == Source(artifact.path) or item in artifact.sources
                    ],
                    "configuration_changed": Source(".agent-baseline.json") in changed,
                }
                for artifact in baseline.artifacts
                if Source(".agent-baseline.json") in changed
                or any(
                    item == Source(artifact.path) or item in artifact.sources
                    for item in changed
                )
            ],
            "missing": sorted(
                {item.path for item, value in before.items() if value == "missing"}
            ),
            "note": "Review the listed guidance against its changed evidence before recording. Removed or changed configuration also needs policy review.",
        }, 1
    if command == "check":
        return {
            "status": "current",
            "artifacts": len(baseline.artifacts),
            "checks_declared": len(baseline.checks),
            "note": "Monitored files match their recorded hashes. Verification commands were not run; semantic correctness is not established.",
        }, 0
    guidance_paths = [
        artifact.path
        for artifact in baseline.artifacts
        if artifact.path.lower().endswith(".md")
    ]
    guidance = (
        scan_paths(root, guidance_paths)
        if guidance_paths
        else {"status": "not_applicable", "scope": "No Markdown artifacts configured."}
    )
    if not guidance_paths and not baseline.checks:
        return {
            "status": "not_passed",
            "guidance": guidance,
            "checks": [],
            "project_checks_declared": 0,
            "note": "No verification applies. Declare project checks for non-Markdown artifacts; check can still report evidence freshness.",
        }, 1
    if guidance["status"] == "not_passed":
        return {
            "status": "not_passed",
            "guidance": guidance,
            "checks": [],
            "note": "Fix structural guidance errors before running project checks.",
        }, 1
    if os.name != "posix":
        raise InvalidBaseline(
            "verify currently requires macOS or Linux for process-group timeout handling"
        )
    results = [run_check(root, check) for check in baseline.checks]
    try:
        after = snapshot(root, load_baseline(root, require_evidence=False))
    except (OSError, ValueError) as error:
        return {
            "status": "not_passed",
            "guidance": guidance,
            "checks": results,
            "monitored_inputs_changed": True,
            "post_verification_error": str(error),
        }, 1
    passed = before == after and all(result["status"] == "passed" for result in results)
    return {
        "status": "passed" if passed else "not_passed",
        "guidance": guidance,
        "checks": results,
        "project_checks_declared": len(baseline.checks),
        "monitored_inputs_changed": before != after,
        "evidence_sha256": hashlib.sha256(
            json.dumps(
                serialize_snapshot(before, baseline.schema_version), sort_keys=True
            ).encode()
        ).hexdigest(),
        "scope": "Declared checks and monitored files only; not a full-worktree attestation or proof of architectural quality.",
    }, 0 if passed else 1
