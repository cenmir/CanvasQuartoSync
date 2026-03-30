"""Tests for process_content() with mocked file upload and cross-link resolution."""

import os
from unittest.mock import patch, MagicMock
from handlers.content_utils import process_content


@patch("handlers.content_utils.upload_file")
@patch("handlers.content_utils.resolve_cross_link")
def test_local_image_uploaded(mock_resolve, mock_upload):
    """Local images trigger upload_file and get replaced with Canvas URL."""
    mock_upload.return_value = ("https://canvas.com/files/123/img.jpg", 123)
    mock_course = MagicMock()

    content = "![Alt](image.jpg)"
    result = process_content(content, "/base", mock_course)
    mock_upload.assert_called_once()
    assert "https://canvas.com/files/123/img.jpg" in result


@patch("handlers.content_utils.upload_file")
def test_http_images_not_uploaded(mock_upload):
    """HTTP/HTTPS images are left as-is."""
    mock_course = MagicMock()
    content = "![Alt](https://example.com/img.jpg)"
    result = process_content(content, "/base", mock_course)
    mock_upload.assert_not_called()
    assert "https://example.com/img.jpg" in result


@patch("handlers.content_utils.upload_file")
def test_data_uri_images_not_uploaded(mock_upload):
    """Data URI images are left as-is."""
    mock_course = MagicMock()
    content = "![Alt](data:image/png;base64,iVBOR)"
    result = process_content(content, "/base", mock_course)
    mock_upload.assert_not_called()


@patch("handlers.content_utils.upload_file")
@patch("handlers.content_utils.resolve_cross_link")
def test_code_blocks_protected(mock_resolve, mock_upload):
    """Content inside fenced code blocks is not processed."""
    mock_course = MagicMock()
    content = "```\n![Alt](image.jpg)\n[link](page.qmd)\n```"
    result = process_content(content, "/base", mock_course)
    mock_upload.assert_not_called()
    mock_resolve.assert_not_called()
    assert "![Alt](image.jpg)" in result


@patch("handlers.content_utils.upload_file")
@patch("handlers.content_utils.resolve_cross_link")
def test_hash_links_not_processed(mock_resolve, mock_upload):
    """Anchor links (#heading) are left as-is."""
    mock_course = MagicMock()
    content = "[Section](#heading)"
    result = process_content(content, "/base", mock_course)
    mock_upload.assert_not_called()
    mock_resolve.assert_not_called()
    assert "[Section](#heading)" in result


@patch("handlers.content_utils.upload_file")
@patch("handlers.content_utils.resolve_cross_link")
def test_mailto_links_not_processed(mock_resolve, mock_upload):
    mock_course = MagicMock()
    content = "[Email](mailto:test@example.com)"
    result = process_content(content, "/base", mock_course)
    mock_upload.assert_not_called()
    assert "mailto:test@example.com" in result


@patch("handlers.content_utils.upload_file")
@patch("handlers.content_utils.resolve_cross_link")
def test_qmd_link_calls_cross_link(mock_resolve, mock_upload):
    """Links to .qmd files trigger resolve_cross_link."""
    mock_resolve.return_value = "https://canvas.com/courses/1/pages/my-page"
    mock_course = MagicMock()

    content = "[Next Page](../02_Module/01_Page.qmd)"
    result = process_content(content, "/base", mock_course)
    mock_resolve.assert_called_once()
    assert "https://canvas.com/courses/1/pages/my-page" in result


@patch("handlers.content_utils.upload_file")
@patch("handlers.content_utils.resolve_cross_link")
def test_qmd_link_falls_through_to_upload(mock_resolve, mock_upload):
    """When resolve_cross_link returns None (no canvas metadata), fall through to file upload."""
    mock_resolve.return_value = None
    mock_upload.return_value = ("https://canvas.com/files/99", 99)
    mock_course = MagicMock()
    mock_course._requester = MagicMock()
    mock_course._requester.original_url = "https://canvas.com"
    mock_course.id = 1

    content = "[Template](template.qmd)"
    result = process_content(content, "/base", mock_course)
    mock_upload.assert_called_once()
    assert "99" in result  # file ID appears in the URL


@patch("handlers.content_utils.upload_file")
@patch("handlers.content_utils.resolve_cross_link")
def test_pdf_link_uploaded(mock_resolve, mock_upload):
    """PDF links are uploaded as files."""
    mock_upload.return_value = ("https://canvas.com/files/55/syllabus.pdf", 55)
    mock_course = MagicMock()
    mock_course._requester = MagicMock()
    mock_course._requester.original_url = "https://canvas.com"
    mock_course.id = 1

    content = "[Syllabus](docs/syllabus.pdf)"
    result = process_content(content, "/base", mock_course)
    mock_upload.assert_called_once()
    assert "55" in result


@patch("handlers.content_utils.upload_file")
def test_html_img_tag_processed(mock_upload):
    """HTML <img> tags with local src also trigger upload."""
    mock_upload.return_value = ("https://canvas.com/files/77/photo.png", 77)
    mock_course = MagicMock()

    content = '<img src="photo.png" alt="Photo">'
    result = process_content(content, "/base", mock_course)
    mock_upload.assert_called_once()
    assert "https://canvas.com/files/77/photo.png" in result


@patch("handlers.content_utils.upload_file")
def test_html_img_http_not_uploaded(mock_upload):
    """HTTP <img> tags are left as-is."""
    mock_course = MagicMock()
    content = '<img src="https://example.com/photo.png">'
    result = process_content(content, "/base", mock_course)
    mock_upload.assert_not_called()


@patch("handlers.content_utils.upload_file")
@patch("handlers.content_utils.resolve_cross_link")
def test_http_links_not_processed(mock_resolve, mock_upload):
    """External HTTP links are preserved as-is."""
    mock_course = MagicMock()
    content = "[Canvas](https://canvas.instructure.com)"
    result = process_content(content, "/base", mock_course)
    mock_upload.assert_not_called()
    mock_resolve.assert_not_called()
    assert "https://canvas.instructure.com" in result
