"""End-to-end test: running sync a second time should succeed with no errors.

Depends on the canvas_course fixture which already ran the first sync.
"""

import os
import sys
import subprocess
import pytest

pytestmark = pytest.mark.canvas

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
E2E_CONTENT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "fixtures", "e2e_content",
)


def _get_course_id(request):
    """Get course ID from CLI flag or env var."""
    course_id = request.config.getoption("--course-id")
    if not course_id:
        course_id = os.environ.get("CANVAS_TEST_COURSE_ID")
    if not course_id:
        pytest.skip("No test course ID provided.")
    return course_id


def test_second_sync_succeeds(canvas_course, request):
    """Running sync again (without --force) should complete without errors.
    Smart sync should skip unchanged files.
    """
    course_id = _get_course_id(request)
    sync_script = os.path.join(PROJECT_ROOT, "sync_to_canvas.py")

    result = subprocess.run(
        [sys.executable, sync_script, E2E_CONTENT_DIR, "--course-id", course_id],
        capture_output=True,
        text=True,
        env={**os.environ},
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, f"Second sync failed:\n{result.stderr}"


def test_module_count_unchanged(canvas_course, request):
    """Module count should remain the same after a second sync."""
    modules_before = list(canvas_course.get_modules())
    count_before = len(modules_before)

    course_id = _get_course_id(request)
    sync_script = os.path.join(PROJECT_ROOT, "sync_to_canvas.py")

    result = subprocess.run(
        [sys.executable, sync_script, E2E_CONTENT_DIR, "--course-id", course_id],
        capture_output=True, text=True, env={**os.environ}, cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0

    modules_after = list(canvas_course.get_modules())
    assert len(modules_after) == count_before, (
        f"Module count changed: {count_before} -> {len(modules_after)}"
    )
