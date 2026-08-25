# Consulting-slide images

Use this reference for diagrams, workflows, comparisons, case-study summaries, KPI visuals, and any request for a consulting-slide or presentation-like finish.

## Design the argument before the image

For each asset, write these fields in `image-plan.md` before prompting:

- `reader_question`: the question the image answers;
- `takeaway`: one conclusion the reader should retain;
- `evidence`: steps, cases, KPIs, constraints, or caveats supporting it;
- `visual_structure`: timeline, phased process, comparison, decision tree, or system map;
- `reading_order`: the intended eye path;
- `rendering_mode`: `full_image_generation` for every generated asset;
- `exact_text`: every visible character and number;
- `prohibited`: motifs and layouts that would weaken the result.

Do not generate until the body claim, source, placement, and takeaway agree. A visual must add synthesis: a process image shows sequence and gates; a comparison shows meaningful contrast; a case image ties actions to outcomes and limitations.

## Executive-slide visual grammar

Use a restrained visual system unless the Brief says otherwise:

- landscape composition with generous margins and a clear grid;
- one headline, one optional subhead, and no more than three primary groups;
- dark navy for conclusions, blue for progression, pale blue-gray for structure, and one accent color only when it encodes meaning;
- flat shapes, fine rules, short arrows, aligned cards, and small evidence labels;
- strong size contrast between takeaway, section labels, evidence, and caveats;
- numbers displayed as KPI blocks only when supported by the article's sources;
- caveats placed next to the claim they qualify, not buried as decorative footnotes;
- Japanese typography that remains legible in the note feed preview.

Avoid glossy 3D objects, floating app logos, humanoid robots, neon AI brains, excessive gradients, stock-photo office scenes, dense icon collections, mock browser chrome, ornamental charts, and generic template filler. Do not fabricate corporate logos or imply official company endorsement.

## Prompt contract

Describe the asset as a finished executive communication, not merely a style. Include:

1. canvas ratio and safe margins;
2. exact headline and supporting copy;
3. layout and reading order;
4. semantic meaning of every group, arrow, metric, and color;
5. typography hierarchy and whitespace;
6. factual caveats;
7. prohibited motifs;
8. an instruction to reproduce Japanese text and numbers exactly.

For a multi-asset article, repeat the palette, grid, line weight, card radius, and typography direction in every prompt. Vary the structure to match the content; do not force all images into the same template.

## Full image-generation rule

For every generated thumbnail and body image:

- generate every final visible asset with the image tool;
- do not rebuild the composition in HTML, SVG, canvas, PowerPoint, or a plotting library;
- allow only non-creative normalization after generation: resize, crop, MIME conversion, and color-profile normalization;
- regenerate rather than patching misspelled or clipped text with an overlay;
- preserve provenance by copying the accepted generator output into the run and hashing the final normalized file.

If the model cannot render required text exactly after reasonable regeneration, report that limitation before CMS mutation. Do not silently switch rendering modes. Use a deterministic overlay only when the user explicitly requests a hybrid or edited-image workflow.

## Visual QA gate

Inspect the final PNG at original size and at approximately 25% scale. Mark `quality_gate: pass` in `image-plan.md` only when all checks pass:

- the takeaway is understandable within five seconds;
- the visual structure matches the article's logic;
- every title, label, KPI, arrow direction, and caveat is correct;
- text is neither clipped nor crowded and remains readable at feed size;
- grouping, alignment, spacing, and contrast produce a clear reading order;
- cases and numbers have not been generalized beyond their sources;
- no unsupported logo, brand implication, face, watermark, or private data appears;
- the image adds information instead of duplicating nearby prose;
- all assets in the article read as one visual system.

Any failure means regenerate the asset and update its prompt, hash, dimensions, and package entry. User rejection also resets this gate for the affected asset and any companion image whose style no longer matches.
