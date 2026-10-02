# Claude Code — Project Instructions

Start with [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for architecture and
[TESTING.md](TESTING.md) for the full test guide.

## E2E manual verification (when testing content changes)

The E2E suite (`tests/e2e/`, run with `-m canvas`) auto-checks everything that
can be read back from the Canvas API — including math rendered to equation
images (each image is HTTP-fetched to confirm it renders), callouts/code styled,
tables, dates, grading, indentation, quiz settings, etc. A few things still need
human eyes: the rendered **PDF**, the **New Quizzes UI**, and overall **visual
polish/branding**.

Manual verification is intentionally **advisory** — there is deliberately **no**
pytest sign-off gate.

**Behavioral rule for AI agents:** when you run the E2E suite while testing new
code that affects synced content, after it passes you MUST prompt the developer
to perform the manual checks in
[tests/e2e/MANUAL_CHECKLIST.md](tests/e2e/MANUAL_CHECKLIST.md), wait for their
feedback, and fold their pass/fail into your summary. Do **not** declare a content
change verified on "N passed" alone until the developer has confirmed the visual
items (or explicitly waived them).

## The VS Code extension belongs upstream

Decided: `extension/` is part of this project, not a fork-local add-on. It ships
with the tool, the installers set it up, and the docs tell people to use it.

**It has not landed upstream yet.** `JonssonLogic/main` has no `extension/`
directory at all; it exists only in the `cenmir` fork, along with the installers
(`install.ps1`, `install.sh`, `init_course.bat`, `update.ps1`, `dev-deploy.ps1`)
and the VSIX build workflow. Until that changes, this trips up every pull
request that touches the panel:

```
a branch cut from cenmir/main, diffed against its own base:  ~12 files
the same branch, diffed against JonssonLogic/main:           ~73 files, 14k lines
```

The extension comes along as collateral and buries the actual change.

**So until the extension lands upstream, split a branch before opening a PR:**
the Python half goes upstream now and is reviewable on its own; the extension
half waits. Most fixes divide cleanly, because the Python side answers a
question and the panel only displays the answer.

Do not "solve" this by rebasing onto `upstream/main` and dropping the extension
changes. The panel work is real and wanted; it is the ordering that is wrong,
not the work.
