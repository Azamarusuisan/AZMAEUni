#!/usr/bin/env python3
"""Read-only structural validation for the write-note-drafts Skill."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PureWindowsPath
from urllib.parse import unquote, urlsplit

try:
    import yaml
except ImportError:
    print(
        "error: PyYAML is required; install requirements-validation.txt",
        file=sys.stderr,
    )
    raise SystemExit(2)


REQUIRED_FILES = (
    ".gitignore",
    ".github/workflows/validate.yml",
    "LICENSE",
    "README.md",
    "SKILL.md",
    "agents/openai.yaml",
    "requirements-validation.txt",
    "scripts/manage.py",
    "scripts/validate_skill.py",
    "references/acceptance-tests.md",
    "references/agent-compatibility.md",
    "references/architecture.md",
    "references/browser-chrome.md",
    "references/browser-safari.md",
    "references/cms-note.md",
    "references/consulting-slide-images.md",
    "references/configuration.md",
    "references/rich-media.md",
    "references/workflows.md",
    "assets/workspace-template/ASSETS.md",
    "assets/workspace-template/NOTE_GENERATOR.md",
    "assets/workspace-template/OPERATING_RULES.md",
    "assets/workspace-template/PROFILE.md",
    "assets/workspace-template/WRITING_PROFILE.md",
    "assets/workspace-template/templates/default.md",
)
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)
LINK_RE = re.compile(
    r'(?<!\\)!?\[[^\]]*]\(\s*(?P<target><[^>]+>|[^)\s]+)'
    r'(?:\s+(?:"[^"]*"|\'[^\']*\'))?\s*\)'
)
FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
IGNORED_PARTS = {".git", ".state", ".venv", "__pycache__", "runs"}


def read_yaml(path: Path, text: str, errors: list[str]) -> object:
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        errors.append(f"{path}: invalid YAML: {exc}")
        return None


def strip_fenced_code(text: str) -> str:
    kept: list[str] = []
    fence: str | None = None
    for line in text.splitlines(keepends=True):
        marker = FENCE_RE.match(line)
        if fence is not None:
            if (
                marker
                and marker.group(1)[0] == fence[0]
                and len(marker.group(1)) >= len(fence)
            ):
                fence = None
            continue
        if marker:
            fence = marker.group(1)
        else:
            kept.append(line)
    return "".join(kept)


def within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def validate_required_files(root: Path, errors: list[str]) -> None:
    for relative in REQUIRED_FILES:
        path = root / relative
        if not path.is_file():
            errors.append(f"missing required file: {relative}")
            continue
        if not within(path.resolve(), root):
            errors.append(f"required file resolves outside Skill: {relative}")


def validate_skill_md(root: Path, errors: list[str]) -> str | None:
    path = root / "SKILL.md"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"SKILL.md: cannot read: {exc}")
        return None
    match = FRONTMATTER_RE.match(text)
    if not match:
        errors.append("SKILL.md: missing opening YAML frontmatter")
        return None
    data = read_yaml(path, match.group(1), errors)
    if not isinstance(data, dict):
        errors.append("SKILL.md: frontmatter must be a mapping")
        return None
    if set(data) != {"name", "description"}:
        errors.append("SKILL.md: frontmatter must contain only name and description")

    name = data.get("name")
    description = data.get("description")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name) or len(name) >= 64:
        errors.append("SKILL.md: name must be under 64 lowercase letters/digits/hyphens")
        name = None
    elif name != root.name:
        try:
            plugin_name = json.loads(
                (root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
            ).get("name")
        except (OSError, json.JSONDecodeError, AttributeError):
            plugin_name = None
        if plugin_name != name:
            errors.append(f"SKILL.md: name {name!r} must match folder {root.name!r}")
    if not isinstance(description, str) or not description.strip():
        errors.append("SKILL.md: description must be a non-empty string")
    return name


def validate_openai_yaml(root: Path, skill_name: str | None, errors: list[str]) -> None:
    path = root / "agents" / "openai.yaml"
    try:
        data = read_yaml(path, path.read_text(encoding="utf-8"), errors)
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"agents/openai.yaml: cannot read: {exc}")
        return
    if not isinstance(data, dict):
        errors.append("agents/openai.yaml: root must be a mapping")
        return
    interface = data.get("interface")
    if not isinstance(interface, dict):
        errors.append("agents/openai.yaml: interface must be a mapping")
        return
    for key in ("display_name", "short_description", "default_prompt"):
        value = interface.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"agents/openai.yaml: interface.{key} must be non-empty")
    prompt = interface.get("default_prompt")
    if (
        skill_name
        and isinstance(prompt, str)
        and f"${skill_name}" not in prompt
    ):
        errors.append(
            f"agents/openai.yaml: default_prompt must invoke ${skill_name}"
        )
    policy = data.get("policy")
    if policy is not None and (
        not isinstance(policy, dict)
        or not isinstance(policy.get("allow_implicit_invocation"), bool)
    ):
        errors.append(
            "agents/openai.yaml: policy.allow_implicit_invocation must be boolean"
        )


def markdown_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if not any(part in IGNORED_PARTS for part in path.relative_to(root).parts)
    )


def validate_markdown_links(root: Path, errors: list[str]) -> int:
    checked = 0
    for markdown in markdown_files(root):
        resolved_markdown = markdown.resolve()
        if not within(resolved_markdown, root):
            errors.append(
                f"{markdown.relative_to(root)}: Markdown resolves outside Skill"
            )
            continue
        try:
            text = strip_fenced_code(markdown.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"{markdown.relative_to(root)}: cannot read: {exc}")
            continue
        checked += 1
        for match in LINK_RE.finditer(text):
            raw = match.group("target")
            target = raw[1:-1] if raw.startswith("<") and raw.endswith(">") else raw
            if target.startswith("#") or target.startswith("//"):
                continue
            if PureWindowsPath(target).is_absolute() or Path(target).is_absolute():
                errors.append(
                    f"{markdown.relative_to(root)}: absolute local link is forbidden: {raw}"
                )
                continue
            parsed = urlsplit(target)
            if parsed.scheme:
                if parsed.scheme == "file":
                    errors.append(
                        f"{markdown.relative_to(root)}: file URL is forbidden: {raw}"
                    )
                continue
            local = unquote(parsed.path)
            if not local:
                continue
            try:
                destination = (markdown.parent / local).resolve(strict=True)
            except FileNotFoundError:
                errors.append(
                    f"{markdown.relative_to(root)}: missing local link target: {raw}"
                )
                continue
            if not within(destination, root):
                errors.append(
                    f"{markdown.relative_to(root)}: link escapes Skill: {raw}"
                )
    return checked


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    if not root.is_dir():
        return [f"Skill directory does not exist: {root}"]
    validate_required_files(root, errors)
    skill_name = validate_skill_md(root, errors)
    validate_openai_yaml(root, skill_name, errors)
    validate_markdown_links(root, errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "skill_directory",
        nargs="?",
        default=Path(__file__).resolve().parent.parent,
        type=Path,
    )
    args = parser.parse_args(argv)
    root = args.skill_directory.expanduser().resolve()
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"OK: {root.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
