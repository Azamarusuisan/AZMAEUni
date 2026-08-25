# Rich media for note articles

Use this reference when the user requests rich-editor formatting, video, embeds, audio, files, strong link handling, or a visually complete note draft.

## Plan the block structure

Represent the body as ordered semantic blocks before CMS mutation:

- paragraph;
- H2 large heading;
- H3 small heading;
- unordered or ordered list;
- quote;
- code;
- divider;
- verified anchor link;
- image;
- embed;
- inline hashtags.

Do not paste Markdown markers as visible text when the editor provides semantic formatting. Use the current rich menu, editor-documented Markdown shortcut, or keyboard shortcut only after observing the actual control. Re-read the draft and confirm the resulting semantic structure.

## Links

Open each external URL read-only before relying on it. Use only credential-free HTTPS URLs. Record the intended anchor text, destination, source role, and placement in the Article Package or image/rich-media plan.

After insertion, verify both the visible anchor text and final destination. Do not rely on search-result redirects, ad links, shortened URLs, tracking parameters, or a title inferred from a snippet. For technical facts, prefer official documentation; for company cases, identify whether the source is a corporate statement, vendor case, employee post, or independent report.

If rich anchor creation is unavailable, keep the readable caption, save the draft as `save_unverified`, and report the missing link. Do not expose the raw URL in ordinary prose or claim the anchor was verified.

## Video and embeds

Embed a video only when it materially improves comprehension, demonstrates a workflow, or supplies primary evidence. Prefer the original publisher's official channel or the user's own media. Do not embed scraped copies, reaction videos as factual authority, or media with unclear provenance.

For every required embed, record:

- canonical HTTPS URL;
- provider and publisher;
- exact title observed on the source page;
- article placement and the question it answers;
- a one-sentence caption explaining why it is included;
- a normal link fallback using the same canonical URL;
- `required: true`.

Optional media stays a descriptive fallback link and is not added to `article-package.json embeds` until it becomes required.

In the note editor:

1. place the cursor at the planned block boundary;
2. open the current semantic insertion menu;
3. choose `埋め込み` or the observed equivalent;
4. enter one verified URL;
5. wait for the preview to finish;
6. verify provider/title and surrounding block order before inserting the next item.

Do not autoplay, log into the provider, accept marketing consent, or interact with account controls. A preview failure does not authorize a different URL. Keep the caption and fallback link, mark a required embed missing, and report `save_unverified` when the user explicitly required the embed.

### note article cards

Use a native article card for a planned previous/related note article that occupies its own block; keep inline citations as normal anchors. Record only required cards in `article-package.json embeds` with canonical `url`, observed `provider`, exact `title`, exact `fallback_text`, and `required: true`. The URL and fallback text must match exactly one unindented top-level standalone descriptive Markdown anchor, and card order must follow anchor order. The Markdown anchor is the portable fallback; in note, replace that one block with the card rather than displaying both.

Use only the currently observed semantic `埋め込み` or equivalent control. After preview and again after reopening the draft, confirm one card, its exact title/provider, canonical destination, and surrounding block order. At the first failure, stop before all later embeds so the verified list remains an ordered prefix. Leave or restore the descriptive fallback anchor, record that URL and every unattempted suffix as `embed:<canonical-url>` missing, and use `save_unverified`.

For reread comparison, normal anchors are the source anchors excluding successful card fallbacks. Exclude the matched fallback block and card block from both sides of the normalized text fingerprint; never weaken comparison for the rest of the article.

## Rich-editor QA

Before stage completion, confirm:

- H2/H3 levels and order match the Article Package;
- lists are actual list blocks rather than lines containing hyphens or numbers;
- code samples are code blocks and contain no secret or credential;
- links are clickable and canonical;
- every normal link has meaningful visible text; raw URLs appear only inside semantic code blocks;
- every required embed renders once in the intended position;
- images, embeds, and headings are not duplicated;
- the article remains readable when an embed is unavailable because its caption and fallback link are present.
- the reread contains no pseudo-list paragraphs or collapsed command, JSON, configuration, or log paragraphs.
