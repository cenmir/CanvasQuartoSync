"""Tests for BaseHandler.add_to_module() with mocked Canvas module."""

from unittest.mock import MagicMock
from handlers.page_handler import PageHandler


def _make_mock_module(existing_items=None):
    """Create a mock Canvas module with stubbed methods."""
    module = MagicMock()
    module.name = "Test Module"
    module.get_module_items.return_value = existing_items or []

    new_item = MagicMock()
    new_item.position = 1
    module.create_module_item.return_value = new_item
    return module


def _make_existing_item(item_type, **kwargs):
    """Create a mock existing module item."""
    item = MagicMock()
    item.type = item_type
    item.title = kwargs.get("title", "Test Item")
    item.indent = kwargs.get("indent", 0)
    item.published = kwargs.get("published", True)
    item.page_url = kwargs.get("page_url", None)
    item.content_id = kwargs.get("content_id", None)
    item.external_url = kwargs.get("external_url", None)
    return item


class TestCreateNewItem:

    def test_creates_page_in_empty_module(self):
        module = _make_mock_module()
        handler = PageHandler()
        handler.add_to_module(module, {
            "type": "Page",
            "page_url": "test-page",
            "title": "Test Page",
            "published": True,
        })
        module.create_module_item.assert_called_once()
        payload = module.create_module_item.call_args[1]["module_item"]
        assert payload["type"] == "Page"
        assert payload["page_url"] == "test-page"

    def test_published_set_separately_after_create(self):
        """Canvas ignores published during creation — must be set via edit."""
        module = _make_mock_module()
        handler = PageHandler()
        result = handler.add_to_module(module, {
            "type": "Page",
            "page_url": "p",
            "title": "T",
            "published": False,
        })
        # The new_item.edit should be called with published
        result.edit.assert_called_once_with(module_item={"published": False})

    def test_no_edit_when_published_is_none(self):
        module = _make_mock_module()
        handler = PageHandler()
        result = handler.add_to_module(module, {
            "type": "Page",
            "page_url": "p",
            "title": "T",
            "published": None,
        })
        result.edit.assert_not_called()

    def test_indent_included_in_payload(self):
        module = _make_mock_module()
        handler = PageHandler()
        handler.add_to_module(module, {
            "type": "Page",
            "page_url": "p",
            "title": "T",
        }, indent=2)
        payload = module.create_module_item.call_args[1]["module_item"]
        assert payload["indent"] == 2


class TestUpdateExistingItem:

    def test_matches_existing_page_by_url(self):
        existing = _make_existing_item("Page", page_url="test-page", title="Old Title")
        module = _make_mock_module([existing])
        handler = PageHandler()
        result = handler.add_to_module(module, {
            "type": "Page",
            "page_url": "test-page",
            "title": "New Title",
            "published": True,
        })
        # Should update existing, not create new
        module.create_module_item.assert_not_called()
        existing.edit.assert_called_once()
        updates = existing.edit.call_args[1]["module_item"]
        assert updates["title"] == "New Title"

    def test_no_edit_when_nothing_changed(self):
        existing = _make_existing_item("Page", page_url="p", title="Same", indent=0, published=True)
        module = _make_mock_module([existing])
        handler = PageHandler()
        handler.add_to_module(module, {
            "type": "Page",
            "page_url": "p",
            "title": "Same",
            "published": True,
        }, indent=0)
        existing.edit.assert_not_called()

    def test_updates_indent(self):
        existing = _make_existing_item("Page", page_url="p", title="T", indent=0)
        module = _make_mock_module([existing])
        handler = PageHandler()
        handler.add_to_module(module, {
            "type": "Page",
            "page_url": "p",
            "title": "T",
        }, indent=2)
        updates = existing.edit.call_args[1]["module_item"]
        assert updates["indent"] == 2

    def test_matches_assignment_by_content_id(self):
        existing = _make_existing_item("Assignment", content_id=42, title="HW")
        module = _make_mock_module([existing])
        handler = PageHandler()
        result = handler.add_to_module(module, {
            "type": "Assignment",
            "content_id": 42,
            "title": "HW Updated",
        })
        module.create_module_item.assert_not_called()
        updates = existing.edit.call_args[1]["module_item"]
        assert updates["title"] == "HW Updated"

    def test_matches_subheader_by_title(self):
        existing = _make_existing_item("SubHeader", title="Resources")
        module = _make_mock_module([existing])
        handler = PageHandler()
        result = handler.add_to_module(module, {
            "type": "SubHeader",
            "title": "Resources",
        })
        module.create_module_item.assert_not_called()

    def test_matches_external_url(self):
        existing = _make_existing_item("ExternalUrl", external_url="https://example.com")
        module = _make_mock_module([existing])
        handler = PageHandler()
        result = handler.add_to_module(module, {
            "type": "ExternalUrl",
            "external_url": "https://example.com",
            "title": "Example",
        })
        module.create_module_item.assert_not_called()


class TestIndentClamping:

    def test_negative_indent_clamped_to_zero(self):
        module = _make_mock_module()
        handler = PageHandler()
        handler.add_to_module(module, {
            "type": "Page",
            "page_url": "p",
            "title": "T",
        }, indent=-1)
        payload = module.create_module_item.call_args[1]["module_item"]
        assert payload["indent"] == 0

    def test_indent_above_5_clamped(self):
        module = _make_mock_module()
        handler = PageHandler()
        handler.add_to_module(module, {
            "type": "Page",
            "page_url": "p",
            "title": "T",
        }, indent=10)
        payload = module.create_module_item.call_args[1]["module_item"]
        assert payload["indent"] == 5
