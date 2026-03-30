"""Tests for handlers/config.py — configuration resolution."""

import os
import pytest
from handlers.config import load_config, get_course_id, get_api_credentials, _config_cache


class TestLoadConfig:

    def test_no_config_file(self, tmp_path):
        cfg = load_config(str(tmp_path))
        assert isinstance(cfg, dict)

    def test_with_toml(self, tmp_path):
        (tmp_path / "config.toml").write_text('course_id = 12345\n')
        cfg = load_config(str(tmp_path))
        assert cfg["course_id"] == 12345

    def test_caching(self, tmp_path):
        """Second call returns cached result."""
        (tmp_path / "config.toml").write_text('course_id = 42\n')
        cfg1 = load_config(str(tmp_path))
        cfg2 = load_config(str(tmp_path))
        assert cfg1 is cfg2


class TestGetCourseId:

    def test_from_cli_arg(self, tmp_path):
        assert get_course_id(str(tmp_path), "999") == "999"

    def test_from_toml(self, tmp_path):
        (tmp_path / "config.toml").write_text('course_id = 42\n')
        assert get_course_id(str(tmp_path)) == "42"

    def test_from_legacy_txt(self, tmp_path):
        (tmp_path / "course_id.txt").write_text("1434")
        assert get_course_id(str(tmp_path)) == "1434"

    def test_cli_wins_over_toml(self, tmp_path):
        (tmp_path / "config.toml").write_text('course_id = 42\n')
        assert get_course_id(str(tmp_path), "999") == "999"

    def test_toml_wins_over_txt(self, tmp_path):
        (tmp_path / "config.toml").write_text('course_id = 42\n')
        (tmp_path / "course_id.txt").write_text("1434")
        assert get_course_id(str(tmp_path)) == "42"

    def test_nothing_configured(self, tmp_path):
        assert get_course_id(str(tmp_path)) is None


class TestGetApiCredentials:

    def test_from_env(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CANVAS_API_URL", "https://canvas.test.com")
        monkeypatch.setenv("CANVAS_API_TOKEN", "test-token-123")
        url, token = get_api_credentials(str(tmp_path))
        assert url == "https://canvas.test.com"
        assert token == "test-token-123"

    def test_url_from_toml(self, tmp_path, monkeypatch):
        monkeypatch.delenv("CANVAS_API_URL", raising=False)
        monkeypatch.delenv("CANVAS_API_TOKEN", raising=False)
        (tmp_path / "config.toml").write_text('canvas_api_url = "https://toml.canvas.com"\n')
        url, token = get_api_credentials(str(tmp_path))
        assert url == "https://toml.canvas.com"

    def test_env_url_wins_over_toml(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CANVAS_API_URL", "https://env.canvas.com")
        monkeypatch.delenv("CANVAS_API_TOKEN", raising=False)
        (tmp_path / "config.toml").write_text('canvas_api_url = "https://toml.canvas.com"\n')
        url, _ = get_api_credentials(str(tmp_path))
        assert url == "https://env.canvas.com"
