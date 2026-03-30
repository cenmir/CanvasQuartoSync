"""Tests for can_handle() detection logic across all handlers."""

import os
import json
from handlers.page_handler import PageHandler
from handlers.assignment_handler import AssignmentHandler
from handlers.quiz_handler import QuizHandler
from handlers.new_quiz_handler import NewQuizHandler
from handlers.subheader_handler import SubHeaderHandler
from handlers.external_link_handler import ExternalLinkHandler
from handlers.study_guide_handler import StudyGuideHandler
from handlers.calendar_handler import CalendarHandler


def _write(tmp_path, name, content):
    """Helper: write content to a file and return its path."""
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return str(p)


# --- PageHandler ---

class TestPageHandler:

    def test_accepts_page_qmd(self, tmp_path):
        path = _write(tmp_path, "01_Welcome.qmd", "---\ncanvas:\n  type: page\n---\nContent")
        assert PageHandler().can_handle(path) is True

    def test_rejects_assignment_qmd(self, tmp_path):
        path = _write(tmp_path, "02_HW.qmd", "---\ncanvas:\n  type: assignment\n---\nContent")
        assert PageHandler().can_handle(path) is False

    def test_rejects_non_qmd(self, tmp_path):
        path = _write(tmp_path, "file.json", '{"canvas": {"type": "page"}}')
        assert PageHandler().can_handle(path) is False

    def test_rejects_temp_file(self, tmp_path):
        path = _write(tmp_path, "_temp_page.qmd", "---\ncanvas:\n  type: page\n---\n")
        assert PageHandler().can_handle(path) is False

    def test_rejects_no_canvas_meta(self, tmp_path):
        path = _write(tmp_path, "01_Bare.qmd", "---\ntitle: Test\n---\nBody")
        assert PageHandler().can_handle(path) is False


# --- AssignmentHandler ---

class TestAssignmentHandler:

    def test_accepts_assignment(self, tmp_path):
        path = _write(tmp_path, "01_HW.qmd", "---\ncanvas:\n  type: assignment\n---\n")
        assert AssignmentHandler().can_handle(path) is True

    def test_rejects_page(self, tmp_path):
        path = _write(tmp_path, "01_P.qmd", "---\ncanvas:\n  type: page\n---\n")
        assert AssignmentHandler().can_handle(path) is False


# --- QuizHandler ---

class TestQuizHandler:

    def test_json_with_questions_key(self, tmp_path):
        data = {"questions": [{"question_name": "Q1"}]}
        path = _write(tmp_path, "quiz.json", json.dumps(data))
        assert QuizHandler().can_handle(path) is True

    def test_json_legacy_list_format(self, tmp_path):
        data = [{"question_name": "Q1", "answers": []}]
        path = _write(tmp_path, "quiz.json", json.dumps(data))
        assert QuizHandler().can_handle(path) is True

    def test_json_no_questions_rejected(self, tmp_path):
        data = {"title": "Not a quiz"}
        path = _write(tmp_path, "data.json", json.dumps(data))
        assert QuizHandler().can_handle(path) is False

    def test_qmd_frontmatter_type(self, tmp_path):
        path = _write(tmp_path, "quiz.qmd", "---\ncanvas:\n  type: quiz\n---\n")
        assert QuizHandler().can_handle(path) is True

    def test_qmd_structural_fallback(self, tmp_path):
        """Detects quiz by structural markers even without canvas.type."""
        content = "---\ncanvas:\n  title: Test\n---\n\n:::: {.question name=\"Q1\"}\nWhat?\n- [x] A\n::::\n"
        path = _write(tmp_path, "quiz.qmd", content)
        assert QuizHandler().can_handle(path) is True

    def test_qmd_no_markers_rejected(self, tmp_path):
        path = _write(tmp_path, "page.qmd", "---\ncanvas:\n  type: page\n---\nNo quiz here")
        assert QuizHandler().can_handle(path) is False


# --- NewQuizHandler ---

class TestNewQuizHandler:

    def test_qmd_new_quiz(self, tmp_path):
        path = _write(tmp_path, "nq.qmd", "---\ncanvas:\n  type: new_quiz\n---\n")
        assert NewQuizHandler().can_handle(path) is True

    def test_json_quiz_engine_new(self, tmp_path):
        data = {"canvas": {"quiz_engine": "new"}, "questions": []}
        path = _write(tmp_path, "nq.json", json.dumps(data))
        assert NewQuizHandler().can_handle(path) is True

    def test_json_without_engine_rejected(self, tmp_path):
        data = {"questions": [{"question_name": "Q1"}]}
        path = _write(tmp_path, "quiz.json", json.dumps(data))
        assert NewQuizHandler().can_handle(path) is False

    def test_qmd_classic_type_rejected(self, tmp_path):
        path = _write(tmp_path, "q.qmd", "---\ncanvas:\n  type: quiz\n---\n")
        assert NewQuizHandler().can_handle(path) is False


# --- SubHeaderHandler ---

class TestSubHeaderHandler:

    def test_accepts_qmd_subheader(self, tmp_path):
        path = _write(tmp_path, "sub.qmd", "---\ncanvas:\n  type: subheader\ntitle: Section\n---\n")
        assert SubHeaderHandler().can_handle(path) is True

    def test_accepts_md_subheader(self, tmp_path):
        path = _write(tmp_path, "sub.md", "---\ncanvas:\n  type: subheader\ntitle: Section\n---\n")
        assert SubHeaderHandler().can_handle(path) is True

    def test_rejects_non_subheader(self, tmp_path):
        path = _write(tmp_path, "page.qmd", "---\ncanvas:\n  type: page\n---\n")
        assert SubHeaderHandler().can_handle(path) is False


# --- ExternalLinkHandler ---

class TestExternalLinkHandler:

    def test_accepts_external_url(self, tmp_path):
        path = _write(tmp_path, "link.qmd", '---\ncanvas:\n  type: external_url\n  url: "https://example.com"\n---\n')
        assert ExternalLinkHandler().can_handle(path) is True

    def test_rejects_page(self, tmp_path):
        path = _write(tmp_path, "page.qmd", "---\ncanvas:\n  type: page\n---\n")
        assert ExternalLinkHandler().can_handle(path) is False

    def test_rejects_json(self, tmp_path):
        path = _write(tmp_path, "link.json", '{"canvas": {"type": "external_url"}}')
        assert ExternalLinkHandler().can_handle(path) is False


# --- StudyGuideHandler ---

class TestStudyGuideHandler:

    def test_by_filename_studyguide(self, tmp_path):
        path = _write(tmp_path, "09_StudyGuide.qmd", "---\ncanvas:\n  type: page\n---\n")
        assert StudyGuideHandler().can_handle(path) is True

    def test_by_filename_kurspm(self, tmp_path):
        path = _write(tmp_path, "01_KursPM.qmd", "---\ntitle: PM\n---\n")
        assert StudyGuideHandler().can_handle(path) is True

    def test_by_frontmatter(self, tmp_path):
        path = _write(tmp_path, "01_info.qmd", "---\ncanvas:\n  type: study_guide\n---\n")
        assert StudyGuideHandler().can_handle(path) is True

    def test_rejects_regular_page(self, tmp_path):
        path = _write(tmp_path, "01_Welcome.qmd", "---\ncanvas:\n  type: page\n---\n")
        assert StudyGuideHandler().can_handle(path) is False

    def test_rejects_temp_file(self, tmp_path):
        path = _write(tmp_path, "_temp_StudyGuide.qmd", "---\ncanvas:\n  type: study_guide\n---\n")
        assert StudyGuideHandler().can_handle(path) is False

    def test_rejects_tmp_prefix(self, tmp_path):
        path = _write(tmp_path, "tmp-StudyGuide.qmd", "---\ncanvas:\n  type: study_guide\n---\n")
        assert StudyGuideHandler().can_handle(path) is False


# --- CalendarHandler ---

class TestCalendarHandler:

    def test_accepts_schedule_yaml(self):
        assert CalendarHandler().can_handle("schedule.yaml") is True

    def test_accepts_path_with_schedule_yaml(self):
        assert CalendarHandler().can_handle("course/schedule.yaml") is True

    def test_rejects_other_yaml(self):
        assert CalendarHandler().can_handle("config.yaml") is False


# --- Handler Priority ---

class TestHandlerPriority:
    """StudyGuideHandler is registered before PageHandler in the handler chain.
    For files matching both (studyguide filename with type: page), StudyGuide wins."""

    def test_studyguide_filename_matches_both(self, tmp_path):
        path = _write(tmp_path, "09_StudyGuide.qmd", "---\ncanvas:\n  type: page\n---\n")
        assert StudyGuideHandler().can_handle(path) is True
        assert PageHandler().can_handle(path) is True
        # In the handler chain, StudyGuideHandler is listed first → it wins

    def test_new_quiz_before_classic(self, tmp_path):
        """NewQuizHandler is registered before QuizHandler.
        A file with type: new_quiz should only match NewQuizHandler."""
        path = _write(tmp_path, "q.qmd", "---\ncanvas:\n  type: new_quiz\n---\n")
        assert NewQuizHandler().can_handle(path) is True
        assert QuizHandler().can_handle(path) is False
