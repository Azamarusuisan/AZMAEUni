# Final editorial audit

Use this once after the article and images are complete and before CMS staging. Its purpose is to catch expensive editor-side rework, not to expand the article.

## Brief and reader

- The opening names the actual reader problem and the result this article delivers.
- The depth, vocabulary, examples, and CTA match the resolved audience and purpose.
- A free article contains no paywall, purchase, premium, or sales-state language. A paid article matches the confirmed free/paid promise and boundary.
- The article stays inside the agreed scope. Remove interesting detours that do not change the reader's next action.

## Claims and evidence

- Every important factual claim maps to a `claim_sources` entry and a readable source record.
- Product capabilities, proposed uses, public case studies, and the author's own hypotheses are labeled differently.
- Current, preview, beta, early-access, deprecated, and historical behavior are not presented as the same thing.
- Numbers retain their population, date, unit, and caveat. Community reports remain attributed experience or counterpoints.

## Structure and usefulness

- The conclusion appears early, each section has one job, and later sections do not restate earlier explanations.
- H2/H3 text and order match `outline.md` and `article-package.json`.
- Define unfamiliar terms near first use. Add a glossary only for terms readers must revisit; do not create a glossary to rescue unexplained prose.
- Procedures include prerequisites, the action, a check, a likely failure, and a safe recovery where relevant.
- Prompts and code are complete, internally consistent, and followed by a way to verify the result.

## CMS readiness

- Code fences are closed and preserve internal blank lines.
- Links are canonical, unique in the package, and represented by descriptive Markdown anchors whose ordered unique targets exactly match `article-package.json links`; each required card in `embeds` matches exactly one standalone fallback anchor and follows anchor order; exposed raw URLs are allowed only inside fenced code.
- Lists use Markdown list syntax, quotes use block quotes, and commands, JSON, configuration, and logs use fenced code. Reject pseudo-list characters and multiple collapsed items on one line.
- Each body image appears once at its planned position. Its caption states what the reader should notice and does not duplicate a nearby paragraph.
- Figure numbering, captions, hashtags, and CTA are consistent and not duplicated.
- Remove placeholders, editing notes, internal claim IDs, duplicate raw URLs, and accidental empty paragraphs.

## Freeze the package

After corrections, update `outline.md`, `article.md`, `image-plan.md`, `article-package.json`, image hashes, and the content fingerprint wherever affected. Run preflight again. Do not stage a package after changing any of those files without rerunning this audit and preflight.
