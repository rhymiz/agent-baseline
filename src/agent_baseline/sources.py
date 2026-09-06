"""Whole-file and explicitly selected evidence, with stable identities."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

from markdown_it import MarkdownIt

from .errors import InvalidBaseline
from .metadata import markdown_body


@dataclass(frozen=True)
class JsonPointer:
    value: str


@dataclass(frozen=True)
class MarkdownSection:
    heading: str


@dataclass(frozen=True)
class Source:
    path: str
    selector: JsonPointer | MarkdownSection | None = None

    def to_json(self) -> str | dict[str, str]:
        if isinstance(self.selector, JsonPointer):
            return {"path": self.path, "json_pointer": self.selector.value}
        if isinstance(self.selector, MarkdownSection):
            return {"path": self.path, "heading": self.selector.heading}
        return self.path

    def key(self) -> str:
        return json.dumps(self.to_json(), sort_keys=True, ensure_ascii=False)


def source(value: object, *, structured: bool = True) -> Source:
    if isinstance(value, str):
        if not value.strip() or "\x00" in value:
            raise InvalidBaseline("Evidence paths must be nonempty strings without NUL")
        return Source(value)
    if not structured or not isinstance(value, dict):
        raise InvalidBaseline(
            "Expected an evidence path or a version 2 source selector"
        )
    keys = set(value)
    if keys not in ({"path", "json_pointer"}, {"path", "heading"}):
        raise InvalidBaseline(
            "A source selector requires path and exactly one of json_pointer or heading"
        )
    path = value["path"]
    if not isinstance(path, str) or not path.strip() or "\x00" in path:
        raise InvalidBaseline("Source path must be a nonempty string without NUL")
    if "json_pointer" in value:
        pointer = value["json_pointer"]
        if (
            not isinstance(pointer, str)
            or (pointer and not pointer.startswith("/"))
            or re.search(r"~(?![01])", pointer)
        ):
            raise InvalidBaseline(
                "json_pointer must follow RFC 6901 (empty or /-prefixed, with only ~0 and ~1 escapes)"
            )
        return Source(path, JsonPointer(pointer))
    heading = value["heading"]
    if not isinstance(heading, str) or not heading.strip():
        raise InvalidBaseline("heading must be a nonempty exact Markdown heading")
    return Source(path, MarkdownSection(heading))


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise InvalidBaseline(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def invalid_constant(value: str) -> NoReturn:
    raise InvalidBaseline(f"Non-JSON constant: {value}")


def parsed_json(text: str) -> object:
    return json.loads(
        text, object_pairs_hook=unique_object, parse_constant=invalid_constant
    )


def selected_json(text: str, pointer: str) -> bytes:
    value: object = parsed_json(text)
    for raw in pointer.split("/")[1:] if pointer else []:
        key = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif (
            isinstance(value, list)
            and re.fullmatch(r"0|[1-9][0-9]*", key)
            and int(key) < len(value)
        ):
            value = value[int(key)]
        else:
            raise InvalidBaseline(f"JSON pointer does not resolve: {pointer}")
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def selected_markdown(text: str, heading: str) -> bytes:
    tokens = MarkdownIt("commonmark").parse(markdown_body(text))
    headings: list[tuple[str, int, int]] = []
    for index, token in enumerate(tokens):
        if token.type == "heading_open" and token.map:
            inline = tokens[index + 1]
            title = "".join(
                child.content
                for child in inline.children or []
                if child.type in {"text", "code_inline"}
            )
            headings.append((title, token.map[0], int(token.tag[1:])))
    matches = [(line, level) for title, line, level in headings if title == heading]
    if len(matches) != 1:
        raise InvalidBaseline(
            f"Markdown heading must resolve exactly once: {heading!r} (found {len(matches)})"
        )
    start, level = matches[0]
    lines = text.splitlines(keepends=True)
    end = next(
        (line for _, line, depth in headings if line > start and depth <= level),
        len(lines),
    )
    return "".join(lines[start:end]).encode("utf-8")


def fingerprint(path: Path, selector: JsonPointer | MarkdownSection | None) -> str:
    if selector is None:
        with path.open("rb") as handle:
            return hashlib.file_digest(handle, "sha256").hexdigest()
    text = path.read_text(encoding="utf-8-sig")
    try:
        content = (
            selected_json(text, selector.value)
            if isinstance(selector, JsonPointer)
            else selected_markdown(text, selector.heading)
        )
    except ValueError as error:
        raise InvalidBaseline(f"{path}: {error}") from error
    return hashlib.sha256(content).hexdigest()
