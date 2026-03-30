# Testing Guide

This project uses [pytest](https://docs.pytest.org/) for testing. Tests are organized into three tiers based on what external dependencies they require.

---

## Quick Start

```bash
# 1. Activate the virtual environment
.venv\Scripts\activate           # Windows
# source .venv/bin/activate      # macOS/Linux

# 2. Install test dependencies
uv pip install -r requirements-dev.txt

# 3. Run all unit tests (fast, no external deps)
python -m pytest tests/unit/ -v
```

---

## Test Tiers

### Tier 1: Unit Tests (`tests/unit/`)
**No external dependencies.** Tests pure logic functions like parsers, utilities, HTML transformations, and handler detection. These run on any machine without Canvas credentials or Quarto.

```bash
python -m pytest tests/unit/ -v
```

### Tier 2: Integration Tests (`tests/integration/`)
**Mocked Canvas API.** Tests multi-component interactions (module management, content processing, cross-link resolution) using `unittest.mock` to simulate Canvas API responses. No network calls.

```bash
python -m pytest tests/integration/ -v
```

### Tier 3: End-to-End Tests (`tests/e2e/`)
**Requires real Canvas course + Quarto CLI.** Syncs dedicated test content (`tests/fixtures/e2e_content/`) to a real Canvas test course, then downloads and verifies the results. Each developer uses their own test course.

```bash
# Set credentials
export CANVAS_API_URL="https://your-institution.instructure.com"
export CANVAS_API_TOKEN="your-token"

# Run E2E tests — pass YOUR test course ID
python -m pytest tests/e2e/ -v -m canvas --course-id 12345

# Or set it as an environment variable
export CANVAS_TEST_COURSE_ID="12345"
python -m pytest tests/e2e/ -v -m canvas
```

---

## Running Tests

| Command | What it runs |
|---------|-------------|
| `python -m pytest tests/unit/ -v` | All unit tests |
| `python -m pytest tests/integration/ -v` | All integration tests |
| `python -m pytest tests/ -v -m "not canvas"` | Everything except E2E |
| `python -m pytest tests/e2e/ -v -m canvas --course-id 12345` | E2E tests (needs credentials + course ID) |
| `python -m pytest tests/unit/test_qmd_quiz_parser.py -v` | One specific test file |
| `python -m pytest tests/unit/test_qmd_quiz_parser.py::TestChecklistAnswers::test_basic -v` | One specific test |
| `python -m pytest tests/unit/ -v -s` | Unit tests with print output visible |

---

## Test Structure

```
tests/
    conftest.py                     # Shared fixtures, global state cleanup
    unit/                           # Pure logic tests
        test_content_utils.py       # parse_module_name, clean_title, sync map, safe_delete
        test_is_valid_name.py       # NN_ prefix validation
        test_qmd_quiz_parser.py     # QMD quiz format parsing (checklist, div, formula)
        test_handler_detection.py   # can_handle() for all 8 handlers
        test_new_quiz_transform.py  # New Quizzes API question transformation
        test_formula_solutions.py   # Formula evaluation with asteval
        test_callout_styles.py      # Callout + syntax highlighting inlining
        test_log_formatter.py       # Rich markup stripping
        test_drift_detector.py      # HTML normalization and hashing
        test_qmd_preprocessor.py    # Study guide preprocessing
        test_config.py              # Config resolution priority
    integration/                    # Mocked Canvas API tests
        test_add_to_module.py       # Module item create/update/match logic
        test_process_content.py     # Image/link processing with mocked uploads
    e2e/                            # Real Canvas course tests
        conftest.py                 # Course setup/teardown fixtures
        test_full_sync.py           # Verify modules, pages, quizzes, images, etc.
        test_idempotency.py         # Second sync produces same result
    fixtures/
        e2e_content/                # Dedicated test content for E2E tests
            _quarto.yml             # Quarto config (HTML + PDF)
            config.toml             # Course metadata for preprocessor
            branding.css            # Callout & brand styling
            schedule.yaml           # Calendar events
            graphics/               # Test image
            01_Introduction/        # Page, callouts, subheader, external links, quizzes
            02_Basics/              # Upload + text entry assignments
            03_Advanced/            # New Quizzes (MC, numeric, formula, JSON)
            04_Course Documents/    # Study guide with preprocessing + PDF
```

---

## Writing a New Test

Tests follow the **Arrange / Act / Assert** pattern:

```python
# tests/unit/test_example.py

from handlers.content_utils import parse_module_name

def test_strips_two_digit_prefix():
    # Arrange: set up test data
    input_name = "03_Advanced_Topics"

    # Act: call the function under test
    result = parse_module_name(input_name)

    # Assert: verify the expected outcome
    assert result == "Advanced_Topics"
```

### Tips for writing tests:
- **Name tests descriptively**: `test_rejects_single_digit_prefix` is better than `test_case_2`
- **One assertion per concept**: Test one behavior at a time
- **Use `tmp_path`**: pytest's built-in fixture for temporary directories (auto-cleaned)
- **Use `monkeypatch`**: pytest's built-in fixture for setting environment variables
- **Group related tests in classes**: `class TestParseModuleName:` keeps things organized

---

## E2E Test Setup

1. Create a **dedicated test course** in Canvas (do not use a production course)
2. Set environment variables:
   - `CANVAS_API_URL` — your institution's Canvas URL
   - `CANVAS_API_TOKEN` — your API access token
3. Pass your course ID when running tests:
   - CLI flag: `--course-id 12345`
   - Or env var: `CANVAS_TEST_COURSE_ID=12345`
4. The E2E tests will **purge the course** before syncing, so ensure the course is disposable

The E2E tests sync content from `tests/fixtures/e2e_content/` (not `Example/`), so test results are stable and independent of your project's example content.

---

## Adding Test Fixtures

Static test data goes in `tests/fixtures/`. Reference it via the `fixtures_dir` fixture:

```python
def test_something(fixtures_dir):
    path = os.path.join(fixtures_dir, "sample_page.qmd")
    # Use the fixture file...
```

---

## CI / GitHub Actions

Unit tests can run in CI without any secrets:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: python -m pytest tests/unit/ tests/integration/ -v
```

E2E tests require Canvas secrets and should only run on protected branches.
