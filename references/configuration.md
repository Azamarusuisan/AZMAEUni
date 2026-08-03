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
| `OPERATING_RULES.md` | Automation, outline confirmation, research, free/paid access, image, SEO/AIO, CTA, and note defaults |
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
| `paid-plan.md` | Paid promise, exact paywall heading, price proposal, and confirmation state; paid articles only |
| `image-plan.md` | Purpose, prompt, placement, size, alt |
| `article-package.json` | CMS-neutral manifest and content fingerprint |
| `cms-receipt.json` | Draft URL and save verification |
| `failure.json` | Cause, retry, manual recovery |

## Brief contract

Do not research or draft until the resolved Brief passes its automation gate. The minimum fields are:

```json
{
  "schema_version": 2,
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
    "depth": "standard",
    "questions": ["What must this article prove?"],
    "source_categories": ["government", "academic", "corporate", "news"],
    "preferred_platforms": ["auto"]
  },
  "access": {
    "model": "paid",
    "purchase_promise": "What the reader can do after purchase",
    "free_preview_delivers": ["Audience fit and the method overview"],
    "paid_section_delivers": ["Procedure", "Template", "Checklist"],
    "paywall_after": "## この先で分かること",
    "paywall_confirmed_at": null,
    "price": {
      "currency": "JPY",
      "proposal": 980,
      "rationale": "Includes a reusable procedure and template",
      "confirmed_at": null
    },
    "referral_rate": {
      "proposal_percent": null,
      "confirmed_at": null
    }
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

`references` is a list of HTTPS URL strings or objects containing an HTTPS `url`. Credentials embedded in URLs are rejected. Open each supplied URL before claiming to have read it; record inaccessible pages as inaccessible rather than reconstructing their contents from a search result.

`access.model` must resolve to `free` or `paid` in every run. The saved workspace default may be `ask_each_time`; it is not a resolved run value. For `paid`, the purchase promise, non-empty free and paid deliverables, exact paywall heading, positive integer price proposal, ISO currency code, and price rationale are required. The proposal can be generated before confirmation. CMS staging additionally requires an attended `guided` run plus current-run timestamps in `price.confirmed_at` and `paywall_confirmed_at`. General Brief or outline confirmation timestamps do not satisfy these commercial confirmations.

Brief schema 2 introduces the required `access` object. An in-progress schema 1 Brief created by an older release and lacking `access` remains valid as a free article, so an update does not strand an existing run. New runs always write schema 2.

## Research record

Each JSONL line has:

```json
{
  "schema_version": 1,
  "source_id": "src-001",
  "title": "Source title",
  "url": "https://example.com/",
  "platform": "e-Stat",
  "publisher": "Publisher",
  "source_type": "official",
  "evidence_role": "primary",
  "research_question": "What is the latest official figure?",
  "language": "ja",
  "published_at": "2026-01-01",
  "date_status": "known",
  "accessed_at": "2026-01-02T00:00:00+00:00",
  "importance": "high",
  "facts": [],
  "figures": [],
  "quote_candidates": [],
  "key_points": [],
  "access_status": "read",
  "conflicts": []
}
```

Unknown publication dates remain unknown. Keep quotations short and include a page, heading, paragraph, or timestamp locator. `evidence_role` is `primary`, `analysis`, `discovery`, `experience`, or `counterpoint`. Use YouTube, SNS, reviews, and note for attributable opinion or experience; use primary sources for general factual claims where possible. Choose platforms by question using [research-platforms.md](research-platforms.md), not by mechanically searching every listed service.

Schema 2 preflight requires every non-empty JSONL row to have a unique safe `source_id`, credential-free HTTPS `url`, non-empty `platform`, `source_type`, `research_question`, and `accessed_at`, an allowed `evidence_role`, and `access_status` of `read`, `inaccessible`, or `excluded`. This records inaccessible sources without pretending they were read. Schema 1 runs retain their older record shape for update compatibility.

## Article package

The package contains no browser selector or CMS-specific HTML:

```json
{
  "schema_version": 2,
  "run_id": "run-id",
  "title": "Title",
  "body_path": "article.md",
  "headings": [],
  "links": [],
  "inline_hashtags": [],
  "access": {
    "model": "paid",
    "paywall_after": "## この先で分かること",
    "price": {"currency": "JPY", "proposal": 980}
  },
  "images": [
    {
      "path": "images/diagram.png",
      "mime": "image/png",
      "sha256": "hex digest",
      "kind": "diagram",
      "width": 1200,
      "height": 675,
      "placement": "after section 2",
      "alt": "URLから記事の材料を整理する三段階の図解",
      "text": "URLを渡すだけで、記事の材料が見える",
      "text_verified": true
    }
  ],
  "thumbnail": null,
  "claim_sources": {},
  "content_fingerprint": "sha256",
  "preflight": "pass"
}
```

An image entry contains a run-relative path, MIME, SHA-256, kind, actual pixel dimensions, placement, alt text, and any supported claim IDs. Allowed kinds are `article`, `diagram`, `comparison`, `flow`, and `thumbnail`. When a rendered image contains text, include the exact `text` and set `text_verified` only after visually checking the final file character-for-character. Body-image count must exactly match `brief.json images.count`; a thumbnail is counted separately. note thumbnails must be exactly `1280x670`.

The package `access.model` must equal the Brief. For paid articles, `paywall_after` and the price proposal must match the Brief, the exact heading must exist in `article.md`, and `paid-plan.md` must contain the same heading and amount. This proves that the paid article is structurally complete; it does not mean the CMS sale is active.

## Checkpoint and receipt

`state.json` records the current phase, status, completed phases, immutable idempotency key, opaque draft reference, sanitized draft URL, and timestamps. Valid statuses are `pending`, `running`, `waiting_user`, `completed`, `failed`, and `save_unverified`.

A successful schema 2 receipt is:

```json
{
  "schema_version": 2,
  "cms": "note",
  "draft_url": "https://note.com/...",
  "saved_at": "ISO-8601 timestamp",
  "verification": {
    "status": "verified",
    "saved_state_seen": true,
    "content_fingerprint_matches": true,
    "title_matches": true,
    "required_images_present": true,
    "expected_body_image_count": 2,
    "observed_body_image_count": 2,
    "verified_image_paths": ["images/diagram-1.png", "images/diagram-2.png"],
    "thumbnail_present": true,
    "verified_thumbnail_path": "images/thumbnail.png",
    "inline_hashtags_present": true
  },
  "published": false
}
```

If the safe reread cannot confirm the content, use `save_unverified`; never call it success.

New runs write receipt schema 2. `checkpoint --phase verify --status completed` validates the receipt against `article-package.json` and rejects missing or reordered body images, a missing thumbnail, a mismatched draft URL, non-false `published`, or any false core verification flag. Schema 1 remains readable for an in-progress older run, but still requires `required_images_present: true` and any required thumbnail before completion.

A partial schema 2 draft keeps the same count, path, and thumbnail fields, sets `verification.status: save_unverified`, and adds a non-empty `missing_required_items` list containing every unobserved required image path. This permits the same draft to be resumed without pretending the article is complete.

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
