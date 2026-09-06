"""Agent Skills metadata parsed with safe YAML at the boundary."""

from __future__ import annotations

import re
from dataclasses import dataclass

import yaml


@dataclass(frozen=True)
class Skill:
    name: str
    description: str


def markdown_body(text: str) -> str:
    """Blank frontmatter while preserving Markdown source line numbers."""
    match = re.match(r"\A---\r?\n.*?\r?\n---(?:\r?\n|\Z)", text, re.S)
    if match:
        return "\n" * match[0].count("\n") + text[match.end() :]
    return text


def skill_metadata(text: str, folder: str) -> tuple[Skill | None, str | None]:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.S)
    if not match:
        return (
            None,
            "SKILL.md must start with YAML frontmatter containing name and description.",
        )
    try:
        raw: object = yaml.safe_load(match[1])
    except yaml.YAMLError as error:
        return None, f"Invalid skill YAML: {error}"
    if not isinstance(raw, dict):
        return None, "Skill frontmatter must be a YAML mapping."
    name, description = raw.get("name"), raw.get("description")
    if (
        not isinstance(name, str)
        or not 1 <= len(name) <= 64
        or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)
    ):
        return (
            None,
            "Skill name must be 1–64 lowercase letters, digits, or single hyphens.",
        )
    if name != folder:
        return None, f"Skill name {name!r} does not match its directory {folder!r}."
    if (
        not isinstance(description, str)
        or not description.strip()
        or len(description) > 1024
    ):
        return (
            None,
            "Skill description must be a nonempty string of at most 1024 characters.",
        )
    return Skill(name, description), None
