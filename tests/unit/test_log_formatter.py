"""Tests for the Rich markup stripping log formatter."""

import logging
from handlers.log import _RichMarkupStrippingFormatter


class TestRichMarkupStrippingFormatter:

    def _make_record(self, msg):
        return logging.LogRecord("test", logging.INFO, "", 0, msg, (), None)

    def test_strips_bold(self):
        fmt = _RichMarkupStrippingFormatter("%(message)s")
        record = self._make_record("[bold]hello[/bold]")
        result = fmt.format(record)
        assert result == "hello"

    def test_strips_color(self):
        fmt = _RichMarkupStrippingFormatter("%(message)s")
        record = self._make_record("[red]error[/red] text")
        result = fmt.format(record)
        assert result == "error text"

    def test_strips_compound_markup(self):
        fmt = _RichMarkupStrippingFormatter("%(message)s")
        record = self._make_record("[bold cyan]Processing[/bold cyan]")
        result = fmt.format(record)
        assert result == "Processing"

    def test_preserves_plain_text(self):
        fmt = _RichMarkupStrippingFormatter("%(message)s")
        record = self._make_record("plain text")
        result = fmt.format(record)
        assert result == "plain text"

    def test_preserves_original_message(self):
        """The original record.msg must survive for other handlers (Rich)."""
        fmt = _RichMarkupStrippingFormatter("%(message)s")
        record = self._make_record("[green]ok[/green]")
        fmt.format(record)
        assert record.msg == "[green]ok[/green]"

    def test_strips_nested_markup(self):
        fmt = _RichMarkupStrippingFormatter("%(message)s")
        record = self._make_record("[bold][red]nested[/red][/bold]")
        result = fmt.format(record)
        assert result == "nested"

    def test_non_string_message_passthrough(self):
        """Non-string messages (rare but possible) should not crash."""
        fmt = _RichMarkupStrippingFormatter("%(message)s")
        record = self._make_record(12345)
        result = fmt.format(record)
        assert "12345" in result
