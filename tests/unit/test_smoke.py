"""Smoke test — verifies test infrastructure works."""


def test_import_content_utils():
    from handlers.content_utils import parse_module_name
    assert parse_module_name("01_Hello") == "Hello"


def test_import_config():
    from handlers.config import load_config
    assert callable(load_config)
