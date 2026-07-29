#!/usr/bin/env python3
"""Manage a write-note-drafts workspace without third-party dependencies."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from urllib.parse import unquote, urlsplit, urlunsplit


SKILL_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_TEMPLATE = SKILL_ROOT / "assets" / "workspace-template"
DEFAULT_WORKSPACE = Path(
    os.environ.get("NOTE_DRAFT_PIPELINE_HOME", "~/.config/write-note-drafts")
).expanduser()
MAX_IMAGE_BYTES = 10 * 1024 * 1024
SCHEMA_VERSION = 1
IMAGE_LINK_RE = re.compile(
    r'(?<!\\)!\[[^\]]*]\(\s*(?P<target><[^>]+>|[^)\s]+)'
    r'(?:\s+(?:"[^"]*"|\'[^\']*\'))?\s*\)'
)
FENCED_CODE_RE = re.compile(
    r"^[ \t]*(`{3,}|~{3,}).*?^[ \t]*\1[ \t]*$", re.MULTILINE | re.DOTALL
)
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")
ACCOUNT_HANDLE_RE = re.compile(r"^[A-Za-z0-9_]{3,64}$")
ALLOWED_BROWSERS = {"chrome", "safari"}
ALLOWED_AGENTS = {"codex", "claude", "hermes"}
ALLOWED_AUTOMATION_MODES = {"guided", "autopilot"}
ALLOWED_OUTLINE_CONFIRMATIONS = {"毎回", "依頼時のみ"}
REQUIRED_MARKDOWN = (
    "NOTE_GENERATOR.md",
    "PROFILE.md",
    "WRITING_PROFILE.md",
    "OPERATING_RULES.md",
    "ASSETS.md",
    "templates/default.md",
)
ONBOARDING_FIELDS = {
    "NOTE_GENERATOR.md": ("使用ブラウザ", "note handle"),
    "PROFILE.md": ("発信の目的", "主なテーマ", "主な読者"),
    "WRITING_PROFILE.md": (
        "文体学習の状態",
        "口調",
        "一文の長さ",
        "改行・段落",
        "見出しの付け方",
        "導入の型",
        "締め方",
        "CTAの特徴",
    ),
    "OPERATING_RULES.md": (
        "自動化モード",
        "目標文字数",
        "構成確認",
        "調査範囲",
        "使用する情報の期間",
        "海外記事",
        "画像枚数",
        "画像のテイスト",
        "サムネイル",
        "サムネイル文字入れ",
        "図解",
        "SEO",
        "AIO",
        "CTAの有無",
    ),
    "templates/default.md": ("テンプレート名", "使用する記事タイプ"),
}
PHASES = {
    "intake",
    "research",
    "outline",
    "draft",
    "images",
    "preflight",
    "account_check",
    "stage",
    "verify",
}
PHASE_STATUSES = {
    "pending",
    "running",
    "waiting_user",
    "completed",
    "failed",
    "save_unverified",
}


class ManageError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManageError(f"missing file: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ManageError(f"invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ManageError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def workspace_path(value: str | None) -> Path:
    workspace = (
        Path(value).expanduser().resolve() if value else DEFAULT_WORKSPACE.resolve()
    )
    if is_within(workspace, SKILL_ROOT):
        raise ManageError("workspace must be outside the Skill checkout")
    return workspace


def secure_workspace_permissions(workspace: Path) -> None:
    if os.name == "nt" or not workspace.exists():
        return
    for path in [workspace, *workspace.rglob("*")]:
        if path.is_symlink():
            continue
        try:
            path.chmod(0o700 if path.is_dir() else 0o600)
        except OSError as exc:
            raise ManageError(f"cannot secure workspace permissions: {path}: {exc}") from exc


def doctor(
    workspace: Path,
    browser: str | None = None,
    agent_name: str = "codex",
    *,
    platform_name: str | None = None,
) -> dict:
    if browser is not None and browser not in ALLOWED_BROWSERS:
        raise ManageError(f"unsupported browser: {browser}")
    if agent_name not in ALLOWED_AGENTS:
        raise ManageError(f"unsupported agent: {agent_name}")

    python_ok = sys.version_info >= (3, 10)
    checks = {
        "python": {
            "status": "pass" if python_ok else "blocked",
            "version": ".".join(map(str, sys.version_info[:3])),
            "required": ">=3.10",
        }
    }

    probe_parent = workspace
    if workspace.exists() and not workspace.is_dir():
        workspace_check = {
            "status": "blocked",
            "detail": "workspace path exists but is not a directory",
        }
    else:
        if not workspace.exists():
            probe_parent = workspace.parent
            while not probe_parent.exists() and probe_parent != probe_parent.parent:
                probe_parent = probe_parent.parent
        if not probe_parent.is_dir():
            workspace_check = {
                "status": "blocked",
                "detail": f"nearest existing parent is not a directory: {probe_parent}",
            }
        else:
            try:
                with tempfile.TemporaryDirectory(
                    prefix=".write-note-drafts-doctor-", dir=probe_parent
                ):
                    pass
            except OSError as exc:
                workspace_check = {
                    "status": "blocked",
                    "detail": f"workspace is not writable/creatable: {exc}",
                }
            else:
                workspace_check = {
                    "status": "pass",
                    "detail": f"temporary write probe passed in {probe_parent}",
                }
    checks["workspace"] = workspace_check

    if browser is not None:
        current_platform = platform_name or sys.platform
        platform_ok = browser != "safari" or current_platform == "darwin"
        checks["platform"] = {
            "status": "pass" if platform_ok else "blocked",
            "value": current_platform,
            "required": "darwin" if browser == "safari" else "any",
        }
    image_capability = {
        "codex": "imagegen",
        "claude": "image_generation",
        "hermes": "image_generate",
    }[agent_name]
    runtime_names = ["web", image_capability]
    if browser == "chrome":
        runtime_names.append(
            {
                "codex": "chrome_connector",
                "claude": "claude_in_chrome",
                "hermes": "browser_cdp",
            }[agent_name]
        )
    elif browser == "safari":
        runtime_names.append(
            {
                "codex": "computer_use",
                "claude": "computer_use_mcp",
                "hermes": "computer_use",
            }[agent_name]
        )
    runtime_checks = {
        name: {
            "status": "pending",
            "detail": "The active agent must verify this capability in the active session",
        }
        for name in runtime_names
    }
    blocked = [name for name, value in checks.items() if value["status"] == "blocked"]
    return {
        "browser": browser,
        "agent": agent_name,
        "workspace": str(workspace),
        "status": "blocked" if blocked else "pending",
        "ready": False,
        "local_checks": checks,
        "runtime_checks": runtime_checks,
        "blocking_checks": blocked,
    }


def state_path(workspace: Path) -> Path:
    return workspace / ".state" / "workspace.json"


def load_workspace(workspace: Path) -> dict:
    state = read_json(state_path(workspace))
    if state.get("schema_version") != SCHEMA_VERSION:
        raise ManageError("unsupported workspace schema_version")
    if state.get("browser") not in ALLOWED_BROWSERS:
        raise ManageError("invalid workspace browser")
    if state.get("status") not in {"onboarding", "ready"}:
        raise ManageError("invalid workspace status")
    return state


def copy_template(template: Path, workspace: Path) -> tuple[int, int]:
    if not template.is_dir():
        raise ManageError(f"workspace template not found: {template}")
    template_resolved = template.resolve()
    workspace_resolved = workspace.resolve()
    if is_within(workspace_resolved, template_resolved) or is_within(
        template_resolved, workspace_resolved
    ):
        raise ManageError("workspace and template must not contain one another")

    copied = skipped = 0
    workspace.mkdir(parents=True, exist_ok=True)
    for source in sorted(template.rglob("*")):
        relative = source.relative_to(template)
        if relative.parts and relative.parts[0] == ".state":
            raise ManageError("workspace template must not contain .state")
        if source.is_symlink():
            raise ManageError(f"workspace template contains symlink: {relative}")
        destination = workspace / relative
        if source.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        elif source.is_file():
            if destination.exists():
                if not destination.is_file():
                    raise ManageError(f"template destination is not a file: {destination}")
                skipped += 1
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                copied += 1
    return copied, skipped


def init_workspace(
    workspace: Path, browser: str, template: Path = WORKSPACE_TEMPLATE
) -> dict:
    if is_within(workspace.resolve(), SKILL_ROOT):
        raise ManageError("workspace must be outside the Skill checkout")
    existing = None
    if state_path(workspace).exists():
        existing = load_workspace(workspace)
        if existing["browser"] != browser:
            raise ManageError(
                f"workspace already uses browser {existing['browser']!r}; refusing to overwrite"
            )

    copied, skipped = copy_template(template, workspace)
    (workspace / "runs").mkdir(exist_ok=True)
    (workspace / "assets").mkdir(exist_ok=True)
    (workspace / ".state").mkdir(exist_ok=True)
    try:
        (workspace / ".state").chmod(0o700)
    except OSError:
        pass

    if existing is None:
        timestamp = utc_now()
        existing = {
            "schema_version": SCHEMA_VERSION,
            "browser": browser,
            "created_at": timestamp,
            "updated_at": timestamp,
            "status": "onboarding",
            "expected_account_handle": None,
        }
        write_json(state_path(workspace), existing)
    secure_workspace_permissions(workspace)
    return {
        "workspace": str(workspace),
        "browser": existing["browser"],
        "status": existing["status"],
        "copied": copied,
        "skipped": skipped,
        "initialized": True,
    }


def image_mime(path: Path) -> str:
    with path.open("rb") as stream:
        head = stream.read(32)
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    raise ManageError(f"unsupported or invalid image: {path}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local_image_path(raw_target: str, markdown: Path, workspace: Path) -> Path:
    target = raw_target[1:-1] if raw_target.startswith("<") else raw_target
    target = unquote(target)
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or target.startswith("//"):
        raise ManageError(f"remote image is not allowed in {markdown}: {raw_target}")
    if parsed.query or parsed.fragment:
        raise ManageError(f"image query/fragment is not allowed in {markdown}: {raw_target}")
    if Path(target).is_absolute() or PureWindowsPath(target).is_absolute():
        raise ManageError(f"absolute image path is not allowed in {markdown}: {raw_target}")
    parts = Path(target.replace("\\", "/")).parts
    if ".." in parts:
        raise ManageError(f"parent traversal is not allowed in {markdown}: {raw_target}")

    try:
        resolved = (markdown.parent / target).resolve(strict=True)
    except FileNotFoundError as exc:
        raise ManageError(f"missing image in {markdown}: {raw_target}") from exc
    if not is_within(resolved, workspace.resolve()):
        raise ManageError(f"image resolves outside workspace in {markdown}: {raw_target}")
    if not resolved.is_file():
        raise ManageError(f"image is not a file in {markdown}: {raw_target}")
    return resolved


def markdown_files(workspace: Path) -> list[Path]:
    root = workspace.resolve()
    files = []
    for path in workspace.rglob("*.md"):
        resolved = path.resolve()
        if not is_within(resolved, root):
            raise ManageError(f"Markdown file resolves outside workspace: {path}")
        if resolved.is_file():
            files.append(path)
    return sorted(files)


def validate_workspace(workspace: Path) -> dict:
    load_workspace(workspace)
    root = workspace.resolve()
    assets: dict[str, dict] = {}
    checked_markdown = 0
    missing = [name for name in REQUIRED_MARKDOWN if not (workspace / name).is_file()]
    if missing:
        raise ManageError(f"missing required Markdown: {', '.join(missing)}")

    for markdown in markdown_files(workspace):
        checked_markdown += 1
        try:
            text = markdown.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise ManageError(f"cannot read Markdown: {markdown}: {exc}") from exc
        text = FENCED_CODE_RE.sub("", text)
        for match in IMAGE_LINK_RE.finditer(text):
            image = local_image_path(match.group("target"), markdown, workspace)
            size = image.stat().st_size
            if size > MAX_IMAGE_BYTES:
                raise ManageError(f"image exceeds 10MB: {image}")
            relative = image.relative_to(root).as_posix()
            referenced_by = markdown.resolve().relative_to(root).as_posix()
            if relative not in assets:
                assets[relative] = {
                    "path": relative,
                    "mime": image_mime(image),
                    "bytes": size,
                    "sha256": sha256_file(image),
                    "referenced_by": [],
                }
            if referenced_by not in assets[relative]["referenced_by"]:
                assets[relative]["referenced_by"].append(referenced_by)

    lock = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "assets": [assets[key] for key in sorted(assets)],
    }
    write_json(workspace / ".state" / "asset-lock.json", lock)
    secure_workspace_permissions(workspace)
    return {
        "workspace": str(workspace),
        "valid": True,
        "markdown_files": checked_markdown,
        "assets": len(assets),
    }


def normalize_account_handle(value: str) -> str:
    handle = value.removeprefix("@")
    if not ACCOUNT_HANDLE_RE.fullmatch(handle):
        raise ManageError("account handle must contain 3-64 letters, digits, or underscores")
    return handle


def markdown_fields(path: Path) -> dict[str, str]:
    fields = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*-\s*([^:：]+?)\s*[:：]\s*(.*?)\s*$", line)
        if match:
            fields[match.group(1).strip()] = match.group(2).strip()
    return fields


def validate_onboarding(workspace: Path, state: dict, account_handle: str) -> None:
    missing = []
    values = {}
    for relative, required_fields in ONBOARDING_FIELDS.items():
        fields = markdown_fields(workspace / relative)
        values[relative] = fields
        missing.extend(
            f"{relative}:{field}" for field in required_fields if not fields.get(field)
        )
    if missing:
        raise ManageError(f"onboarding fields are incomplete: {', '.join(missing)}")
    generator = values["NOTE_GENERATOR.md"]
    if generator["使用ブラウザ"].lower() != state["browser"]:
        raise ManageError("NOTE_GENERATOR.md browser does not match workspace state")
    if normalize_account_handle(generator["note handle"]) != account_handle:
        raise ManageError("NOTE_GENERATOR.md note handle does not match confirmed handle")
    automation_mode = values["OPERATING_RULES.md"]["自動化モード"].lower()
    if automation_mode not in ALLOWED_AUTOMATION_MODES:
        raise ManageError("自動化モード must be guided or autopilot")
    outline_confirmation = values["OPERATING_RULES.md"]["構成確認"]
    if outline_confirmation not in ALLOWED_OUTLINE_CONFIRMATIONS:
        raise ManageError("構成確認 must be 毎回 or 依頼時のみ")
    if automation_mode == "autopilot" and outline_confirmation != "依頼時のみ":
        raise ManageError("autopilot requires 構成確認: 依頼時のみ")
    thumbnail = values["OPERATING_RULES.md"]["サムネイル"]
    thumbnail_text = values["OPERATING_RULES.md"]["サムネイル文字入れ"]
    if thumbnail not in {"あり", "なし"}:
        raise ManageError("サムネイル must be あり or なし")
    if thumbnail_text not in {"あり", "なし"}:
        raise ManageError("サムネイル文字入れ must be あり or なし")
    if thumbnail == "あり" and thumbnail_text != "あり":
        raise ManageError("enabled thumbnails require サムネイル文字入れ: あり")


def mark_ready(workspace: Path, account_handle: str) -> dict:
    validation = validate_workspace(workspace)
    state = load_workspace(workspace)
    account_handle = normalize_account_handle(account_handle)
    validate_onboarding(workspace, state, account_handle)
    timestamp = utc_now()
    state.update(
        {
            "status": "ready",
            "expected_account_handle": account_handle,
            "ready_at": timestamp,
            "updated_at": timestamp,
        }
    )
    write_json(state_path(workspace), state)
    return {
        **validation,
        "status": "ready",
        "expected_account_handle": state["expected_account_handle"],
    }


def verify_account(workspace: Path, observed_handle: str) -> dict:
    state = load_workspace(workspace)
    expected = state.get("expected_account_handle")
    if state["status"] != "ready" or not expected:
        raise ManageError("workspace has no confirmed account handle")
    if observed_handle != expected:
        raise ManageError(
            f"account mismatch: expected {expected!r}, observed {observed_handle!r}"
        )
    return {"account_match": True, "expected_account_handle": expected}


def new_run(workspace: Path, requested_run_id: str | None) -> dict:
    workspace_state = load_workspace(workspace)
    if workspace_state["status"] != "ready":
        raise ManageError("workspace is not ready; run ready --account-handle first")
    validate_onboarding(
        workspace, workspace_state, workspace_state["expected_account_handle"]
    )
    run_id = requested_run_id or (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + os.urandom(3).hex()
    )
    if not SAFE_ID_RE.fullmatch(run_id):
        raise ManageError("run_id must be 1-80 letters, digits, underscores, or hyphens")
    run_dir = workspace / "runs" / run_id
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise ManageError(f"run already exists: {run_id}") from exc
    (run_dir / "images").mkdir()
    state = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "status": "running",
        "current_phase": "intake",
        "current_status": "pending",
        "phases": {},
        "browser": workspace_state["browser"],
        "expected_account_handle": workspace_state["expected_account_handle"],
        "idempotency_key": hashlib.sha256(
            f"note-draft:{run_id}".encode()
        ).hexdigest(),
        "draft_ref": None,
        "draft_url": None,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    write_json(run_dir / "state.json", state)
    secure_workspace_permissions(run_dir)
    return {"run_id": run_id, "run_dir": str(run_dir), "state": state}


def safe_draft_url(value: str) -> str:
    parsed = urlsplit(value)
    hostname = (parsed.hostname or "").lower()
    if (
        parsed.scheme != "https"
        or parsed.username
        or parsed.password
        or not (hostname == "note.com" or hostname.endswith(".note.com"))
    ):
        raise ManageError("draft_url must be an HTTPS note.com URL")
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def validate_run_image(run_dir: Path, item: dict) -> None:
    raw_path = item.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        raise ManageError("article package image is missing a path")
    relative = Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ManageError(f"unsafe run image path: {raw_path}")
    try:
        image = (run_dir / relative).resolve(strict=True)
    except FileNotFoundError as exc:
        raise ManageError(f"missing run image: {raw_path}") from exc
    if not is_within(image, (run_dir / "images").resolve()) or not image.is_file():
        raise ManageError(f"run image must be inside images/: {raw_path}")
    if image.stat().st_size > MAX_IMAGE_BYTES:
        raise ManageError(f"run image exceeds 10MB: {raw_path}")
    mime = image_mime(image)
    if item.get("mime") != mime:
        raise ManageError(f"run image MIME mismatch: {raw_path}")
    digest = sha256_file(image)
    if item.get("sha256") != digest:
        raise ManageError(f"run image hash mismatch: {raw_path}")


def require_resolved_brief(workspace: Path, run_dir: Path) -> dict:
    brief = read_json(run_dir / "brief.json")
    automation_mode = brief.get("automation_mode")
    rules = markdown_fields(workspace / "OPERATING_RULES.md")
    configured_mode = rules.get("自動化モード", "").lower()
    configured_outline = rules.get("構成確認", "")
    if automation_mode not in ALLOWED_AUTOMATION_MODES:
        raise ManageError("brief.json has an invalid automation_mode")
    if automation_mode != configured_mode:
        raise ManageError("brief.json automation_mode does not match OPERATING_RULES.md")
    if configured_outline not in ALLOWED_OUTLINE_CONFIRMATIONS:
        raise ManageError("OPERATING_RULES.md has an invalid 構成確認")
    if automation_mode == "autopilot" and configured_outline != "依頼時のみ":
        raise ManageError("autopilot requires 構成確認: 依頼時のみ")
    required = (
        "topic",
        "purpose",
        "audience",
        "target_characters",
        "tone",
        "research",
        "images",
        "field_origins",
        "resolved_at",
    )
    missing = [name for name in required if brief.get(name) in (None, "", [], {})]
    if missing:
        raise ManageError(f"brief.json is unresolved: {', '.join(missing)}")
    conflicts = brief.get("conflicts")
    if not isinstance(conflicts, list) or conflicts:
        raise ManageError("brief.json conflicts must be an empty list")
    if automation_mode == "guided" and not brief.get("confirmed_at"):
        raise ManageError("guided brief.json is not confirmed")
    if (
        automation_mode == "autopilot"
        and brief.get("outline_confirmation") != "request_only"
    ):
        raise ManageError("autopilot brief.json requires outline_confirmation=request_only")
    if brief.get("outline_confirmation") not in {"always", "request_only"}:
        raise ManageError("brief.json has an invalid outline_confirmation")
    if configured_outline == "毎回" and brief["outline_confirmation"] != "always":
        raise ManageError("brief.json cannot bypass 構成確認: 毎回")
    return brief


def validate_preflight(run_dir: Path, state: dict, require_checkpoint: bool) -> None:
    if not (run_dir / "article.md").is_file():
        raise ManageError("missing article.md")
    package = read_json(run_dir / "article-package.json")
    preflight = package.get("preflight")
    status = preflight.get("status") if isinstance(preflight, dict) else preflight
    if status != "pass":
        raise ManageError("article-package.json preflight is not pass")
    for item in package.get("images", []):
        if not isinstance(item, dict):
            raise ManageError("article package image must be an object")
        validate_run_image(run_dir, item)
    thumbnail = package.get("thumbnail")
    if thumbnail is not None:
        if not isinstance(thumbnail, dict):
            raise ManageError("article package thumbnail must be an object")
        validate_run_image(run_dir, thumbnail)
    brief_images = read_json(run_dir / "brief.json").get("images")
    if not isinstance(brief_images, dict):
        raise ManageError("brief.json images must be an object")
    if brief_images.get("thumbnail") is True:
        if not isinstance(thumbnail, dict):
            raise ManageError("article package is missing the required thumbnail")
        thumbnail_text = brief_images.get("thumbnail_text")
        if not isinstance(thumbnail_text, str) or not thumbnail_text.strip():
            raise ManageError("brief.json is missing required thumbnail_text")
        if (
            thumbnail.get("text") != thumbnail_text
            or thumbnail.get("text_verified") is not True
        ):
            raise ManageError("thumbnail text is not verified character-for-character")
        image_plan = run_dir / "image-plan.md"
        if not image_plan.is_file():
            raise ManageError("missing image-plan.md")
        if thumbnail_text not in image_plan.read_text(encoding="utf-8"):
            raise ManageError("image-plan.md is missing the exact thumbnail_text")
    if require_checkpoint and state.get("phases", {}).get("preflight", {}).get(
        "status"
    ) != "completed":
        raise ManageError("preflight phase is not completed")


def validate_checkpoint_gate(run_dir: Path, state: dict, phase: str, status: str) -> None:
    if phase == "intake":
        return
    brief = require_resolved_brief(run_dir.parent.parent, run_dir)
    if status == "failed":
        return
    if (
        phase in {"draft", "images", "preflight", "account_check", "stage", "verify"}
        and brief["automation_mode"] == "guided"
        and brief["outline_confirmation"] == "always"
        and not brief.get("outline_confirmed_at")
    ):
        raise ManageError("guided outline is not confirmed")
    if phase == "preflight":
        validate_preflight(run_dir, state, require_checkpoint=False)
    elif phase in {"account_check", "stage", "verify"}:
        validate_preflight(run_dir, state, require_checkpoint=True)
    if phase == "verify":
        if not state.get("draft_url"):
            raise ManageError("cannot verify without a checkpointed draft_url")
        if state.get("phases", {}).get("stage", {}).get("status") != "completed":
            raise ManageError("stage phase is not completed")


def checkpoint(
    workspace: Path,
    run_id: str,
    phase: str,
    phase_status: str,
    draft_url: str | None,
    draft_ref: str | None = None,
) -> dict:
    load_workspace(workspace)
    if not SAFE_ID_RE.fullmatch(run_id):
        raise ManageError("invalid run_id")
    if phase not in PHASES or phase_status not in PHASE_STATUSES:
        raise ManageError("invalid phase or status")
    path = workspace / "runs" / run_id / "state.json"
    state = read_json(path)
    if state.get("run_id") != run_id:
        raise ManageError("run state does not match run_id")
    validate_checkpoint_gate(path.parent, state, phase, phase_status)

    if draft_url is not None:
        sanitized = safe_draft_url(draft_url)
        if state.get("draft_url") not in (None, sanitized):
            raise ManageError("refusing to replace an existing draft_url")
        state["draft_url"] = sanitized
    if draft_ref is not None:
        if not SAFE_ID_RE.fullmatch(draft_ref):
            raise ManageError("draft_ref must be 1-80 letters, digits, underscores, or hyphens")
        if state.get("draft_ref") not in (None, draft_ref):
            raise ManageError("refusing to replace an existing draft_ref")
        state["draft_ref"] = draft_ref
    timestamp = utc_now()
    phases = state.setdefault("phases", {})
    phases[phase] = {"status": phase_status, "updated_at": timestamp}
    state["current_phase"] = phase
    state["current_status"] = phase_status
    if phase_status in {"failed", "save_unverified", "waiting_user"}:
        state["status"] = phase_status
    elif phase == "verify" and phase_status == "completed":
        state["status"] = "completed"
    else:
        state["status"] = "running"
    state["updated_at"] = timestamp
    write_json(path, state)
    secure_workspace_permissions(path.parent)
    return state


def workspace_status(workspace: Path) -> dict:
    if not state_path(workspace).is_file():
        return {
            "workspace": str(workspace),
            "initialized": False,
            "status": "uninitialized",
            "browser": None,
            "expected_account_handle": None,
            "runs": [],
        }
    state = load_workspace(workspace)
    runs = []
    runs_dir = workspace / "runs"
    if runs_dir.is_dir():
        for run_state in sorted(runs_dir.glob("*/state.json")):
            value = read_json(run_state)
            runs.append(
                {
                    key: value.get(key)
                    for key in (
                        "run_id",
                        "status",
                        "current_phase",
                        "draft_ref",
                        "draft_url",
                        "updated_at",
                    )
                }
            )
    return {
        "workspace": str(workspace),
        "initialized": True,
        "status": state["status"],
        "browser": state["browser"],
        "expected_account_handle": state.get("expected_account_handle"),
        "runs": runs,
    }


def self_check() -> dict:
    one_pixel_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
        "YAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    )
    with tempfile.TemporaryDirectory(prefix="write-note-drafts-") as temp:
        root = Path(temp)
        workspace = root / "workspace"
        result = init_workspace(workspace, "chrome")
        assert result["initialized"]
        (workspace / "assets" / "logo.png").write_bytes(one_pixel_png)
        (workspace / "ASSET_SELF_CHECK.md").write_text(
            "![brand](./assets/logo.png)\n", encoding="utf-8"
        )
        validation = validate_workspace(workspace)
        assert validation["assets"] == 1
        if os.name != "nt":
            assert workspace.stat().st_mode & 0o777 == 0o700
            assert (workspace / "ASSET_SELF_CHECK.md").stat().st_mode & 0o777 == 0o600
        lock = read_json(workspace / ".state" / "asset-lock.json")
        assert lock["assets"][0]["sha256"] == hashlib.sha256(one_pixel_png).hexdigest()
        assert workspace_status(root / "missing")["status"] == "uninitialized"
        try:
            workspace_path(str(SKILL_ROOT / "forbidden-workspace"))
        except ManageError:
            pass
        else:
            raise AssertionError("workspace inside the Skill checkout was accepted")
        common_doctor = doctor(root / "common-workspace")
        assert common_doctor["browser"] is None
        assert set(common_doctor["runtime_checks"]) == {"web", "imagegen"}
        chrome_doctor = doctor(root / "chrome-workspace", "chrome")
        assert chrome_doctor["status"] == "pending"
        assert chrome_doctor["ready"] is False
        assert set(chrome_doctor["runtime_checks"]) == {
            "web",
            "imagegen",
            "chrome_connector",
        }
        assert set(
            doctor(root / "hermes-workspace", "chrome", "hermes")["runtime_checks"]
        ) == {"web", "image_generate", "browser_cdp"}
        assert set(
            doctor(root / "claude-workspace", "safari", "claude")["runtime_checks"]
        ) == {"web", "image_generation", "computer_use_mcp"}
        safari_doctor = doctor(
            root / "safari-workspace", "safari", platform_name="darwin"
        )
        assert safari_doctor["status"] == "pending"
        assert set(safari_doctor["runtime_checks"]) == {
            "web",
            "imagegen",
            "computer_use",
        }
        assert (
            doctor(
                root / "safari-workspace", "safari", platform_name="linux"
            )["status"]
            == "blocked"
        )
        try:
            mark_ready(workspace, "@example_user")
        except ManageError:
            pass
        else:
            raise AssertionError("blank onboarding was accepted")
        for relative, fields in ONBOARDING_FIELDS.items():
            path = workspace / relative
            text = path.read_text(encoding="utf-8")
            for field in fields:
                value = {
                    "使用ブラウザ": "chrome",
                    "note handle": "example_user",
                    "自動化モード": "invalid",
                    "サムネイル": "あり",
                    "サムネイル文字入れ": "あり",
                }.get(field, "self-check")
                text, count = re.subn(
                    rf"(?m)^([ \t]*-[ \t]*{re.escape(field)}[ \t]*[:：][ \t]*)(.*?)[ \t]*$",
                    lambda match: match.group(1)
                    + (
                        value
                        if field == "自動化モード" or not match.group(2).strip()
                        else match.group(2).strip()
                    ),
                    text,
                )
                assert count == 1, (relative, field)
            path.write_text(text, encoding="utf-8")
        try:
            mark_ready(workspace, "@example_user")
        except ManageError:
            pass
        else:
            raise AssertionError("invalid automation mode was accepted")
        operating_rules = workspace / "OPERATING_RULES.md"
        operating_rules.write_text(
            re.sub(
                r"(?m)^([ \t]*-[ \t]*自動化モード[ \t]*[:：][ \t]*)invalid[ \t]*$",
                r"\g<1>autopilot",
                operating_rules.read_text(encoding="utf-8"),
            ),
            encoding="utf-8",
        )
        try:
            mark_ready(workspace, "@example_user")
        except ManageError:
            pass
        else:
            raise AssertionError("autopilot with outline confirmation was accepted")
        operating_rules.write_text(
            re.sub(
                r"(?m)^([ \t]*-[ \t]*自動化モード[ \t]*[:：][ \t]*)autopilot[ \t]*$",
                r"\g<1>guided",
                operating_rules.read_text(encoding="utf-8"),
            ),
            encoding="utf-8",
        )
        assert mark_ready(workspace, "@example_user")["status"] == "ready"
        assert verify_account(workspace, "example_user")["account_match"]
        try:
            verify_account(workspace, "other_user")
        except ManageError:
            pass
        else:
            raise AssertionError("account mismatch was accepted")
        run = new_run(workspace, "self-check")
        run_dir = Path(run["run_dir"])
        assert (run_dir / "images").is_dir()
        assert len(run["state"]["idempotency_key"]) == 64
        try:
            checkpoint(workspace, "self-check", "stage", "completed", None)
        except ManageError:
            pass
        else:
            raise AssertionError("stage without a confirmed brief was accepted")
        write_json(
            run_dir / "brief.json",
            {
                "schema_version": 1,
                "automation_mode": "guided",
                "outline_confirmation": "always",
                "topic": "self-check",
                "purpose": "self-check",
                "audience": "self-check",
                "target_characters": 1000,
                "tone": "self-check",
                "research": {"depth": "standard"},
                "images": {
                    "count": 1,
                    "thumbnail": True,
                    "thumbnail_text": "Self check",
                },
                "field_origins": {"topic": "self-check"},
                "conflicts": [],
                "resolved_at": utc_now(),
                "confirmed_at": utc_now(),
                "outline_confirmed_at": None,
            },
        )
        try:
            checkpoint(workspace, "self-check", "draft", "running", None)
        except ManageError:
            pass
        else:
            raise AssertionError("draft without outline confirmation was accepted")
        brief = read_json(run_dir / "brief.json")
        brief["outline_confirmed_at"] = utc_now()
        brief["outline_confirmation"] = "request_only"
        write_json(run_dir / "brief.json", brief)
        try:
            checkpoint(workspace, "self-check", "draft", "running", None)
        except ManageError:
            pass
        else:
            raise AssertionError("guided outline setting was bypassed")
        brief["outline_confirmation"] = "always"
        write_json(run_dir / "brief.json", brief)
        (run_dir / "article.md").write_text("# Self check\n", encoding="utf-8")
        (run_dir / "image-plan.md").write_text(
            "# Image plan\n\n- thumbnail text: Self check\n", encoding="utf-8"
        )
        (run_dir / "images" / "image.png").write_bytes(one_pixel_png)
        write_json(
            run_dir / "article-package.json",
            {
                "schema_version": 1,
                "preflight": "pass",
                "images": [
                    {
                        "path": "images/image.png",
                        "mime": "image/png",
                        "sha256": hashlib.sha256(one_pixel_png).hexdigest(),
                    }
                ],
                "thumbnail": {
                    "path": "images/image.png",
                    "mime": "image/png",
                    "sha256": hashlib.sha256(one_pixel_png).hexdigest(),
                    "text": "Self check",
                    "text_verified": False,
                },
            },
        )
        try:
            checkpoint(workspace, "self-check", "preflight", "completed", None)
        except ManageError:
            pass
        else:
            raise AssertionError("unverified thumbnail text was accepted")
        package = read_json(run_dir / "article-package.json")
        package["thumbnail"]["text_verified"] = True
        write_json(run_dir / "article-package.json", package)
        (run_dir / "image-plan.md").write_text(
            "# Image plan\n\n- thumbnail text: Different copy\n", encoding="utf-8"
        )
        try:
            checkpoint(workspace, "self-check", "preflight", "completed", None)
        except ManageError:
            pass
        else:
            raise AssertionError("thumbnail text missing from image-plan.md was accepted")
        (run_dir / "image-plan.md").write_text(
            "# Image plan\n\n- thumbnail text: Self check\n", encoding="utf-8"
        )
        checkpoint(workspace, "self-check", "preflight", "completed", None)
        saved = checkpoint(
            workspace,
            "self-check",
            "stage",
            "completed",
            "https://note.com/example/n/test?token=secret#fragment",
            "draft-self-check",
        )
        assert saved["draft_ref"] == "draft-self-check"
        assert saved["draft_url"] == "https://note.com/example/n/test"
        assert workspace_status(workspace)["runs"][0]["run_id"] == "self-check"

        operating_rules.write_text(
            re.sub(
                r"(?m)^([ \t]*-[ \t]*自動化モード[ \t]*[:：][ \t]*)guided[ \t]*$",
                r"\g<1>autopilot",
                re.sub(
                    r"(?m)^([ \t]*-[ \t]*構成確認[ \t]*[:：][ \t]*)毎回[ \t]*$",
                    r"\g<1>依頼時のみ",
                    operating_rules.read_text(encoding="utf-8"),
                ),
            ),
            encoding="utf-8",
        )
        autopilot_run = new_run(workspace, "autopilot-check")
        autopilot_dir = Path(autopilot_run["run_dir"])
        write_json(
            autopilot_dir / "brief.json",
            {
                "schema_version": 1,
                "automation_mode": "autopilot",
                "outline_confirmation": "request_only",
                "topic": "self-check",
                "purpose": "self-check",
                "audience": "self-check",
                "target_characters": 1000,
                "tone": "self-check",
                "research": {"depth": "standard"},
                "images": {"count": 0},
                "field_origins": {"topic": "self-check"},
                "conflicts": [],
                "resolved_at": utc_now(),
                "confirmed_at": None,
            },
        )
        assert checkpoint(
            workspace, "autopilot-check", "research", "running", None
        )["current_phase"] == "research"

        outside = root / "outside.png"
        outside.write_bytes(one_pixel_png)
        (workspace / "bad.md").write_text("![bad](../outside.png)\n", encoding="utf-8")
        try:
            validate_workspace(workspace)
        except ManageError:
            pass
        else:
            raise AssertionError("parent traversal was accepted")
    return {"self_check": "passed"}


def add_workspace_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--workspace",
        help="workspace path (defaults to NOTE_DRAFT_PIPELINE_HOME or ~/.config/write-note-drafts)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    init_parser = commands.add_parser("init")
    init_parser.add_argument("--workspace", required=True)
    init_parser.add_argument("--browser", choices=sorted(ALLOWED_BROWSERS), required=True)

    for name in ("status", "validate"):
        add_workspace_option(commands.add_parser(name))

    doctor_parser = commands.add_parser("doctor")
    add_workspace_option(doctor_parser)
    doctor_parser.add_argument("--browser", choices=sorted(ALLOWED_BROWSERS))
    doctor_parser.add_argument(
        "--agent", choices=sorted(ALLOWED_AGENTS), default="codex"
    )

    ready_parser = commands.add_parser("ready")
    add_workspace_option(ready_parser)
    ready_parser.add_argument("--account-handle", required=True)

    verify_account_parser = commands.add_parser("verify-account")
    add_workspace_option(verify_account_parser)
    verify_account_parser.add_argument("--observed-handle", required=True)

    new_run_parser = commands.add_parser("new-run")
    add_workspace_option(new_run_parser)
    new_run_parser.add_argument("--run-id")

    checkpoint_parser = commands.add_parser("checkpoint")
    add_workspace_option(checkpoint_parser)
    checkpoint_parser.add_argument("--run-id", required=True)
    checkpoint_parser.add_argument("--phase", required=True)
    checkpoint_parser.add_argument("--status", required=True)
    checkpoint_parser.add_argument("--draft-ref")
    checkpoint_parser.add_argument("--draft-url")

    commands.add_parser("self-check")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "self-check":
            result = self_check()
        else:
            workspace = workspace_path(args.workspace)
            if args.command == "init":
                result = init_workspace(workspace, args.browser)
            elif args.command == "doctor":
                result = doctor(workspace, args.browser, args.agent)
            elif args.command == "status":
                result = workspace_status(workspace)
            elif args.command == "ready":
                result = mark_ready(workspace, args.account_handle)
            elif args.command == "verify-account":
                result = verify_account(workspace, args.observed_handle)
            elif args.command == "new-run":
                result = new_run(workspace, args.run_id)
            elif args.command == "checkpoint":
                result = checkpoint(
                    workspace,
                    args.run_id,
                    args.phase,
                    args.status,
                    args.draft_url,
                    args.draft_ref,
                )
            elif args.command == "validate":
                result = validate_workspace(workspace)
            else:
                raise ManageError(f"unsupported command: {args.command}")
        print_json(result)
        return 0
    except (ManageError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
