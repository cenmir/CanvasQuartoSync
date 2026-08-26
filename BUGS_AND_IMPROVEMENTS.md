# Bugs & Improvements

Active known issues and planned enhancements.

For past issues and design rationale, see [LESSONS_LEARNED.md](LESSONS_LEARNED.md).

---

## Known Bugs

### Quiz "Save It Now" Banner After Sync (Canvas API Limitation)

When syncing a quiz that has student submissions, Canvas shows an "Unsaved Changes" banner. The script cannot unpublish/republish the quiz (Canvas blocks this), so the quiz snapshot is not regenerated.

- **Root cause**: The Canvas REST API only regenerates `quiz_data` during a `workflow_state` transition. The Canvas UI has a dedicated endpoint for this, but it requires SSO session auth.
- **Mitigation**: The script detects this, updates the quiz in-place, and prints a URL so the user can click "Save It Now" manually.
- **Status**: Cannot be fixed without Canvas-side changes.

---

## Planned Improvements
## 📋 Kit Gaps

Behaviour that content authors (or their AI assistants) hit but which isn't documented,
collected from `.claude/kit-gaps.md` files in content folders. Promote entries here into
`content_kit/skills/canvas-content/reference/` once confirmed.

- **Quarto shortcodes beyond `{{< video >}}`** — `{{< include >}}` and `{{< embed >}}`
  are untested against the Canvas render path.
- **Cross-page figure references** — `@fig-label` across separate Canvas pages is
  undefined; Quarto numbering is per-document.
- **Client-side diagram blocks** — Mermaid and friends render via JavaScript, which
  Canvas strips. Presumed unsupported; needs confirming, and if so a documented
  alternative (render to an image at author time).

---

## 🚀 Future Improvements

### Custom Quarto Profiles/Args

The system uses a hardcoded render command: `quarto render ... --to html`. Allow passing `--quarto-args` via CLI, or detect `_quarto.yml` in the content root.

### New Quizzes: Additional Question Types

Remaining New Quizzes API types not yet implemented:
- `matching`, `categorization`, `ordering`
- `essay`, `file-upload`
- `rich-fill-blank`, `hot-spot`

Each type has its own `interaction_data` and `scoring_data` structure. See the [Canvas API docs](https://canvas.instructure.com/doc/api/new_quiz_items.html#Question+Types-appendix).

### VS Code Extension

See [extension/TODO.md](extension/TODO.md) for extension-specific issues (comment highlighting on math content, scroll sync).
### ~~3. New Quizzes: Additional Question Types~~ (Partially Implemented)
`numeric` and `formula` questions were added. The remaining New Quizzes API types are:
- `matching` — match items to categories
- `categorization` — sort items into groups
- `ordering` — arrange items in sequence
- `numeric` — numeric input with margin of error
- `essay` — free-text response (manually graded)
- `file-upload` — student file submission
- `rich-fill-blank` — fill-in-the-blank with rich content
- `hot-spot` — click on a region of an image

Each type has its own `interaction_data` and `scoring_data` structure. See the [official API docs](https://canvas.instructure.com/doc/api/new_quiz_items.html#Question+Types-appendix) for details.

---

### ~~4. New Quizzes: Formula Questions with Variables~~ (Implemented)
The New Quizzes `formula` question type supports **parameterized questions**.

_Implemented via local evaluation utilizing `asteval` to precalculate and upload data sets per the Canvas API requirements._

**Considerations**:
- Requires defining variables (name, min, max, precision) and a formula string in the question metadata.
- The API uses `generated_solutions` — pre-computed answer sets that must be calculated and included in the payload.
- A new frontmatter/JSON syntax would be needed to define variables and formulas in a user-friendly way.
- 
---

### 5. Canvas Asset Removal Tool
Develop a dedicated utility or CLI flag to remove assets from Canvas that were previously synced.

**Details**:
- The tool should use the `.canvas_sync_map.json` file to identify items (Pages, Assignments, Quizzes, Files) that it "owns" in the Canvas course.
- Useful for cleaning up a course after a major restructuring or when wanting to start fresh without manually deleting dozens of items in the Canvas UI.
- Should include a `--dry-run` option to show what would be deleted.

---

### ~~6. One-line Install Command~~ (Implemented)
A PowerShell one-liner installs the entire system interactively.

_Implemented as `install.ps1` — checks for Python/Quarto/Git, clones the repo, creates a venv at `~/venvs/canvas_quarto_env`, installs packages from `requirements.txt`, and walks the user through Canvas API credential setup. Run via `irm .../install.ps1 | iex`._

---

### 7. Study Guide (Dual HTML + PDF Output)
A single `.qmd` file that produces **two Canvas artifacts** from one source:

1. **Canvas Page (HTML)** — the student-facing welcome/study guide, added to the module where the file lives.
2. **PDF** — a standardized regulatory document, uploaded to a separately specified module.

**Motivation**: Regulatory requirements mandate a formatted PDF study guide in every course. Rather than maintaining two separate files, a single QMD file uses Quarto's conditional content blocks (`.content-visible when-format="html"` / `when-format="pdf"`) to include shared and format-exclusive sections.

**Design**:
- New `canvas.type: study_guide` triggers a dedicated `StudyGuideHandler`.
- Frontmatter includes a `canvas.pdf.target_module` field (required) specifying which module receives the PDF.
- The handler renders the QMD twice (`--to html` and `--to pdf`), syncs the HTML as a Canvas Page, and uploads the PDF as a file item in the target module.
- Requires a LaTeX distribution (e.g., `quarto install tinytex`) for PDF rendering.
- If PDF rendering fails, the HTML page is still synced (partial success).

---

### ~~8. Unified Date/Time Handling~~ (Implemented)
Dates used to travel from source file to Canvas untouched, so their meaning depended on
the file format, on whether the author quoted them, and on which handler consumed them.

_Implemented in `handlers/dates.py`. Authors now write course-local wall clock
(`due_at: "2026-11-17T09:00:00"`) and the tool converts to the correct UTC instant,
daylight saving included. The zone comes from `timezone` in `config.toml`, else the
Canvas course's own `time_zone`; resolution is lazy, so an all-`Z` course needs no
configuration. Values already carrying `Z` or an offset pass through untouched, so this
was not a content migration._

_This also closed two bugs: New Quizzes aborting on unquoted `.qmd` dates (the payload
is JSON, and `to_canvas_iso()` always returns a `str`), and calendar events being
hardcoded to UTC. Converting calendar times additionally required replacing the
duplicate check, which had been substring-matching a local time against the UTC
`start_at` Canvas returns. See LESSONS_LEARNED.md for the reasoning; `tzdata` is now
required on Windows._
