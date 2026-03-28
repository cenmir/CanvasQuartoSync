"""
E2E conftest.py — fixtures for real Canvas API testing.

These tests require:
  - CANVAS_API_URL and CANVAS_API_TOKEN environment variables
  - A test course ID via --course-id flag or CANVAS_TEST_COURSE_ID env var
  - Quarto CLI installed and in PATH

Run with:
  python -m pytest tests/e2e/ -v -m canvas --course-id 12345

All tests in this directory are marked with @pytest.mark.canvas.
"""

import os
import sys
import subprocess
import pytest

# Project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Dedicated test content (independent of Example/)
E2E_CONTENT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "fixtures", "e2e_content",
)


def _get_credentials(request):
    """Return (api_url, api_token, course_id) or skip."""
    api_url = os.environ.get("CANVAS_API_URL")
    api_token = os.environ.get("CANVAS_API_TOKEN")
    if not api_url or not api_token:
        pytest.skip("Canvas credentials not set (CANVAS_API_URL, CANVAS_API_TOKEN)")

    # Course ID: CLI flag > env var
    course_id = request.config.getoption("--course-id")
    if not course_id:
        course_id = os.environ.get("CANVAS_TEST_COURSE_ID")
    if not course_id:
        pytest.skip(
            "No test course ID provided. Use --course-id or set CANVAS_TEST_COURSE_ID env var."
        )

    return api_url, api_token, course_id


@pytest.fixture(scope="session")
def canvas_course(request):
    """Connect to real Canvas course. Purge existing content, then sync test content.

    Returns the canvasapi Course object for verification.
    """
    api_url, api_token, course_id = _get_credentials(request)

    from canvasapi import Canvas
    canvas = Canvas(api_url, api_token)
    course = canvas.get_course(course_id)

    # --- Purge the course ---
    for module in course.get_modules():
        module.delete()

    for page in course.get_pages():
        try:
            if getattr(page, "front_page", False):
                page.edit(wiki_page={"front_page": False})
            page.delete()
        except Exception:
            pass

    for assignment in course.get_assignments():
        assignment.delete()

    for quiz in course.get_quizzes():
        quiz.delete()

    # --- Sync test content ---
    sync_script = os.path.join(PROJECT_ROOT, "sync_to_canvas.py")

    result = subprocess.run(
        [sys.executable, sync_script, E2E_CONTENT_DIR, "--force", "--course-id", course_id],
        capture_output=True,
        text=True,
        env={**os.environ},
        cwd=PROJECT_ROOT,
    )

    if result.returncode != 0:
        pytest.fail(f"Sync failed (exit code {result.returncode}):\n{result.stderr}")

    return course


@pytest.fixture(scope="session")
def synced_modules(canvas_course):
    """Return dict of module_name -> module object."""
    modules = {}
    for m in canvas_course.get_modules():
        modules[m.name] = m
    return modules


@pytest.fixture(scope="session")
def synced_pages(canvas_course):
    """Return dict of page_title -> page object (with body loaded)."""
    pages = {}
    for p in canvas_course.get_pages():
        full = canvas_course.get_page(p.url)
        pages[full.title] = full
    return pages
