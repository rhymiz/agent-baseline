"""Bootstrap portable guidance without inventing project policy or evidence."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .doctor import scan_paths
from .metadata import skill_metadata
from .records import CONFIG, InvalidBaseline, load_baseline, within
from .skills import Agent, install_at


def alias_target(root: Path, canonical: Path, agent: Agent) -> Path:
    target = root / agent.directory / "skills" / canonical.name
    within(root, target.relative_to(root).as_posix())
    if target.exists() or target.is_symlink():
        if target.resolve() != canonical.resolve():
            raise InvalidBaseline(
                f"Existing skill entry points elsewhere: {target}. Preserve and review it before linking."
            )
    return target


def link_skill(root: Path, source: str, agents: tuple[Agent, ...]) -> dict[str, object]:
    canonical = (root / source).resolve()
    if not canonical.is_relative_to(root) or not canonical.is_dir():
        raise InvalidBaseline(
            "A project skill must be an existing canonical directory inside the project"
        )
    metadata, error = skill_metadata(
        (canonical / "SKILL.md").read_text(encoding="utf-8-sig"), canonical.name
    )
    if error or metadata is None:
        raise InvalidBaseline(error or "Missing skill metadata")
    targets = [alias_target(root, canonical, agent) for agent in agents]
    created: list[Path] = []
    try:
        for target in targets:
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(
                    os.path.relpath(canonical, target.parent), target_is_directory=True
                )
                created.append(target)
        report = scan_paths(
            root,
            [(target / "SKILL.md").relative_to(root).as_posix() for target in targets],
        )
        if report["status"] != "passed":
            raise InvalidBaseline(
                f"Skill links do not resolve from the host locations: {json.dumps(report['issues'])}"
            )
    except (OSError, ValueError):
        for target in created:
            target.unlink()
        raise
    return {
        "status": "linked" if created else "current",
        "skill": metadata.name,
        "canonical": canonical.relative_to(root).as_posix(),
        "locations": [target.relative_to(root).as_posix() for target in targets],
        "note": "Aliases preserve one canonical skill. Validate native discovery in a new host session.",
    }


def initialize(root: Path, agents: tuple[Agent, ...]) -> dict[str, object]:
    if not root.is_dir():
        raise InvalidBaseline(f"Project directory does not exist: {root}")
    canonical = root / ".agents/skills/baseline-project"
    within(root, ".agents/skills/baseline-project")
    # Validate every existing destination before installing anything.
    for agent in agents:
        alias_target(root, canonical, agent)
    config_path = within(root, CONFIG)
    if config_path.exists():
        load_baseline(root, require_evidence=False)
    claude_path = root / "CLAUDE.md"
    within(root, "CLAUDE.md")
    installed = install_at(canonical)
    linked = (
        link_skill(root, canonical.relative_to(root).as_posix(), agents)
        if agents
        else None
    )
    changed: list[str] = []
    if not config_path.exists():
        # An empty draft cannot be recorded or verified as a reviewed baseline.
        with config_path.open("x", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {"schema_version": 2, "artifacts": [], "checks": []}, indent=2
                )
                + "\n"
            )
        changed.append(CONFIG)
    if (
        Agent.CLAUDE in agents
        and (root / "AGENTS.md").is_file()
        and not claude_path.exists()
    ):
        with claude_path.open("x", encoding="utf-8") as handle:
            handle.write("@AGENTS.md\n")
        changed.append("CLAUDE.md")
    return {
        "status": "initialized",
        "installation": installed,
        "discovery": linked,
        "created": changed,
        "review_recorded": False,
        "next_prompt": "Read .agents/skills/baseline-project/SKILL.md and use it to set up this project's agent baseline. Preserve existing instructions. Inspect actual code, contracts, and commands before authoring guidance or selecting evidence. Configure .agent-baseline.json, run doctor, record only after review, and verify. If no project checks exist, report that explicitly.",
        "note": "No project rules or commands were invented and no evidence was marked reviewed. Existing root instructions remain intact; review host routing when independent instruction files already exist.",
    }
