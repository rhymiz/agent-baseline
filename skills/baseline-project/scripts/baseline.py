#!/usr/bin/env python3
"""Inspect project guidance, track its evidence, and execute declared checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from enum import Enum
from importlib.resources import files
from pathlib import Path

CONFIG = ".agent-baseline.json"
LOCK = ".agent-baseline.lock.json"
EXCLUDED = {".git", "node_modules", ".venv", "venv", "__pycache__", ".next", "dist", "build", "vendor"}
MANIFESTS = {"package.json", "pyproject.toml", "Cargo.toml", "go.mod", "Makefile", "justfile", "Gemfile", "pom.xml", "build.gradle", "build.gradle.kts"}
INSTRUCTIONS = {"AGENTS.md", "AGENTS.override.md", "CLAUDE.md", "GEMINI.md", "SKILL.md", "copilot-instructions.md"}


class InvalidBaseline(ValueError):
    """A project record is missing, unsafe to resolve, or malformed."""


@dataclass(frozen=True)
class Artifact:
    path: str
    sources: tuple[str, ...]


@dataclass(frozen=True)
class Check:
    name: str
    argv: tuple[str, ...]
    cwd: str
    timeout_seconds: int


@dataclass(frozen=True)
class Baseline:
    artifacts: tuple[Artifact, ...]
    checks: tuple[Check, ...]


def fields(value: object, expected: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != expected:
        raise InvalidBaseline(f"{label} must contain exactly: {', '.join(sorted(expected))}")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise InvalidBaseline(f"{label} keys must be strings")
        result[key] = item
    return result


def string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise InvalidBaseline(f"{label} must be a nonempty string without NUL characters")
    return value


def items(value: object, label: str) -> list[object]:
    if not isinstance(value, list) or not value:
        raise InvalidBaseline(f"{label} must be a nonempty array")
    return list(value)


def version(value: object) -> None:
    if type(value) is not int or value != 1:
        raise InvalidBaseline("schema_version must be the integer 1")


def within(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise InvalidBaseline(f"Use a project-relative path without '..': {relative}")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root):
        raise InvalidBaseline(f"Path or symlink leaves the project: {relative}")
    return resolved


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_baseline(root: Path) -> Baseline:
    config = fields(read_json(within(root, CONFIG)), {"schema_version", "artifacts", "checks"}, CONFIG)
    version(config["schema_version"])
    artifacts: list[Artifact] = []
    for raw in items(config["artifacts"], "artifacts"):
        entry = fields(raw, {"path", "sources"}, "artifact")
        path = string(entry["path"], "artifact.path")
        sources = tuple(string(source, "source") for source in items(entry["sources"], "sources"))
        for candidate in (path, *sources):
            if candidate in {CONFIG, LOCK} or not within(root, candidate).is_file():
                raise InvalidBaseline(f"Artifact/source must be an existing project file other than the baseline records: {candidate}")
        if len(set(sources)) != len(sources):
            raise InvalidBaseline(f"Duplicate sources for {path}")
        if within(root, path) in {within(root, source) for source in sources}:
            raise InvalidBaseline(f"An artifact cannot be its own evidence: {path}")
        artifacts.append(Artifact(path, sources))
    if len({within(root, artifact.path) for artifact in artifacts}) != len(artifacts):
        raise InvalidBaseline("Artifact paths must be unique")
    checks: list[Check] = []
    for raw in items(config["checks"], "checks"):
        entry = fields(raw, {"name", "argv", "cwd", "timeout_seconds"}, "check")
        timeout = entry["timeout_seconds"]
        if type(timeout) is not int or not 1 <= timeout <= 86400:
            raise InvalidBaseline("timeout_seconds must be an integer between 1 and 86400")
        cwd = string(entry["cwd"], "check.cwd")
        if not within(root, cwd).is_dir():
            raise InvalidBaseline(f"Check working directory does not exist: {cwd}")
        argv = tuple(string(arg, "argv item") for arg in items(entry["argv"], "argv"))
        checks.append(Check(string(entry["name"], "check.name"), argv, cwd, timeout))
    if len({check.name for check in checks}) != len(checks):
        raise InvalidBaseline("Check names must be unique")
    return Baseline(tuple(artifacts), tuple(checks))


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def snapshot(root: Path, baseline: Baseline) -> dict[str, str]:
    paths = {CONFIG}
    for artifact in baseline.artifacts:
        paths.add(artifact.path)
        paths.update(artifact.sources)
    return {path: digest(within(root, path)) for path in sorted(paths)}


def save_snapshot(root: Path, baseline: Baseline) -> None:
    destination = root / LOCK
    if destination.is_symlink():
        raise InvalidBaseline("The lock record must not be a symlink")
    content = json.dumps({"schema_version": 1, "files": snapshot(root, baseline)}, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=root, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(content)
    try:
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def drift(root: Path, current: dict[str, str]) -> list[str]:
    record = fields(read_json(within(root, LOCK)), {"schema_version", "files"}, LOCK)
    version(record["schema_version"])
    raw = record["files"]
    if not isinstance(raw, dict):
        raise InvalidBaseline("lock.files must be an object")
    recorded: dict[str, str] = {}
    for key, value in raw.items():
        name = string(key, "lock path")
        fingerprint = string(value, "lock hash")
        if len(fingerprint) != 64 or any(c not in "0123456789abcdef" for c in fingerprint):
            raise InvalidBaseline(f"Invalid SHA-256 for {name}")
        recorded[name] = fingerprint
    changed: list[str] = []
    for name in sorted(current.keys() | recorded.keys()):
        if name not in current or name not in recorded or current[name] != recorded[name]:
            changed.append(name)
    return changed


def inventory(root: Path) -> dict[str, object]:
    git = subprocess.run(["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"], capture_output=True, check=False)
    if git.returncode == 0:
        paths = sorted(set(git.stdout.decode("utf-8").split("\x00")) - {""})
        method = "git tracked and non-ignored untracked files"
    else:
        paths = []
        for directory, subdirs, files in os.walk(root, followlinks=False):
            subdirs[:] = sorted(name for name in subdirs if name not in EXCLUDED)
            paths.extend((Path(directory) / name).relative_to(root).as_posix() for name in files)
        paths.sort()
        method = "filesystem walk with common dependency/build directories excluded; ignore files not interpreted"
    groups: dict[str, list[str]] = {"manifests": [], "instructions": [], "ci": [], "contracts": []}
    for path in paths:
        parts = Path(path).parts
        if any(part in EXCLUDED for part in parts):
            continue
        name = Path(path).name
        if name in MANIFESTS:
            groups["manifests"].append(path)
        if name in INSTRUCTIONS or path.startswith(".cursor/rules/"):
            groups["instructions"].append(path)
        if path.startswith(".github/workflows/") or name in {".gitlab-ci.yml", "Jenkinsfile"}:
            groups["ci"].append(path)
        if name.endswith((".md", ".json", ".yaml", ".yml")) and any(part in {"contracts", "schemas", "openspec"} for part in parts):
            groups["contracts"].append(path)
    return {"status": "inventory", "root": str(root), "method": method, "file_count": len(paths), "candidates": {name: entries[:200] for name, entries in groups.items()}, "truncated_groups": [name for name, entries in groups.items() if len(entries) > 200], "note": "Paths are candidates, not verified sources of authority. No project commands were executed."}


def run_check(root: Path, check: Check) -> dict[str, object]:
    with tempfile.TemporaryFile() as output:
        try:
            process = subprocess.Popen(check.argv, cwd=within(root, check.cwd), stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        except OSError as error:
            return {"name": check.name, "status": "blocked", "error": str(error)}
        try:
            code = process.wait(timeout=check.timeout_seconds)
            status = "passed" if code == 0 else "failed"
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            code = process.returncode
            status = "timed_out"
        output.seek(0, os.SEEK_END)
        length = output.tell()
        output.seek(max(0, length - 8000))
        tail = output.read().decode("utf-8", errors="replace")
    return {"name": check.name, "argv": list(check.argv), "cwd": check.cwd, "status": status, "exit_code": code, "output_tail": tail, "output_truncated": length > 8000}


def execute(command: str, root: Path) -> tuple[dict[str, object], int]:
    if not root.is_dir():
        raise InvalidBaseline(f"Project directory does not exist: {root}")
    if command == "inspect":
        return inventory(root), 0
    baseline = load_baseline(root)
    if command == "record":
        save_snapshot(root, baseline)
        return {"status": "recorded", "note": "Evidence snapshot recorded. This does not run checks or certify the guidance."}, 0
    before = snapshot(root, baseline)
    changed = drift(root, before)
    if changed:
        return {"status": "needs_review", "changed": changed, "note": "Review the dependent guidance before recording a new baseline."}, 1
    if command == "check":
        return {"status": "current", "artifacts": len(baseline.artifacts), "checks_declared": len(baseline.checks), "note": "Monitored files match their recorded hashes. Verification commands were not run; semantic correctness is not established."}, 0
    if os.name != "posix":
        raise InvalidBaseline("verify currently requires macOS or Linux for process-group timeout handling")
    results = [run_check(root, check) for check in baseline.checks]
    after = snapshot(root, load_baseline(root))
    passed = before == after and all(result["status"] == "passed" for result in results)
    return {"status": "passed" if passed else "not_passed", "checks": results, "monitored_inputs_changed": before != after, "evidence_sha256": hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest(), "scope": "Declared checks and monitored files only; not a full-worktree attestation or proof of architectural quality."}, 0 if passed else 1


class Agent(Enum):
    CODEX = "codex"
    CLAUDE = "claude"

    @property
    def directory(self) -> str:
        return {Agent.CODEX: ".agents", Agent.CLAUDE: ".claude"}[self]


class Scope(Enum):
    PROJECT = "project"
    USER = "user"


@dataclass(frozen=True)
class SkillFile:
    path: str
    content: bytes


def skill_files() -> tuple[SkillFile, ...]:
    root = files("agent_baseline_guidance").joinpath("baseline-project")
    paths = ["SKILL.md"] + ["references/" + child.name for child in sorted(root.joinpath("references").iterdir(), key=lambda item: item.name) if child.is_file() and child.name.endswith(".md")]
    return tuple(SkillFile(path, root.joinpath(path).read_bytes()) for path in paths)


def install_skill(agent: Agent, scope: Scope, project: Path) -> dict[str, object]:
    root = Path.home() if scope is Scope.USER else project.expanduser().resolve()
    if not root.is_dir():
        raise InvalidBaseline(f"Installation root is not a directory: {root}")
    destination = root / agent.directory / "skills" / "baseline-project"
    bundle = skill_files()
    if destination.is_symlink():
        raise InvalidBaseline(f"Refusing to replace linked skill: {destination}")
    if destination.exists():
        expected = {item.path: item.content for item in bundle}
        existing: dict[str, bytes] = {}
        if not destination.is_dir():
            raise InvalidBaseline(f"Skill destination is not a directory: {destination}")
        for path in destination.rglob("*"):
            if path.is_symlink():
                raise InvalidBaseline(f"Existing skill contains a symlink: {path}")
            if path.is_file():
                existing[path.relative_to(destination).as_posix()] = path.read_bytes()
        if existing != expected:
            raise InvalidBaseline(f"Existing skill differs: {destination}. Review and move it aside before installing; no files were overwritten.")
        status = "current"
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".baseline-install-", dir=destination.parent) as staging:
            staged = Path(staging) / "baseline-project"
            staged.mkdir()
            for item in bundle:
                target = staged / item.path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(item.content)
            staged.rename(destination)
        status = "installed"
    return {"status": status, "skill": "baseline-project", "destination": str(destination), "files": [item.path for item in bundle], "next": "Start a new agent session and explicitly invoke baseline-project. Host discovery and automatic selection are separate from installation."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command, help_text in {"inspect": "read candidate paths", "record": "snapshot reviewed guidance", "check": "detect drift without executing checks", "verify": "execute all declared project checks"}.items():
        operation = commands.add_parser(command, help=help_text)
        operation.add_argument("project", nargs="?", default=".")
    skill = commands.add_parser("skill", help="read bundled guidance or install it for agent discovery")
    skill_commands = skill.add_subparsers(dest="skill_command", required=True)
    skill_commands.add_parser("show", help="print the skill and all references as Markdown")
    install = skill_commands.add_parser("install", help="copy guidance into an agent skill directory; preserve differing existing files")
    install.add_argument("--agent", required=True, choices=[agent.value for agent in Agent])
    install.add_argument("--scope", required=True, choices=[scope.value for scope in Scope])
    install.add_argument("--project", default=None, help="existing project directory for project scope (default: current directory)")
    args = parser.parse_args()
    try:
        if args.command == "skill":
            if args.skill_command == "show":
                print("\n\n".join(f"# File: {item.path}\n\n{item.content.decode('utf-8')}" for item in skill_files()))
                return 0
            scope = Scope(args.scope)
            if scope is Scope.USER and args.project is not None:
                raise InvalidBaseline("--project cannot be used with --scope user")
            report, code = install_skill(Agent(args.agent), scope, Path(args.project or ".")), 0
        else:
            report, code = execute(args.command, Path(args.project).expanduser().resolve())
    except (InvalidBaseline, OSError, ValueError) as error:
        report, code = {"status": "invalid", "error": str(error)}, 2
    print(json.dumps(report, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
