"""Tests for handlers/drift_detector.py — HTML normalization and hashing."""

from handlers.drift_detector import _normalize_html, compute_content_hash, _html_to_text


# --- _normalize_html ---

class TestNormalizeHtml:

    def test_removes_data_attrs(self):
        html = '<div data-api-endpoint="/api/v1/pages/123">text</div>'
        result = _normalize_html(html)
        assert "data-api-endpoint" not in result

    def test_removes_class(self):
        html = '<p class="some-canvas-class">text</p>'
        result = _normalize_html(html)
        assert "class=" not in result

    def test_removes_style(self):
        html = '<span style="color: red;">text</span>'
        result = _normalize_html(html)
        assert "style=" not in result

    def test_normalizes_whitespace(self):
        html = "<p>  hello   world  </p>"
        result = _normalize_html(html)
        assert "  " not in result  # No double spaces

    def test_empty_string(self):
        assert _normalize_html("") == ""

    def test_none_input(self):
        assert _normalize_html(None) == ""

    def test_preserves_content(self):
        html = "<p>Hello World</p>"
        result = _normalize_html(html)
        assert "Hello World" in result


# --- compute_content_hash ---

class TestComputeContentHash:

    def test_same_content_same_hash(self):
        h1 = compute_content_hash("<p>hello</p>")
        h2 = compute_content_hash("<p>hello</p>")
        assert h1 == h2

    def test_different_content_different_hash(self):
        h1 = compute_content_hash("<p>hello</p>")
        h2 = compute_content_hash("<p>world</p>")
        assert h1 != h2

    def test_whitespace_insensitive(self):
        h1 = compute_content_hash("<p>hello   world</p>")
        h2 = compute_content_hash("<p>hello world</p>")
        assert h1 == h2

    def test_class_attrs_ignored(self):
        h1 = compute_content_hash('<p class="foo">text</p>')
        h2 = compute_content_hash("<p>text</p>")
        assert h1 == h2

    def test_hash_is_hex_string(self):
        h = compute_content_hash("<p>test</p>")
        assert len(h) == 16
        assert all(c in "0123456789abcdef" for c in h)


# --- _html_to_text ---

class TestHtmlToText:

    def test_strips_tags(self):
        html = "<strong>bold</strong> and <em>italic</em>"
        text = _html_to_text(html)
        assert text == "bold and italic"

    def test_block_elements_add_newlines(self):
        html = "<p>Hello</p><p>World</p>"
        text = _html_to_text(html)
        assert "Hello" in text
        assert "World" in text

    def test_empty_string(self):
        assert _html_to_text("") == ""

    def test_none_input(self):
        assert _html_to_text(None) == ""

    def test_html_entities_decoded(self):
        html = "5 &gt; 3 &amp; 2 &lt; 4"
        text = _html_to_text(html)
        assert "5 > 3 & 2 < 4" in text

    def test_list_items(self):
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        text = _html_to_text(html)
        assert "Item 1" in text
        assert "Item 2" in text
