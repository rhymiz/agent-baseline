"""Read-only structural checks for guidance, independent of a project's stack."""

from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
from markdown_it.token import Token

from .metadata import Skill, markdown_body, skill_metadata
from .records import CONFIG, INSTRUCTIONS, InvalidBaseline, load_baseline, within
from .skills import Agent


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    path: str
    line: int
    message: str


@dataclass(frozen=True)
class Link:
    target: str
    line: int
    kind: str


@dataclass(frozen=True)
class Document:
    path: str
    links: tuple[Link, ...]
    skill: Skill | None


def inline_links(tokens: list[Token], line: int) -> list[Link]:
    links: list[Link] = []
    for token in tokens:
        if token.type in {"link_open", "image"}:
            target = token.attrGet("href" if token.type == "link_open" else "src")
            if target is not None:
                if not isinstance(target, str):
                    raise InvalidBaseline("Markdown link destination must be text")
                links.append(Link(target, line, "markdown"))
        if token.children:
            links.extend(inline_links(token.children, line))
    return links


def document(path: str, text: str) -> tuple[Document, list[Issue]]:
    issues: list[Issue] = []
    skill = None
    if Path(path).name == "SKILL.md":
        skill, error = skill_metadata(text, Path(path).parent.name)
        if error:
            issues.append(Issue("error", "invalid_skill", path, 1, error))
    tokens = MarkdownIt("commonmark").enable("table").parse(markdown_body(text))
    links: list[Link] = []
    for token in tokens:
        line = token.map[0] + 1 if token.map else 1
        if token.type == "inline":
            links.extend(inline_links(token.children or [], line))
            if Path(path).name == "CLAUDE.md":
                # Host imports in prose are not imports inside inline or fenced code.
                for child in token.children or []:
                    if child.type == "text":
                        for match in re.finditer(r"(?:^|\s)@([^\s]+)", child.content):
                            links.append(Link(match[1], line, "import"))
    return Document(path, tuple(links), skill), issues


def scan_paths(
    root: Path, paths: list[str], agents: tuple[Agent, ...] = ()
) -> dict[str, object]:
    pending = list(dict.fromkeys(paths))
    visited: set[str] = set()
    issues: list[Issue] = []
    docs: list[Document] = []
    checked_links = 0
    skipped_external = 0
    while pending:
        if len(visited) >= 1000:
            issues.append(
                Issue(
                    "error",
                    "document_limit",
                    ".",
                    1,
                    "More than 1000 linked guidance locations; narrow --path or inspect recursive aliases.",
                )
            )
            break
        path = pending.pop(0)
        if path in visited:
            continue
        visited.add(path)
        try:
            resolved = within(root, path)
            text = resolved.read_text(encoding="utf-8-sig")
        except (OSError, ValueError) as error:
            issues.append(Issue("error", "unreadable_guidance", path, 1, str(error)))
            continue
        parsed, problems = document(path, text)
        docs.append(parsed)
        issues.extend(problems)
        for link in parsed.links:
            if link.kind == "import" and link.target.startswith("~/"):
                skipped_external += 1
                issues.append(
                    Issue(
                        "warning",
                        "external_import",
                        path,
                        link.line,
                        f"User import is outside the portable project scope: {link.target}",
                    )
                )
                continue
            try:
                url = urlsplit(link.target)
            except ValueError as error:
                issues.append(
                    Issue("error", "invalid_link", path, link.line, str(error))
                )
                continue
            if url.scheme or url.netloc:
                skipped_external += 1
                continue
            if not url.path:
                continue  # Renderer-specific fragments are not treated as missing files.
            if url.path.startswith("/"):
                issues.append(
                    Issue(
                        "warning",
                        "absolute_link",
                        path,
                        link.line,
                        f"Absolute or site-root link needs host-specific review: {link.target}",
                    )
                )
                continue
            # Resolve relative to the path through which the host loads the file.
            # This catches aliases that move a skill to a different nesting depth.
            candidate = Path(os.path.normpath((root / path).parent / unquote(url.path)))
            try:
                resolved_target = candidate.resolve(strict=True)
                if not resolved_target.is_relative_to(root):
                    raise InvalidBaseline("Target is outside the project")
            except (OSError, ValueError) as error:
                issues.append(
                    Issue(
                        "error",
                        "broken_import" if link.kind == "import" else "broken_link",
                        path,
                        link.line,
                        f"{link.target}: {error}",
                    )
                )
                continue
            checked_links += 1
            # Keep the lexical alias location for subsequent relative-link checks.
            target = Path(os.path.normpath(candidate)).relative_to(root).as_posix()
            if resolved_target.is_file() and resolved_target.suffix.lower() == ".md":
                pending.append(target)
    discoveries: list[dict[str, object]] = []
    canonical_skills: dict[tuple[str, Path], Document] = {}
    for doc in docs:
        if doc.skill:
            canonical_skills[(doc.skill.name, (root / doc.path).resolve())] = doc
    names: dict[str, set[Path]] = {}
    for (name, canonical), doc in canonical_skills.items():
        names.setdefault(name, set()).add(canonical)
        locations: dict[str, str] = {}
        for agent in agents:
            destination = root / agent.directory / "skills" / name / "SKILL.md"
            if destination.is_file() and destination.resolve() == canonical:
                locations[agent.value] = destination.relative_to(root).as_posix()
            else:
                issues.append(
                    Issue(
                        "error",
                        "skill_not_discoverable",
                        doc.path,
                        1,
                        f"{agent.value} has no entry pointing to this canonical skill at {destination.relative_to(root)}",
                    )
                )
        discoveries.append(
            {
                "name": name,
                "canonical": canonical.relative_to(root).as_posix(),
                "locations": locations,
            }
        )
    for name, targets in names.items():
        if len(targets) > 1:
            issues.append(
                Issue(
                    "warning",
                    "duplicate_skill",
                    name,
                    1,
                    "Different canonical folders declare the same skill name; host precedence may select different guidance.",
                )
            )
    if Agent.CLAUDE in agents and (root / "AGENTS.md").is_file():
        root_claude = next((doc for doc in docs if doc.path == "CLAUDE.md"), None)
        imports_root = root_claude is not None and any(
            link.kind == "import"
            and (root / link.target).resolve() == root / "AGENTS.md"
            for link in root_claude.links
        )
        if not imports_root and not (
            (root / "CLAUDE.md").is_file()
            and (root / "CLAUDE.md").resolve() == (root / "AGENTS.md").resolve()
        ):
            issues.append(
                Issue(
                    "error",
                    "root_not_routed",
                    "CLAUDE.md",
                    1,
                    "Claude's root instructions do not import or link to AGENTS.md.",
                )
            )
    if not paths:
        issues.append(
            Issue(
                "error",
                "no_guidance",
                ".",
                1,
                "No maintained guidance found. Use init or provide --path.",
            )
        )
    return {
        "status": "not_passed"
        if any(issue.severity == "error" for issue in issues)
        else "passed",
        "documents_checked": len(docs),
        "links_checked": checked_links,
        "external_links_not_checked": skipped_external,
        "issues": [asdict(issue) for issue in issues],
        "skills": discoveries,
        "scope": "Local Markdown link targets, YAML skill metadata, and explicitly selected host routes. Excludes anchor validity, remote URLs, prose correctness, and model behavior.",
    }


def doctor(
    root: Path, discovered: list[str], paths: list[str], agents: tuple[Agent, ...]
) -> dict[str, object]:
    if not root.is_dir():
        raise InvalidBaseline(f"Project directory does not exist: {root}")
    explicit_paths = bool(paths)
    if not paths:
        if (root / CONFIG).exists():
            paths = [
                artifact.path
                for artifact in load_baseline(root, require_evidence=False).artifacts
                if artifact.path.lower().endswith(".md")
            ]
        if not paths:
            paths = [
                path
                for path in discovered
                if Path(path).name in INSTRUCTIONS | {"README.md"}
                and path.lower().endswith(".md")
            ]
    if agents and not explicit_paths:
        # A configured artifact list may omit installed skills. Inspect native
        # project entries independently when host routing was requested.
        for host in Agent:
            directory = within(root, f"{host.directory}/skills")
            if directory.is_dir():
                for entry in sorted(directory.iterdir()):
                    skill_path = entry / "SKILL.md"
                    if skill_path.is_file() or entry.is_symlink():
                        path = skill_path.relative_to(root).as_posix()
                        if path not in paths:
                            paths.append(path)
    if (
        Agent.CLAUDE in agents
        and (root / "CLAUDE.md").is_file()
        and "CLAUDE.md" not in paths
    ):
        paths.append("CLAUDE.md")
    return scan_paths(root, paths, agents)
