"""Portable packaged guidance and explicit host installation."""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass
from enum import Enum
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path

from .records import InvalidBaseline, fields, read_json, string, within


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
    paths = ["SKILL.md"] + [
        "references/" + child.name
        for child in sorted(
            root.joinpath("references").iterdir(), key=lambda item: item.name
        )
        if child.is_file() and child.name.endswith(".md")
    ]
    return tuple(SkillFile(path, root.joinpath(path).read_bytes()) for path in paths)


RECEIPT = ".agent-baseline-install.json"


@dataclass(frozen=True)
class Installation:
    package_version: str
    hashes: dict[str, str]


def fingerprints(contents: dict[str, bytes]) -> dict[str, str]:
    return {
        path: hashlib.sha256(content).hexdigest()
        for path, content in sorted(contents.items())
    }


def installed_contents(destination: Path) -> dict[str, bytes]:
    if destination.is_symlink() or not destination.is_dir():
        raise InvalidBaseline(
            f"Skill destination must be a real directory: {destination}"
        )
    contents: dict[str, bytes] = {}
    for path in destination.rglob("*"):
        if path.is_symlink():
            raise InvalidBaseline(f"Existing skill contains a symlink: {path}")
        if path.is_file() and path.relative_to(destination).as_posix() != RECEIPT:
            contents[path.relative_to(destination).as_posix()] = path.read_bytes()
    return contents


def installation(destination: Path) -> Installation | None:
    receipt = destination / RECEIPT
    if not receipt.exists():
        return None
    raw = fields(
        read_json(receipt),
        {"schema_version", "package_version", "files"},
        "installation receipt",
    )
    if type(raw["schema_version"]) is not int or raw["schema_version"] != 1:
        raise InvalidBaseline("Unknown installation receipt version")
    package_version = string(raw["package_version"], "installed package version")
    hashes: dict[str, str] = {}
    mapping = raw["files"]
    if not isinstance(mapping, dict) or not mapping:
        raise InvalidBaseline("Installation receipt must list its files")
    for path, value in mapping.items():
        name, digest = string(path, "installed path"), string(value, "installed hash")
        within(destination, name)
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise InvalidBaseline(f"Invalid installed fingerprint: {name}")
        hashes[name] = digest
    return Installation(package_version, hashes)


def install_at(destination: Path, *, upgrade: bool = False) -> dict[str, object]:
    bundle = skill_files()
    expected = {item.path: item.content for item in bundle}
    current_version = version("agent-baseline")
    previous: dict[str, bytes] | None = None
    if destination.is_symlink():
        raise InvalidBaseline(
            f"Update the canonical skill instead of its alias: {destination} -> {destination.resolve()}"
        )
    if destination.exists():
        previous = installed_contents(destination)
        receipt = installation(destination)
        if (
            previous == expected
            and receipt is not None
            and receipt.hashes == fingerprints(previous)
            and receipt.package_version == current_version
        ):
            return {
                "status": "current",
                "skill": "baseline-project",
                "destination": str(destination),
                "version": current_version,
            }
        if previous != expected:
            if not upgrade:
                raise InvalidBaseline(
                    f"Existing skill differs: {destination}. Use --upgrade for a managed installation; locally modified or untracked files are preserved."
                )
            if receipt is None:
                raise InvalidBaseline(
                    f"No installation receipt at {destination}. Review this older or unmanaged skill and move it aside before installing. No files were overwritten."
                )
            if fingerprints(previous) != receipt.hashes:
                raise InvalidBaseline(
                    f"Local skill edits or extra files at {destination}; review them before upgrading. No files were overwritten."
                )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".baseline-install-", dir=destination.parent
    ) as temporary:
        staged = Path(temporary) / "new"
        staged.mkdir()
        for item in bundle:
            target = staged / item.path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(item.content)
        (staged / RECEIPT).write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "package_version": current_version,
                    "files": fingerprints(expected),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        backup = Path(temporary) / "previous"
        if previous is not None:
            if installed_contents(destination) != previous:
                raise InvalidBaseline(
                    "Skill changed during installation; retry after reviewing the concurrent edits"
                )
            destination.rename(backup)
        try:
            staged.rename(destination)
        except OSError:
            if backup.exists() and not destination.exists():
                backup.rename(destination)
            raise
    return {
        "status": "upgraded" if previous is not None else "installed",
        "skill": "baseline-project",
        "destination": str(destination),
        "version": current_version,
        "files": [item.path for item in bundle],
        "next": "Start a new agent session and explicitly invoke baseline-project. Installation does not prove host discovery or automatic selection.",
    }


def install_skill(
    agent: Agent, scope: Scope, project: Path, *, upgrade: bool = False
) -> dict[str, object]:
    root = (Path.home() if scope is Scope.USER else project.expanduser()).resolve()
    if not root.is_dir():
        raise InvalidBaseline(f"Installation root is not a directory: {root}")
    relative = f"{agent.directory}/skills/baseline-project"
    within(root, relative)
    return install_at(root / relative, upgrade=upgrade)
