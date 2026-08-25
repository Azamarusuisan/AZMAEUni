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

If rich anchor creation is unavailable, insert a readable caption plus the canonical raw HTTPS URL as a clickable fallback. Do not claim the anchor was verified.

## Video and embeds

Embed a video only when it materially improves comprehension, demonstrates a workflow, or supplies primary evidence. Prefer the original publisher's official channel or the user's own media. Do not embed scraped copies, reaction videos as factual authority, or media with unclear provenance.

For every required embed, record:

- canonical HTTPS URL;
- provider and publisher;
- exact title observed on the source page;
- article placement and the question it answers;
- a one-sentence caption explaining why it is included;
- a normal link fallback using the same canonical URL;
- `required: true|false`.

In the note editor:

1. place the cursor at the planned block boundary;
2. open the current semantic insertion menu;
3. choose `埋め込み` or the observed equivalent;
4. enter one verified URL;
5. wait for the preview to finish;
6. verify provider/title and surrounding block order before inserting the next item.

Do not autoplay, log into the provider, accept marketing consent, or interact with account controls. A preview failure does not authorize a different URL. Keep the caption and fallback link, mark a required embed missing, and report `save_unverified` when the user explicitly required the embed.

## Rich-editor QA

Before stage completion, confirm:

- H2/H3 levels and order match the Article Package;
- lists are actual list blocks rather than lines containing hyphens or numbers;
- code samples are code blocks and contain no secret or credential;
- links are clickable and canonical;
- every required embed renders once in the intended position;
- images, embeds, and headings are not duplicated;
- the article remains readable when an embed is unavailable because its caption and fallback link are present.
