"""End-to-end tests for drift detection.

Runs after the full sync (canvas_course fixture).

The point of these tests is that drift detection compares two things that must
be the same kind of thing. Canvas rewrites HTML on save: it absolutizes
course-relative links, injects <tbody> into tables, normalizes void tags, and
may prepend account theme CSS. So the body we PUT is never the body Canvas
serves back, and a baseline taken from the HTML we sent can never match.

Before the fix, test_no_drift_immediately_after_sync failed on a freshly synced
course that nobody had touched. There is no point in a drift check that always
fires, so that test is the regression guard for this whole feature.
"""

import pytest

from handlers.drift_detector import check_all_drift
from tests.e2e.canvas_helpers import run_sync
from tests.e2e.conftest import E2E_CONTENT_DIR

pytestmark = pytest.mark.canvas


def _drifted(course):
    """Return {file: item} for everything currently reported as drifted."""
    return {item["file"]: item for item in check_all_drift(course, E2E_CONTENT_DIR)}


class TestNoFalsePositives:
    """A course nobody has touched must report clean."""

    def test_no_drift_immediately_after_sync(self, canvas_course):
        drifted = _drifted(canvas_course)
        assert not drifted, (
            "Drift reported on a freshly synced course. The stored baseline is "
            "not what Canvas serves back:\n  "
            + "\n  ".join(drifted)
        )

    def test_no_drift_after_a_second_sync(self, canvas_course, e2e_credentials):
        result = run_sync(
            E2E_CONTENT_DIR,
            e2e_credentials["course_id"],
            e2e_credentials["api_url"],
            e2e_credentials["api_token"],
        )
        assert result.returncode == 0, f"Second sync failed:\n{result.stderr}"

        drifted = _drifted(canvas_course)
        assert not drifted, f"Drift reported after an unchanged re-sync: {list(drifted)}"

    def test_no_drift_on_a_repeated_check(self, canvas_course):
        """Two checks in a row must agree.

        Catches baselines that depend on something volatile in the fetched
        HTML, such as a per-request file verifier token.
        """
        first = _drifted(canvas_course)
        second = _drifted(canvas_course)
        assert set(first) == set(second), (
            f"Drift check is not stable across calls: {set(first) ^ set(second)}"
        )


class TestTruePositives:
    """A real Canvas-side edit must be detected."""

    def test_canvas_edit_is_detected_and_diffed(self, canvas_course, synced_pages, e2e_credentials):
        title = next(t for t in synced_pages if "Welcome" in t)
        page = canvas_course.get_page(synced_pages[title].url)
        original = page.body or ""
        marker = "DRIFT PROBE: edited in the Canvas UI"

        page.edit(wiki_page={"body": original + f"<p>{marker}</p>"})
        try:
            drifted = _drifted(canvas_course)
            assert drifted, "A Canvas-side edit was not detected"

            entry = next(
                (v for k, v in drifted.items() if "Welcome" in v.get("title", "") or "Welcome" in k),
                None,
            )
            assert entry is not None, f"Edited page not among drifted items: {list(drifted)}"
            assert marker in (entry.get("diff") or ""), (
                "Drift was reported but the diff does not show what changed"
            )
        finally:
            # Re-sync restores the page and the baseline for later tests.
            run_sync(
                E2E_CONTENT_DIR,
                e2e_credentials["course_id"],
                e2e_credentials["api_url"],
                e2e_credentials["api_token"],
                "--force",
            )

    def test_drift_clears_after_resync(self, canvas_course):
        assert not _drifted(canvas_course), (
            "Drift still reported after the restoring re-sync"
        )
