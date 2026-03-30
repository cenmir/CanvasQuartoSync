"""Tests for handlers/qmd_quiz_parser.py — QMD quiz format parsing."""

from handlers.qmd_quiz_parser import (
    parse_qmd_quiz,
    _extract_frontmatter,
    _parse_attributes,
    _strip_indent,
    _clean_question_text,
)


# --- Frontmatter extraction ---

class TestExtractFrontmatter:

    def test_basic_frontmatter(self):
        content = "---\ncanvas:\n  title: Test Quiz\n  quiz_type: practice_quiz\n---\nbody text"
        meta, body = _extract_frontmatter(content)
        assert meta["title"] == "Test Quiz"
        assert meta["quiz_type"] == "practice_quiz"
        assert body == "body text"

    def test_no_frontmatter(self):
        meta, body = _extract_frontmatter("just body text")
        assert meta == {}
        assert body == "just body text"

    def test_empty_frontmatter(self):
        content = "---\n---\nbody"
        meta, body = _extract_frontmatter(content)
        assert meta == {}

    def test_malformed_yaml(self):
        content = "---\n: : invalid\n---\nbody"
        meta, body = _extract_frontmatter(content)
        # Should not crash, returns empty
        assert isinstance(meta, dict)


# --- Attribute parsing ---

class TestParseAttributes:

    def test_quoted_name(self):
        attrs = _parse_attributes('name="My Question" points=2')
        assert attrs["name"] == "My Question"
        assert attrs["points"] == 2

    def test_unquoted_value(self):
        attrs = _parse_attributes("type=essay_question")
        assert attrs["type"] == "essay_question"

    def test_numeric_conversion(self):
        attrs = _parse_attributes("points=5")
        assert attrs["points"] == 5
        assert isinstance(attrs["points"], int)

    def test_float_conversion(self):
        attrs = _parse_attributes("points=2.5")
        assert attrs["points"] == 2.5

    def test_empty_string(self):
        attrs = _parse_attributes("")
        assert attrs == {}

    def test_unicode_in_name(self):
        attrs = _parse_attributes('name="Spänning"')
        assert attrs["name"] == "Spänning"


# --- Utility functions ---

class TestStripIndent:

    def test_removes_common_indent(self):
        text = "    line1\n    line2"
        assert _strip_indent(text) == "line1\nline2"

    def test_preserves_relative_indent(self):
        text = "    line1\n        line2"
        assert _strip_indent(text) == "line1\n    line2"

    def test_no_indent(self):
        text = "line1\nline2"
        assert _strip_indent(text) == "line1\nline2"

    def test_empty_lines_ignored(self):
        text = "    line1\n\n    line2"
        result = _strip_indent(text)
        assert result == "line1\n\nline2"


class TestCleanQuestionText:

    def test_strips_blank_lines(self):
        text = "\n\n  Hello  \n\n"
        result = _clean_question_text(text)
        assert result == "  Hello  "

    def test_preserves_inner_blank_lines(self):
        text = "Line 1\n\nLine 2"
        result = _clean_question_text(text)
        assert result == "Line 1\n\nLine 2"


# --- Full parse: checklist answers ---

class TestChecklistAnswers:

    def test_basic(self):
        content = """---
canvas:
  title: "Test"
---

:::: {.question name="Q1"}

What is 2+2?

- [x] 4
- [ ] 3
- [ ] 5

::::
"""
        meta, questions = parse_qmd_quiz(content)
        assert len(questions) == 1
        q = questions[0]
        assert q["question_name"] == "Q1"
        assert len(q["answers"]) == 3
        assert q["answers"][0]["answer_weight"] == 100
        assert q["answers"][0]["answer_text"] == "4"
        assert q["answers"][1]["answer_weight"] == 0
        assert q["answers"][2]["answer_weight"] == 0

    def test_with_comments(self):
        content = """---
canvas:
  title: "Test"
---

:::: {.question name="Q1"}

Question?

- [x] Right
  - Good job!
- [ ] Wrong
  - Try again.

::::
"""
        meta, questions = parse_qmd_quiz(content)
        q = questions[0]
        assert q["answers"][0]["answer_comments"] == "Good job!"
        assert q["answers"][1]["answer_comments"] == "Try again."

    def test_uppercase_x(self):
        content = """---
canvas:
  title: "Test"
---

:::: {.question name="Q1"}

Question?

- [X] Correct
- [ ] Wrong

::::
"""
        _, questions = parse_qmd_quiz(content)
        assert questions[0]["answers"][0]["answer_weight"] == 100


# --- Full parse: div answers ---

class TestDivAnswers:

    def test_basic(self):
        content = """---
canvas:
  title: "Test"
---

:::: {.question name="Rich" points=2}

What is E?

::: {.answer correct=true comment="Correct!"}
Young's modulus
:::

::: {.answer comment="No."}
Strain
:::

::::
"""
        meta, questions = parse_qmd_quiz(content)
        assert len(questions) == 1
        q = questions[0]
        assert q["points_possible"] == 2
        assert q["answers"][0]["answer_weight"] == 100
        assert q["answers"][0]["answer_comments"] == "Correct!"
        assert "Young's modulus" in q["answers"][0]["answer_html"]
        assert q["answers"][1]["answer_weight"] == 0

    def test_correct_class_in_attrs_string(self):
        """Test that '.correct' in the attrs_str is recognized."""
        content = """---
canvas:
  title: "Test"
---

:::: {.question name="Q1"}

Q?

::: {.answer .correct}
Right
:::

::::
"""
        _, questions = parse_qmd_quiz(content)
        assert questions[0]["answers"][0]["answer_weight"] == 100


# --- Comment divs ---

class TestCommentDivs:

    def test_correct_and_incorrect_comments(self):
        content = """---
canvas:
  title: "Test"
---

:::: {.question name="Q1"}

Question?

- [x] Right
- [ ] Wrong

::: correct-comment
Well done!
:::

::: incorrect-comment
Review section 2.
:::

::::
"""
        _, questions = parse_qmd_quiz(content)
        q = questions[0]
        assert q["correct_comments"] == "Well done!"
        assert q["incorrect_comments"] == "Review section 2."


# --- Formula question ---

class TestFormulaQuestion:

    def test_formula_with_variables(self):
        content = """---
canvas:
  type: new_quiz
---

:::: {.question type="formula_question" name="Stress"}

Calculate stress when Area = [A] mm2 and Force = [F] kN.

::: {.formula}
formula: F * 1000 / A
margin: 2
margin_type: percent
answer_count: 5
:::

::: {.variable name="F"}
min: 10
max: 100
precision: 0
:::

::: {.variable name="A"}
min: 50
max: 500
precision: 0
:::

::::
"""
        meta, questions = parse_qmd_quiz(content)
        assert len(questions) == 1
        q = questions[0]
        assert q["question_type"] == "formula_question"
        assert q["formula"] == "F * 1000 / A"
        assert q["margin"] == 2
        assert len(q["variables"]) == 2
        assert q["variables"][0]["name"] == "F"
        assert q["variables"][1]["name"] == "A"
        assert "Calculate stress" in q["question_text"]


# --- Multiple questions ---

class TestMultipleQuestions:

    def test_two_questions(self):
        content = """---
canvas:
  title: "Multi"
---

:::: {.question name="Q1"}
Question 1?
- [x] A
- [ ] B
::::

:::: {.question name="Q2"}
Question 2?
- [ ] C
- [x] D
::::
"""
        _, questions = parse_qmd_quiz(content)
        assert len(questions) == 2
        assert questions[0]["question_name"] == "Q1"
        assert questions[1]["question_name"] == "Q2"


# --- Edge cases ---

class TestEdgeCases:

    def test_question_with_latex(self):
        content = r"""---
canvas:
  title: "Test"
---

:::: {.question name="LaTeX"}

What is $\sigma = F/A$?

- [x] Stress formula
- [ ] Strain formula

::::
"""
        _, questions = parse_qmd_quiz(content)
        assert r"$\sigma = F/A$" in questions[0]["question_text"]

    def test_default_question_name(self):
        """Question without a name attribute gets auto-generated name."""
        content = """---
canvas:
  title: "Test"
---

:::: {.question}
Q?
- [x] A
::::
"""
        _, questions = parse_qmd_quiz(content)
        assert questions[0]["question_name"].startswith("Fråga")

    def test_default_question_type(self):
        """Question without type defaults to multiple_choice_question."""
        content = """---
canvas:
  title: "Test"
---

:::: {.question name="Q1"}
Q?
- [x] A
::::
"""
        _, questions = parse_qmd_quiz(content)
        assert questions[0]["question_type"] == "multiple_choice_question"

    def test_no_answers(self):
        """Question with text but no checklist or div answers."""
        content = """---
canvas:
  title: "Test"
---

:::: {.question name="Empty"}
Just some text here.
::::
"""
        _, questions = parse_qmd_quiz(content)
        assert len(questions) == 1
        assert questions[0]["answers"] == []
        assert "Just some text" in questions[0]["question_text"]

    def test_custom_points(self):
        content = """---
canvas:
  title: "Test"
---

:::: {.question name="Q1" points=5}
Q?
- [x] A
::::
"""
        _, questions = parse_qmd_quiz(content)
        assert questions[0]["points_possible"] == 5

    def test_quiz_metadata_preserved(self):
        content = """---
canvas:
  title: "My Quiz"
  quiz_type: assignment
  time_limit: 30
  shuffle_answers: true
  show_correct_answers: false
---

:::: {.question name="Q1"}
Q?
- [x] A
::::
"""
        meta, _ = parse_qmd_quiz(content)
        assert meta["title"] == "My Quiz"
        assert meta["quiz_type"] == "assignment"
        assert meta["time_limit"] == 30
        assert meta["shuffle_answers"] is True
        assert meta["show_correct_answers"] is False
