# Agent compatibility

The canonical package is this one Agent Skill directory. It supports:

- OpenAI Codex
- Anthropic Claude Code
- NousResearch Hermes Agent

“Hermes Agent” means `NousResearch/hermes-agent`; unrelated products with the same name are not covered.

## One shared installation

Clone once into the cross-agent directory:

```bash
mkdir -p "$HOME/.agents/skills"
gh repo clone Azamarusuisan/AZMAEUni "$HOME/.agents/skills/write-note-drafts"
```

Codex discovers the shared Agent Skills directory. Claude Code uses a personal-skill symlink:

```bash
mkdir -p "$HOME/.claude/skills"
ln -s "$HOME/.agents/skills/write-note-drafts" "$HOME/.claude/skills/write-note-drafts"
```

Do not run the `ln` command over an existing path. On systems where skill-directory symlinks are unavailable, clone or copy the same release into Claude’s skill directory instead.

For Hermes, add the absolute path of `~/.agents/skills` to `skills.external_dirs` in `~/.hermes/config.yaml`, then start a new session and verify with:

```bash
hermes skills list
```

Hermes URL installation copies the Skill into `~/.hermes/skills`; use `external_dirs` when one shared checkout is required.

## Runtime capability map

Run:

```bash
python3 scripts/manage.py doctor --agent <codex|claude|hermes> --browser <chrome|safari>
```

| Agent | Image capability | Chrome | Safari |
|---|---|---|---|
| Codex | installed `imagegen` Skill | installed Chrome plugin in the current Work/Codex chat | installed Computer Use plugin on macOS |
| Claude Code | connected image-generation Skill/MCP | Claude in Chrome | compatible semantic Computer Use MCP on macOS |
| Hermes Agent | `image_generate` | local Chromium CDP via `/browser connect` | `computer_use` with `cua-driver` on macOS |

The Doctor must verify the capability in the current session. Installation of this Skill does not install browser extensions, image providers, macOS permissions, or agent toolsets. Codex Chrome and Safari support is conditional on the corresponding ChatGPT plugin being installed, enabled, and exposed to the current Work/Codex chat. Never claim full automation when a required capability is absent.

Claude in Chrome must be enabled for the current Claude Code session and allowed to access note. Hermes Chrome must use the browser session reported by `/browser status`; the user logs into note manually in that session. Hermes Safari requires `hermes computer-use status` to pass.

## Windows hosts

Read [windows support and recovery](windows.md) before onboarding on a Windows host.
Native Windows uses Google Chrome only and invokes manager commands through
`scripts/manage.ps1`. Run `scripts/windows-doctor.ps1` first; its local checks
do not replace the live Agent runtime checks. WSL2 follows the Linux flow and
must not share a run or workspace with the Native Windows flow.

## Portable rules

- `SKILL.md`, references, templates, and `scripts/manage.py` are shared unchanged.
- `agents/openai.yaml` is Codex presentation metadata; other agents ignore it.
- Host-specific tool names are resolved only by the Doctor and browser/image provider sections.
- Workspace Markdown and run state stay outside the Git checkout and work identically across agents.

## Official references

- Agent Skills specification: <https://agentskills.io/specification>
- Codex Skills: <https://learn.chatgpt.com/docs/build-skills>
- Codex Chrome plugin: <https://learn.chatgpt.com/docs/chrome-extension>
- Codex Computer Use plugin: <https://learn.chatgpt.com/docs/computer-use>
- Anthropic Agent Skills: <https://github.com/anthropics/skills>
- Claude in Chrome: <https://support.claude.com/en/articles/12012173-get-started-with-claude-in-chrome>
- Hermes Skills: <https://github.com/NousResearch/hermes-agent/blob/main/website/docs/guides/work-with-skills.md>
- Hermes browser automation: <https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/browser.md>
- Hermes Computer Use: <https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/computer-use.md>
