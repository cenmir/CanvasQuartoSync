# TODO

## Comment highlighting on math/KaTeX content

Comments on text containing rendered math (KaTeX) are saved correctly but not highlighted in the preview. The selected text from KaTeX renders as unicode characters split across many `<span>` elements, which don't match as a single text node in the DOM walker.

**Possible approaches:**
- Match by surrounding plain-text context instead of the target text itself
- Add `data-source-line` attributes during preprocessing and match by line number
- Use Range API to find text across element boundaries

## "Last synced" timestamp for drift detection

Add a `canvas.last_synced` ISO timestamp to the YAML frontmatter of `.qmd` files after a successful sync to Canvas. Then in the Module Structure panel, compare this timestamp against the file's `mtime` to show a yellow "modified since last sync" indicator — lighter weight than running a full diff.

**Changes needed:**
- Python sync handlers: write `last_synced` into frontmatter after successful upload
- Module Structure panel: read `last_synced` from matched local files and compare with `mtime`
- Show a yellow dot or badge for files modified after their last sync

## Synced scrolling

Editor-to-preview scroll sync was removed due to poor alignment (proportional scrolling doesn't account for images/tables making the preview taller). Revisit with a heading-anchor or source-map approach.
