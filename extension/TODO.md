# TODO

## Comment highlighting on math/KaTeX content

Comments on text containing rendered math (KaTeX) are saved correctly but not highlighted in the preview. The selected text from KaTeX renders as unicode characters split across many `<span>` elements, which don't match as a single text node in the DOM walker.

**Possible approaches:**
- Match by surrounding plain-text context instead of the target text itself
- Add `data-source-line` attributes during preprocessing and match by line number
- Use Range API to find text across element boundaries

## Synced scrolling

Editor-to-preview scroll sync was removed due to poor alignment (proportional scrolling doesn't account for images/tables making the preview taller). Revisit with a heading-anchor or source-map approach.
