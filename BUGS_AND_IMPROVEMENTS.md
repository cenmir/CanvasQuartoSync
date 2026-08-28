# Bugs & Improvements

**Tracking moved to [GitHub issues](https://github.com/JonssonLogic/CanvasQuartoSync/issues).**

This file used to hold both. It stopped working once the repo had more than one
maintainer: it conflicted on every upstream merge, completed items piled up as
strikethrough because a file has no way to close anything, and a pull request
could not say which entry it addressed.

Everything live in it has been moved:

| Was | Now |
|:---|:---|
| Kit gaps, three untested authoring behaviours | [#19](https://github.com/JonssonLogic/CanvasQuartoSync/issues/19) |
| Custom Quarto profiles and args | [#20](https://github.com/JonssonLogic/CanvasQuartoSync/issues/20) |
| New Quizzes, remaining question types | [#21](https://github.com/JonssonLogic/CanvasQuartoSync/issues/21) |
| Canvas asset removal tool | [#22](https://github.com/JonssonLogic/CanvasQuartoSync/issues/22) |

Implemented and therefore deleted rather than moved: formula questions with
variables, the one-line install command, the dual HTML plus PDF study guide, and
unified date handling. Their reasoning lives in
[LESSONS_LEARNED.md](LESSONS_LEARNED.md).

Personal scratch lists are not tracked. `TODO.md` is gitignored: keep one if it
helps you think, and turn an entry into an issue when it is real enough for
someone else to act on.

---

## Known Canvas limitations

Not issues, because nothing here can be fixed from this side. Kept so that
someone hitting one can find out why in the repo rather than by experiment.

### Quiz "Save It Now" banner after a sync

Syncing a quiz that already has student submissions leaves Canvas showing an
"Unsaved Changes" banner. The tool cannot clear it.

**Why.** The Canvas REST API only regenerates `quiz_data` during a
`workflow_state` transition, and Canvas blocks unpublish and republish on a quiz
with submissions. The Canvas UI has a dedicated endpoint for this, but it
requires an SSO session, which an API token does not provide.

**What the tool does instead.** Detects the situation, updates the quiz in place,
and prints the URL so a human can click "Save It Now".
