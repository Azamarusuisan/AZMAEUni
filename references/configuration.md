# Configuration and artifact contracts

## Workspace resolution

Resolve the workspace in this order:

1. an absolute path supplied for the current request;
2. `NOTE_DRAFT_PIPELINE_HOME`;
3. `~/.config/write-note-drafts`.

The Skill package is never the user workspace. Reject a workspace that resolves inside the Skill checkout. On non-Windows systems, workspace directories use owner-only `0700` permissions and files use `0600`.

## Human-editable source of truth

Read all six files before each article:

| File | Owns |
|---|---|
| `NOTE_GENERATOR.md` | Master index, selected browser, and confirmed note identity |
| `PROFILE.md` | Author context, purpose, readers, boundaries, brand |
| `WRITING_PROFILE.md` | Observed style features from self-authored samples |
| `OPERATING_RULES.md` | Automation, outline confirmation, research, image, SEO/AIO, CTA, and note defaults |
| `ASSETS.md` | Approved local brand/reference assets |
| `templates/default.md` | Reusable article shape |

Blank values are unresolved. Ask only unresolved, conflicting, or high-risk fields. Save a current answer to these files only when the user confirms it is a reusable default.

The `ready` gate requires the selected browser and note handle, automation mode and compatible outline-confirmation setting, core author purpose/theme/reader, a resolved writing-style decision and core style fields, article length/research/image/SEO/AIO/CTA defaults, and a named default template. Use an explicit value such as `なし` or `今回は行わない` instead of leaving a deliberate opt-out blank.

`WRITING_PROFILE.md` stores observations and source URLs, not copied articles. With fewer than two samples, mark the profile provisional. Analyze:

- sentence endings and tone;
- line breaks and paragraph length;
- kanji ratio and sentence length;
- heading pattern;
- opening and closing;
- list and CTA usage.

## Browser and account state

`.state/workspace.json` is machine state:

```json
{
  "schema_version": 1,
  "status": "ready",
  "browser": "chrome",
  "expected_account_handle": "example",
  "created_at": "2026-01-01T00:00:00+00:00",
  "updated_at": "2026-01-01T00:00:00+00:00"
}
```

Rules:

- `browser` is exactly `chrome` or `safari`.
- `expected_account_handle` is recorded only after reading and confirming the logged-in note UI.
- `NOTE_GENERATOR.md` shows the same confirmed handle; if the two values differ, resume setup and reconfirm the live session instead of choosing either value silently.
- A different live handle stops all note mutations.
- Changing browser requires explicit setup revision and a new session check.
- Never add credentials, cookies, tokens, or recovery codes.

## Automation settings

Store these human-editable values in `OPERATING_RULES.md`:

```markdown
- 自動化モード: guided
- 構成確認: 毎回
- サムネイル: あり
- サムネイル文字入れ: あり
```

Allowed combinations:

| 自動化モード | 構成確認 | Behavior |
|---|---|---|
| `guided` | `毎回` | Confirm the Brief and outline |
| `guided` | `依頼時のみ` | Confirm the Brief; confirm the outline only when requested |
| `autopilot` | `依頼時のみ` | Require a theme, save a resolved Brief, then continue without confirmation |

Treat `autopilot` with `構成確認: 毎回` as a configuration conflict. Ask the user to choose `guided` or `依頼時のみ`; never reinterpret it silently.

`サムネイル` and `サムネイル文字入れ` are exactly `あり` or `なし`. When thumbnails are enabled, text is mandatory: record the approved exact copy in the Brief and image plan, then verify it character-for-character before preflight and upload.

Do not run `autopilot` before onboarding reaches `ready`. On later runs, the theme is the only unconditional per-article value. Ask about another value only when it is missing after default resolution, conflicts with another instruction, or creates a high-risk ambiguity.

## Asset links

List local image assets with ordinary Markdown image syntax, for example:

```markdown
![brand logo](./assets/brand-logo.png)
```

Validation:

- remote URLs, absolute paths, `..`, escaping symlinks, and missing files are rejected;
- only recognized image MIME types are accepted;
- each file must be no larger than 10 MB;
- SHA-256, MIME, size, and relative path are written to `.state/asset-lock.json`;
- references from `templates/default.md` resolve relative to that file;
- upload files are copied into the current run's `images/` directory.

The lock file is derived state. Edit `ASSETS.md`, not the lock.

## Run layout

`new-run` creates:

```text
runs/<run-id>/
├── state.json
└── images/
```

The orchestrator adds:

| Artifact | Required content |
|---|---|
| `brief.json` | Resolved requirements, automation gate, conflicts, and field origins |
| `research.jsonl` | One source record per line |
| `outline.md` | Title, headings, source/quote/image positions |
| `article.md` | Final local article |
| `image-plan.md` | Purpose, prompt, placement, size, alt |
| `article-package.json` | CMS-neutral manifest and content fingerprint |
| `cms-receipt.json` | Draft URL and save verification |
| `failure.json` | Cause, retry, manual recovery |

## Brief contract

Do not research or draft until the resolved Brief passes its automation gate. The minimum fields are:

```json
{
  "schema_version": 1,
  "run_id": "20260101T000000Z-topic",
  "mode": "full",
  "automation_mode": "autopilot",
  "outline_confirmation": "request_only",
  "topic": "required",
  "purpose": "required",
  "audience": "required",
  "target_characters": 3000,
  "tone": "saved profile or current instruction",
  "references": [],
  "research": {
    "include_overseas": false,
    "published_after": null,
    "published_before": null,
    "depth": "standard"
  },
  "images": {
    "count": 2,
    "style": "required when count > 0",
    "diagram": false,
    "thumbnail": true,
    "thumbnail_text": "exact copy or null"
  },
  "cta": null,
  "seo": false,
  "aio": true,
  "keywords": [],
  "field_origins": {},
  "conflicts": [],
  "resolved_at": "ISO-8601 timestamp",
  "confirmed_at": null,
  "outline_confirmed_at": null
}
```

Use `confirmed_at` for the user confirmation timestamp in `guided`. In `autopilot`, leave it `null` and proceed only when `topic` is present, `conflicts` is empty, all required values resolve, and `resolved_at` is present.
Set `outline_confirmed_at` before drafting when the run's `outline_confirmation` is `always`. Leave it `null` for `request_only`.

## Research record

Each JSONL line has:

```json
{
  "schema_version": 1,
  "source_id": "src-001",
  "title": "Source title",
  "url": "https://example.com/",
  "publisher": "Publisher",
  "source_type": "official",
  "language": "ja",
  "published_at": "2026-01-01",
  "date_status": "known",
  "accessed_at": "2026-01-02T00:00:00+00:00",
  "importance": "high",
  "facts": [],
  "figures": [],
  "quote_candidates": [],
  "key_points": [],
  "conflicts": []
}
```

Unknown publication dates remain unknown. Keep quotations short and include a page, heading, paragraph, or timestamp locator. Use YouTube, SNS, and note for attributable opinion; use primary sources for general factual claims where possible.

## Article package

The package contains no browser selector or CMS-specific HTML:

```json
{
  "schema_version": 1,
  "run_id": "run-id",
  "title": "Title",
  "body_path": "article.md",
  "headings": [],
  "links": [],
  "inline_hashtags": [],
  "images": [],
  "thumbnail": null,
  "claim_sources": {},
  "content_fingerprint": "sha256",
  "preflight": "pass"
}
```

An image entry contains a run-relative path, MIME, SHA-256, placement, alt text, and any supported claim IDs.

## Checkpoint and receipt

`state.json` records the current phase, status, completed phases, immutable idempotency key, opaque draft reference, sanitized draft URL, and timestamps. Valid statuses are `pending`, `running`, `waiting_user`, `completed`, `failed`, and `save_unverified`.

A successful receipt is:

```json
{
  "schema_version": 1,
  "cms": "note",
  "draft_url": "https://note.com/...",
  "saved_at": "ISO-8601 timestamp",
  "verification": {
    "status": "verified",
    "saved_state_seen": true,
    "content_fingerprint_matches": true,
    "title_matches": true,
    "required_images_present": true,
    "thumbnail_present": true,
    "inline_hashtags_present": true
  },
  "published": false
}
```

If the safe reread cannot confirm the content, use `save_unverified`; never call it success.

## Failure contract

`failure.json` and the user-facing report contain:

```text
phase
operation
cause
last_checkpoint
draft_url
retryable
retry_steps
manual_steps
local_artifacts
```

Do not persist full DOM dumps or screenshots by default. Redact session-like query parameters from diagnostic URLs.
