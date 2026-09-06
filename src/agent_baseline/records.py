"""Validated project evidence and immutable snapshots."""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .errors import InvalidBaseline as InvalidBaseline
from .sources import Source, fingerprint, parsed_json, source

CONFIG = ".agent-baseline.json"
LOCK = ".agent-baseline.lock.json"
EXCLUDED = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".next",
    "dist",
    "build",
    "vendor",
}
MANIFESTS = {
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "Makefile",
    "justfile",
    "Gemfile",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
}
INSTRUCTIONS = {
    "AGENTS.md",
    "AGENTS.override.md",
    "CLAUDE.md",
    "GEMINI.md",
    "SKILL.md",
    "copilot-instructions.md",
}


@dataclass(frozen=True)
class Artifact:
    path: str
    sources: tuple[Source, ...]


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
    schema_version: int = 1


def fields(value: object, expected: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != expected:
        raise InvalidBaseline(
            f"{label} must contain exactly: {', '.join(sorted(expected))}"
        )
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise InvalidBaseline(f"{label} keys must be strings")
        result[key] = item
    return result


def string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise InvalidBaseline(
            f"{label} must be a nonempty string without NUL characters"
        )
    return value


def items(value: object, label: str) -> list[object]:
    if not isinstance(value, list) or not value:
        raise InvalidBaseline(f"{label} must be a nonempty array")
    return list(value)


def version(value: object) -> int:
    if type(value) is not int or value not in {1, 2}:
        raise InvalidBaseline("schema_version must be the integer 1 or 2")
    return value


def within(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise InvalidBaseline(f"Use a project-relative path without '..': {relative}")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root):
        raise InvalidBaseline(f"Path or symlink leaves the project: {relative}")
    return resolved


def read_json(path: Path) -> object:
    return parsed_json(path.read_text(encoding="utf-8"))


def load_baseline(root: Path, *, require_evidence: bool = True) -> Baseline:
    config = fields(
        read_json(within(root, CONFIG)),
        {"schema_version", "artifacts", "checks"},
        CONFIG,
    )
    schema_version = version(config["schema_version"])
    artifacts: list[Artifact] = []
    raw_artifacts = config["artifacts"]
    if not isinstance(raw_artifacts, list) or (
        schema_version == 1 and not raw_artifacts
    ):
        raise InvalidBaseline(
            "artifacts must be an array (nonempty for schema version 1)"
        )
    for raw in raw_artifacts:
        entry = fields(raw, {"path", "sources"}, "artifact")
        path = string(entry["path"], "artifact.path")
        sources = tuple(
            source(item, structured=schema_version == 2)
            for item in items(entry["sources"], "sources")
        )
        for candidate in (path, *(item.path for item in sources)):
            within(root, candidate)
            if candidate in {CONFIG, LOCK} or (
                require_evidence and not within(root, candidate).is_file()
            ):
                raise InvalidBaseline(
                    f"Artifact/source must be an existing project file other than the baseline records: {candidate}"
                )
        if len(set(sources)) != len(sources):
            raise InvalidBaseline(f"Duplicate sources for {path}")
        if within(root, path) in {within(root, item.path) for item in sources}:
            raise InvalidBaseline(f"An artifact cannot be its own evidence: {path}")
        artifacts.append(Artifact(path, sources))
    if len({within(root, artifact.path) for artifact in artifacts}) != len(artifacts):
        raise InvalidBaseline("Artifact paths must be unique")
    checks: list[Check] = []
    raw_checks = config["checks"]
    if not isinstance(raw_checks, list) or (schema_version == 1 and not raw_checks):
        raise InvalidBaseline("checks must be an array (nonempty for schema version 1)")
    for raw in raw_checks:
        entry = fields(raw, {"name", "argv", "cwd", "timeout_seconds"}, "check")
        timeout = entry["timeout_seconds"]
        if type(timeout) is not int or not 1 <= timeout <= 86400:
            raise InvalidBaseline(
                "timeout_seconds must be an integer between 1 and 86400"
            )
        cwd = string(entry["cwd"], "check.cwd")
        if not within(root, cwd).is_dir():
            raise InvalidBaseline(f"Check working directory does not exist: {cwd}")
        argv = tuple(string(arg, "argv item") for arg in items(entry["argv"], "argv"))
        checks.append(Check(string(entry["name"], "check.name"), argv, cwd, timeout))
    if len({check.name for check in checks}) != len(checks):
        raise InvalidBaseline("Check names must be unique")
    return Baseline(tuple(artifacts), tuple(checks), schema_version)


def snapshot(root: Path, baseline: Baseline) -> dict[Source, str]:
    sources = {Source(CONFIG)}
    for artifact in baseline.artifacts:
        sources.add(Source(artifact.path))
        sources.update(artifact.sources)
    return {
        item: fingerprint(within(root, item.path), item.selector)
        if within(root, item.path).is_file()
        else "missing"
        for item in sorted(sources, key=lambda item: item.key())
    }


def serialize_snapshot(
    current: dict[Source, str], schema_version: int
) -> dict[str, object]:
    if schema_version == 1:
        return {
            "schema_version": 1,
            "files": {item.path: digest for item, digest in current.items()},
        }
    return {
        "schema_version": 2,
        "evidence": [
            {"source": item.to_json(), "sha256": digest}
            for item, digest in current.items()
        ],
    }


def save_snapshot(root: Path, baseline: Baseline) -> None:
    destination = root / LOCK
    if destination.is_symlink():
        raise InvalidBaseline("The lock record must not be a symlink")
    current = snapshot(root, baseline)
    if "missing" in current.values():
        raise InvalidBaseline("Cannot record missing evidence files")
    content = (
        json.dumps(serialize_snapshot(current, baseline.schema_version), indent=2)
        + "\n"
    )
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=root, delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(content)
    try:
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def recorded_snapshot(root: Path) -> dict[Source, str]:
    raw = read_json(within(root, LOCK))
    if not isinstance(raw, dict) or "schema_version" not in raw:
        raise InvalidBaseline("Missing lock schema_version")
    schema_version = version(raw["schema_version"])
    pairs: list[tuple[Source, object]] = []
    if schema_version == 1:
        record = fields(raw, {"schema_version", "files"}, LOCK)
        mapping = record["files"]
        if not isinstance(mapping, dict):
            raise InvalidBaseline("lock.files must be an object")
        pairs = [
            (source(key, structured=False), value) for key, value in mapping.items()
        ]
    else:
        record = fields(raw, {"schema_version", "evidence"}, LOCK)
        for entry in items(record["evidence"], "lock.evidence"):
            row = fields(entry, {"source", "sha256"}, "lock evidence")
            pairs.append((source(row["source"]), row["sha256"]))
    recorded: dict[Source, str] = {}
    for item, value in pairs:
        within(root, item.path)
        digest = string(value, "lock hash")
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise InvalidBaseline(f"Invalid SHA-256 for {item.path}")
        if item in recorded:
            raise InvalidBaseline(f"Duplicate lock evidence: {item.path}")
        recorded[item] = digest
    return recorded


def drift(root: Path, current: dict[Source, str]) -> list[Source]:
    recorded = recorded_snapshot(root)
    return [
        item
        for item in sorted(
            current.keys() | recorded.keys(), key=lambda item: item.key()
        )
        if current.get(item) != recorded.get(item)
    ]
