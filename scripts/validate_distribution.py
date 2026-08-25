#!/usr/bin/env python3
"""Validate the URL-installable Codex plugin and marketplace package."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLUGIN_NAME = "write-note-drafts"
RELEASE_REF = "v0.3.6"
REPOSITORY_URL = "https://github.com/Azamarusuisan/AZMAEUni.git"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def load_object(relative: str) -> dict[str, object]:
    path = ROOT / relative
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict), f"{relative} must contain a JSON object"
    return payload


def main() -> int:
    manifest = load_object(".codex-plugin/plugin.json")
    marketplace = load_object(".agents/plugins/marketplace.json")

    assert manifest.get("name") == PLUGIN_NAME
    version = manifest.get("version")
    assert isinstance(version, str) and SEMVER.fullmatch(version)
    assert manifest.get("skills") == "./skills/"
    interface = manifest.get("interface")
    assert isinstance(interface, dict)
    for field in (
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
        "defaultPrompt",
    ):
        assert interface.get(field), f"plugin interface.{field} is required"

    entrypoint = ROOT / "skills" / PLUGIN_NAME / "SKILL.md"
    assert entrypoint.is_file(), "plugin Skill entry point is missing"
    canonical = ROOT / "SKILL.md"
    assert canonical.is_file(), "canonical root SKILL.md is missing"
    entrypoint_text = entrypoint.read_text(encoding="utf-8")
    assert f"name: {PLUGIN_NAME}" in entrypoint_text
    assert "../../SKILL.md" in entrypoint_text

    account_template = (ROOT / "assets/workspace-template/NOTE_GENERATOR.md").read_text(
        encoding="utf-8"
    )
    for field in ("アカウント名", "note URL", "note handle"):
        assert re.search(
            rf"(?m)^- {re.escape(field)}:\s*$", account_template
        ), f"distributed account field must remain blank: {field}"
    assert not re.search(
        r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", account_template, re.I
    ), "distributed account template must not contain an email address"
    assert "Azamarusuisan" not in account_template

    assets_template = (ROOT / "assets/workspace-template/ASSETS.md").read_text(
        encoding="utf-8"
    )
    for field in (
        "画像の相棒",
        "相棒の名前",
        "基準画像",
        "絶対に変えない特徴",
        "変更してよい要素",
        "登場方針",
        "利用権確認",
    ):
        assert re.search(
            rf"(?m)^- {re.escape(field)}:\s*$", assets_template
        ), f"distributed visual-partner field must remain blank: {field}"
    assert "配布者のキャラクターは置かず" in assets_template
    assert (ROOT / "references/visual-identity.md").is_file()

    research_router = (ROOT / "references/research-platforms.md").read_text(
        encoding="utf-8"
    )
    for required_platform in (
        "日本のnote",
        "Reddit",
        "Baidu Search",
        "百度贴吧",
        "中国政府网",
        "original_title",
        "translation_notes",
    ):
        assert required_platform in research_router, (
            f"research router is missing {required_platform}"
        )

    manager = (ROOT / "scripts/manage.py").read_text(encoding="utf-8")
    canonical_skill = canonical.read_text(encoding="utf-8")
    for required_guard in (
        "--browser-confirmed-by-user",
        "browser_selection",
        "require_browser_selection_confirmation",
        "select-browser",
    ):
        assert required_guard in manager, f"manager is missing {required_guard}"
    assert "never add it speculatively" in canonical_skill
    for required_visual_guard in (
        "validate_visual_partner_profile",
        "validate_visual_partner_plan",
        "identity_checked",
    ):
        assert required_visual_guard in manager, (
            f"manager is missing {required_visual_guard}"
        )
    assert "references/visual-identity.md" in canonical_skill

    assert marketplace.get("name") == "azmaeuni"
    plugins = marketplace.get("plugins")
    assert isinstance(plugins, list) and len(plugins) == 1
    plugin = plugins[0]
    assert isinstance(plugin, dict) and plugin.get("name") == PLUGIN_NAME
    source = plugin.get("source")
    assert isinstance(source, dict)
    assert source == {
        "source": "url",
        "url": REPOSITORY_URL,
        "ref": RELEASE_REF,
    }
    policy = plugin.get("policy")
    assert policy == {
        "installation": "AVAILABLE",
        "authentication": "ON_USE",
    }

    print("distribution validation: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
