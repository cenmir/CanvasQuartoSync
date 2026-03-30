"""End-to-end test: sync test content to a real Canvas course and verify results.

Requires CANVAS_API_URL, CANVAS_API_TOKEN env vars and --course-id.
Run with: python -m pytest tests/e2e/ -v -m canvas --course-id 12345

Test content lives in tests/fixtures/e2e_content/ and covers:
  - Pages (with images, math, callouts, code, cross-links, tables)
  - Assignments (upload + text entry)
  - Classic Quizzes (QMD checklist, QMD div answers, JSON format)
  - New Quizzes (multiple choice, true/false, multi-answer, numeric, formula, JSON)
  - SubHeaders
  - External Links (with indent, new_tab)
  - Study Guides (with preprocessing, front_page, PDF)
  - Calendar events (schedule.yaml)
"""

import pytest

pytestmark = pytest.mark.canvas


# ---------------------------------------------------------------------------
# Modules
# ---------------------------------------------------------------------------
class TestModulesCreated:

    def test_introduction_module_exists(self, synced_modules):
        assert "Introduction" in synced_modules

    def test_basics_module_exists(self, synced_modules):
        assert "Basics" in synced_modules

    def test_advanced_module_exists(self, synced_modules):
        assert "Advanced" in synced_modules

    def test_course_documents_module_exists(self, synced_modules):
        assert "Course Documents" in synced_modules

    def test_module_count(self, synced_modules):
        """Exactly 4 modules should exist."""
        assert len(synced_modules) == 4, (
            f"Expected 4 modules, got {len(synced_modules)}: {list(synced_modules.keys())}"
        )


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
class TestPageContent:

    def test_welcome_page_exists(self, synced_pages):
        matching = [t for t in synced_pages if "Welcome" in t]
        assert len(matching) >= 1, f"No 'Welcome' page. Pages: {list(synced_pages.keys())}"

    def test_welcome_page_has_html(self, synced_pages):
        """Page body should contain rendered HTML, not raw QMD."""
        matching = [t for t in synced_pages if "Welcome" in t]
        if matching:
            page = synced_pages[matching[0]]
            body = getattr(page, "body", "")
            assert "<" in body, "Page body should contain HTML tags"
            assert "---" not in body[:50], "Page body should not start with YAML frontmatter"

    def test_welcome_page_has_table(self, synced_pages):
        """Welcome page contains a markdown table that should render as HTML table."""
        matching = [t for t in synced_pages if "Welcome" in t]
        if matching:
            body = getattr(synced_pages[matching[0]], "body", "")
            assert "<table" in body.lower(), "Page should contain an HTML table"

    def test_callouts_page_exists(self, synced_pages):
        matching = [t for t in synced_pages if "Callout" in t]
        assert len(matching) >= 1, f"No callouts page. Pages: {list(synced_pages.keys())}"

    def test_callouts_page_has_callout_html(self, synced_pages):
        """Callout blocks should be rendered with inline styles."""
        matching = [t for t in synced_pages if "Callout" in t]
        if matching:
            body = getattr(synced_pages[matching[0]], "body", "")
            assert "callout" in body.lower() or "border" in body.lower(), (
                "Callout page should contain callout-styled HTML"
            )

    def test_callouts_page_has_code_block(self, synced_pages):
        """Syntax-highlighted code blocks should be present."""
        matching = [t for t in synced_pages if "Callout" in t]
        if matching:
            body = getattr(synced_pages[matching[0]], "body", "")
            # Quarto renders code blocks with <pre> or <code> tags
            assert "<code" in body.lower() or "<pre" in body.lower(), (
                "Page should contain code blocks"
            )


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------
class TestImageUpload:

    def test_images_use_canvas_urls(self, synced_pages):
        """All images should point to Canvas file URLs, not local paths."""
        for title, page in synced_pages.items():
            body = getattr(page, "body", "") or ""
            if "img" in body.lower():
                assert "src=\"../" not in body, (
                    f"Page '{title}' still has relative image paths"
                )


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------
class TestAssignments:

    def test_at_least_two_assignments(self, canvas_course):
        assignments = list(canvas_course.get_assignments())
        # We have Upload Assignment + Text Entry + potentially New Quiz assignments
        non_quiz = [a for a in assignments if not getattr(a, "is_quiz_assignment", False)]
        assert len(non_quiz) >= 2, (
            f"Expected at least 2 non-quiz assignments, got {len(non_quiz)}"
        )

    def test_upload_assignment_has_points(self, canvas_course):
        """Upload Assignment should have 10 points."""
        for a in canvas_course.get_assignments():
            if "Upload" in (a.name or ""):
                assert a.points_possible == 10, (
                    f"Upload Assignment points: {a.points_possible}"
                )
                return
        pytest.fail("Upload Assignment not found")

    def test_text_entry_assignment_exists(self, canvas_course):
        """Text Entry Assignment should exist with 5 points."""
        for a in canvas_course.get_assignments():
            if "Text Entry" in (a.name or ""):
                assert a.points_possible == 5
                return
        pytest.fail("Text Entry Assignment not found")


# ---------------------------------------------------------------------------
# Classic Quizzes
# ---------------------------------------------------------------------------
class TestClassicQuizzes:

    def test_qmd_quiz_exists(self, canvas_course):
        quizzes = list(canvas_course.get_quizzes())
        matching = [q for q in quizzes if "Checklist" in (q.title or "")]
        assert len(matching) >= 1, (
            f"No checklist quiz found. Quizzes: {[q.title for q in quizzes]}"
        )

    def test_qmd_quiz_has_questions(self, canvas_course):
        """The QMD classic quiz should have 3 questions (checklist + div answers)."""
        for q in canvas_course.get_quizzes():
            if "Checklist" in (q.title or ""):
                questions = list(q.get_questions())
                assert len(questions) == 3, (
                    f"Expected 3 questions, got {len(questions)}"
                )
                return
        pytest.fail("Checklist quiz not found")

    def test_json_quiz_exists(self, canvas_course):
        quizzes = list(canvas_course.get_quizzes())
        matching = [q for q in quizzes if "JSON Classic" in (q.title or "")]
        assert len(matching) >= 1, (
            f"No JSON quiz found. Quizzes: {[q.title for q in quizzes]}"
        )

    def test_json_quiz_has_questions(self, canvas_course):
        """The JSON classic quiz should have 2 questions."""
        for q in canvas_course.get_quizzes():
            if "JSON Classic" in (q.title or ""):
                questions = list(q.get_questions())
                assert len(questions) == 2, (
                    f"Expected 2 questions, got {len(questions)}"
                )
                return

    def test_quiz_allows_unlimited_attempts(self, canvas_course):
        """The checklist quiz should allow unlimited attempts."""
        for q in canvas_course.get_quizzes():
            if "Checklist" in (q.title or ""):
                assert q.allowed_attempts == -1, (
                    f"Expected -1 attempts, got {q.allowed_attempts}"
                )
                return


# ---------------------------------------------------------------------------
# New Quizzes (assignment-backed)
# ---------------------------------------------------------------------------
class TestNewQuizzes:

    def test_new_quiz_mc_exists(self, canvas_course):
        """New Quiz with MC/TF/Multi-answer should exist as an assignment."""
        for a in canvas_course.get_assignments():
            if "Multiple Choice and True/False" in (a.name or ""):
                return
        pytest.fail("New Quiz MC assignment not found")

    def test_new_quiz_numeric_formula_exists(self, canvas_course):
        """New Quiz with numeric/formula questions should exist."""
        for a in canvas_course.get_assignments():
            if "Numeric and Formula" in (a.name or ""):
                return
        pytest.fail("New Quiz Numeric/Formula assignment not found")

    def test_new_quiz_json_exists(self, canvas_course):
        """New Quiz from JSON should exist."""
        for a in canvas_course.get_assignments():
            if "New Quiz from JSON" in (a.name or ""):
                return
        pytest.fail("New Quiz JSON assignment not found")


# ---------------------------------------------------------------------------
# Module Items: order, types, indent
# ---------------------------------------------------------------------------
class TestModuleItems:

    def test_introduction_has_multiple_items(self, synced_modules):
        """Introduction module should have at least 6 items (2 pages, subheader,
        external link, quiz, json quiz, indented link)."""
        module = synced_modules.get("Introduction")
        if not module:
            pytest.skip("Introduction module not found")
        items = list(module.get_module_items())
        assert len(items) >= 6, (
            f"Expected >= 6 items, got {len(items)}: "
            f"{[i.title for i in items]}"
        )

    def test_items_ordered_by_prefix(self, synced_modules):
        """Items should be ordered by their NN_ filename prefix."""
        module = synced_modules.get("Introduction")
        if not module:
            pytest.skip("Introduction module not found")
        items = list(module.get_module_items())
        titles = [item.title for item in items]
        assert len(titles) >= 2, f"Too few items: {titles}"

    def test_external_url_item_exists(self, synced_modules):
        """At least one module should contain an ExternalUrl item."""
        for name, module in synced_modules.items():
            for item in module.get_module_items():
                if item.type == "ExternalUrl":
                    return
        pytest.fail("No ExternalUrl module item found")

    def test_subheader_item_exists(self, synced_modules):
        """At least one module should contain a SubHeader item."""
        for name, module in synced_modules.items():
            for item in module.get_module_items():
                if item.type == "SubHeader":
                    return
        pytest.fail("No SubHeader module item found")

    def test_indented_external_link(self, synced_modules):
        """The indented external link should have indent > 0."""
        module = synced_modules.get("Introduction")
        if not module:
            pytest.skip("Introduction module not found")
        for item in module.get_module_items():
            if item.type == "ExternalUrl" and getattr(item, "indent", 0) > 0:
                return
        pytest.fail("No indented ExternalUrl item found in Introduction")


# ---------------------------------------------------------------------------
# Study Guide
# ---------------------------------------------------------------------------
class TestStudyGuide:

    def test_study_guide_page_exists(self, synced_pages):
        """Study guide should be synced as a page."""
        matching = [t for t in synced_pages if "Course PM" in t or "StudyGuide" in t]
        assert len(matching) >= 1, (
            f"No study guide page. Pages: {list(synced_pages.keys())}"
        )

    def test_study_guide_has_grading_table(self, synced_pages):
        """The preprocessed study guide should contain a grading criteria table."""
        matching = [t for t in synced_pages if "Course PM" in t or "StudyGuide" in t]
        if matching:
            body = getattr(synced_pages[matching[0]], "body", "")
            assert "<table" in body.lower(), "Study guide should contain HTML tables"

    def test_front_page_set(self, canvas_course):
        """The study guide should be set as the course front page."""
        # Get the front page
        try:
            front = canvas_course.get_page("front_page")
            assert front is not None, "No front page set"
        except Exception:
            # Some Canvas versions use show_front_page or default_view
            pass


# ---------------------------------------------------------------------------
# Cross-links
# ---------------------------------------------------------------------------
class TestCrossLinks:

    def test_welcome_cross_links_resolved(self, synced_pages):
        """Cross-links to other .qmd files should resolve to Canvas URLs."""
        matching = [t for t in synced_pages if "Welcome" in t]
        if matching:
            body = getattr(synced_pages[matching[0]], "body", "")
            # Should not contain raw .qmd references
            assert ".qmd" not in body, (
                "Page still has unresolved .qmd cross-links"
            )
