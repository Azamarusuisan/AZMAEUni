# Note Draft Pipeline

`Note Draft Pipeline` is a distributable Agent Skill for OpenAI Codex, Anthropic Claude Code, and NousResearch Hermes Agent. It builds a personal “note generator” on first use, then interviews, researches, outlines, writes, creates images, and saves the result to note as an unpublished draft.

It uses the note account already logged in to a user-selected Chrome or Safari session. It never publishes, schedules, switches accounts automatically, or stores login secrets.

## What works after installation

On the first `$write-note-drafts` call, the Skill:

1. runs an environment Doctor for the workspace, web research, and Image Skill;
2. asks for Chrome or Safari and checks only the selected browser capability;
3. confirms the logged-in note handle;
4. interviews for author profile, readers, writing defaults, research, images, thumbnail text, SEO/AIO, CTA, and automation mode;
5. analyzes user-confirmed self-authored articles;
6. creates a private Markdown workspace.

On later article requests it reruns the Doctor, reads that workspace, researches, writes, invokes the current host's verified image capability, and saves one verified note draft. `guided` confirms the resolved Brief. `autopilot` requires a theme, asks only about missing/conflicting/high-risk values, saves the resolved Brief, and continues without confirmation.

Git installation cannot start a conversation by itself. The first matching prompt triggers onboarding.

## Runtime requirements

- Codex, Claude Code, or NousResearch Hermes Agent
- Python 3 standard library
- Web search/browsing capability
- a supported image-generation capability
- a supported Chrome or Safari capability from [Agent compatibility](references/agent-compatibility.md)
- a note session the user can log into manually

Safari and Chrome are selected explicitly during setup. The Skill does not fall back to another browser without permission.

Before onboarding and every article, the runtime Doctor checks:

- workspace read/write access, Python 3, manager status, web research, and the host image provider;
- the host Chrome provider when Chrome is selected;
- macOS, Safari, host Computer Use, and required Accessibility/Screen Recording permissions when Safari is selected.

A failed check stops the run with setup and retry instructions. Documentation alone never counts as a passed live capability check.

## Install from Git

Authenticate with GitHub using SSH or `gh`; never put a personal access token in a clone URL or Skill config. Clone the private repository once:

```bash
mkdir -p "$HOME/.agents/skills"
gh repo clone Azamarusuisan/AZMAEUni "$HOME/.agents/skills/write-note-drafts"
```

Codex discovers that shared directory. For Claude Code, link the same checkout:

```bash
mkdir -p "$HOME/.claude/skills"
ln -s "$HOME/.agents/skills/write-note-drafts" "$HOME/.claude/skills/write-note-drafts"
```

For Hermes Agent, add the absolute path of `~/.agents/skills` to `skills.external_dirs` in `~/.hermes/config.yaml`, start a new session, then run `hermes skills list`.

Do not overwrite an existing path with the symlink command. Do not put personal profiles or generated articles in the Git checkout. See [Agent compatibility](references/agent-compatibility.md) for provider setup.

## First use

```text
Codex: $write-note-drafts を使ってnoteを書いて
Claude/Hermes: /write-note-drafts noteを書いて
```

The private workspace defaults to:

```text
~/.config/write-note-drafts
```

Override it with `NOTE_DRAFT_PIPELINE_HOME` or an explicit absolute path. The workspace contains:

```text
NOTE_GENERATOR.md
PROFILE.md
WRITING_PROFILE.md
OPERATING_RULES.md
ASSETS.md
templates/default.md
assets/
.state/
runs/
```

The Markdown files are the editable personalization source. `.state/` and `runs/` contain machine state and article artifacts.

## Usage

Normal article:

```text
$write-note-drafts でnoteを書いて。テーマは生成AIの社内導入。
```

Outline only:

```text
$write-note-drafts で、まず構成だけ確認したい。
```

Style learning:

```text
$write-note-drafts で、この3本の自分の記事から文体を学習して。
```

Setup revision:

```text
$write-note-drafts の画像設定と通常CTAを変更して。
```

Autopilot:

```text
$write-note-drafts の自動化モードをautopilotにして。構成確認は依頼時のみ。
```

After onboarding is `ready`, a later request can be as short as:

```text
$write-note-drafts でnoteを書いて。テーマは生成AI時代の採用。
```

## Automation modes

- `guided`: ask only missing/conflicting/high-risk questions, show the resolved Brief, and require confirmation. Confirm the outline when `構成確認` is `毎回` or explicitly requested.
- `autopilot`: require the theme, resolve all other values from the current request and saved Markdown, persist the Brief, and continue through research, writing, images, and draft save without confirmation.

Use `構成確認: 依頼時のみ` with `autopilot`. The incompatible combination `autopilot` plus `構成確認: 毎回` is resolved during setup instead of causing a hidden behavior change. First-use onboarding remains mandatory in both modes.

## Browser behavior

The Skill uses only the currently logged-in account. The handle confirmed during onboarding is compared before every note mutation.
The comparison is also enforced by the local manager's `verify-account` gate.

- logged out: the user logs in manually;
- different handle: stop and ask the user to switch manually;
- MFA, CAPTCHA, consent, or unknown screen: stop;
- exact handle match: create or resume one draft and save it;
- save cannot be reread and verified: report `save_unverified`.

No password, cookie, token, or MFA value is written to the workspace.

## Images and assets

Generated images use the Doctor-verified host capability: Codex `imagegen`, a connected Claude image Skill/MCP, or Hermes `image_generate`. Results are copied into the current run before upload. Enabled thumbnails always include approved text; the exact copy is recorded and checked character-for-character before upload.

Reusable assets belong under workspace `assets/` and are referenced from `ASSETS.md` with local Markdown image links:

```markdown
![brand logo](./assets/brand-logo.png)
```

Absolute paths, remote image links, traversal, workspace-escaping symlinks, missing files, unsupported MIME types, and files over 10 MB are rejected.

## Configuration changes

Edit the workspace Markdown or ask the current agent to update it. Reusable defaults go into the profile/rules/template; one-off article directions stay in the current Brief.

To change Chrome/Safari or the expected note handle, run setup again and reconfirm the live session. Do not edit credentials into any file.

## Update

Update only the shared Skill checkout:

```bash
git -C "$HOME/.agents/skills/write-note-drafts" pull --ff-only
```

Keep the external workspace unchanged. Back it up before a schema migration. Initialization is non-destructive and does not overwrite existing Markdown.

## Release validation

Runtime code uses only the Python standard library. Maintainers additionally install pinned PyYAML in an isolated environment, then run:

```bash
python -m pip install --requirement requirements-validation.txt
python scripts/validate_skill.py .
python scripts/manage.py self-check
```

## Uninstall

Remove the shared checkout and any Claude symlink or Hermes `external_dirs` entry. The private workspace is deliberately retained. Delete it separately only after confirming that its profiles, articles, and images are no longer needed.

## Safety and limitations

- Draft creation/update and verification only
- No publish or scheduled post
- No automatic account switching
- No password/session storage
- No bypass of MFA, CAPTCHA, or consent
- Browser control is capability-gated
- No silent browser fallback
- Live compatibility depends on the current note UI and must be verified per browser/OS release

If browser staging fails, the Skill preserves `article.md`, source records, image files, and a manual insertion checklist.

## License

Proprietary; see [LICENSE](LICENSE). Repository access alone does not grant redistribution or resale rights.

## Design references

- [Architecture](references/architecture.md)
- [Agent compatibility](references/agent-compatibility.md)
- [Configuration](references/configuration.md)
- [Workflows](references/workflows.md)
- [Chrome provider](references/browser-chrome.md)
- [Safari provider](references/browser-safari.md)
- [note draft adapter](references/cms-note.md)
