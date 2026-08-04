# Visual partner and mascot contract

This contract keeps each user's approved mascot or character consistent across
note images without placing any buyer-specific asset in the distributed Skill.
The character is a writing and visual partner, not a mandatory product mascot.

## Mandatory first-use question

Ask every user this once during onboarding:

> noteの画像に継続して登場させたい「相棒」（マスコット／キャラクター）はいますか？

Record exactly one branch in `ASSETS.md`.

- `いない`: continue with the normal image workflow. Do not invent a character.
- `いる`: collect and validate the approved identity profile below.
- `これから作る`: stop setup before `ready`. Design candidate base images,
  show them to the user, and continue only after one is explicitly approved and
  the value is changed to `いる`. The user can instead change it to `いない`.

Do not infer a character from an article package, social avatar, logo, previous
user, or distributor asset. Imported packages remain article material until the
current workspace owner explicitly registers an image as their partner.

## Registered identity profile

For `画像の相棒: いる`, resolve every field in `ASSETS.md`:

- name and role in the article;
- one to five local reference images under workspace `assets/`;
- traits that must never change;
- elements that may vary between scenes;
- base illustration style and palette;
- appearance policy: `アイキャッチ中心`, `要点画像にも登場`, `毎画像`, or
  `記事ごとに確認`;
- `利用権確認: 確認済み` from the current user.

Reference images must use Markdown image links, remain inside the workspace,
match their actual PNG/JPEG/GIF MIME, be at most 10 MB, and be at least 256x256.
`validate` records their dimensions and SHA-256 in `.state/asset-lock.json`.
Never copy these assets into the Skill repository, release archive, manual, or
another user's workspace.

## Per-article Brief

Brief schema 3 requires `images.visual_partner`, including when no partner is
registered. A no-partner plan is:

```json
{"mode": "none", "use": false}
```

When a registered partner appears, record the exact name, planned placements,
approved source path/hash pairs, invariants, allowed variations, style, and
palette. Allowed placements are `thumbnail` and the one-based `body:1`,
`body:2`, and so on. Values must match the current `ASSETS.md` profile.

The saved appearance policy is a real gate:

- `アイキャッチ中心` requires the partner in the thumbnail when a thumbnail exists.
- `要点画像にも登場` requires it in at least one planned image.
- `毎画像` requires every body image and thumbnail placement.
- `記事ごとに確認` requires a fresh `confirmed_at` decision in that Brief,
  whether the answer is yes or no.

When an allowed plan omits the partner, save a specific `omission_reason`.

## Generation and identity QA

Before generation, inspect every selected local reference. Send the approved
reference files through the host image tool's supported reference-image
mechanism. Repeat the invariant traits, allowed variations, base style, and
palette in the prompt without paraphrasing them into different traits.

For each generated file:

1. inspect the actual output, not only the generator response;
2. compare every invariant trait with the approved references;
3. reject an extra or missing signature feature, palette drift, a substituted
   species/person, unintended logo, watermark, or foreign character;
4. separately verify image text, dimensions, cropping, and feed-size contrast;
5. record the source paths and SHA-256 values in `image-plan.md`;
6. record `name`, `source_paths`, `source_sha256`, and
   `identity_checked: true` under that image's `visual_partner` entry in
   `article-package.json`.

Preflight rejects a planned partner image when its identity QA is absent, its
source hash differs from the current approved asset, or the image plan omits an
identity field. A missing or invalid source stops before CMS mutation. Never
generate a lookalike substitute to keep the run moving.

Any redesign of an invariant trait, base style, palette, or primary reference
requires new explicit user approval and an updated `ASSETS.md` profile before
the next run.
