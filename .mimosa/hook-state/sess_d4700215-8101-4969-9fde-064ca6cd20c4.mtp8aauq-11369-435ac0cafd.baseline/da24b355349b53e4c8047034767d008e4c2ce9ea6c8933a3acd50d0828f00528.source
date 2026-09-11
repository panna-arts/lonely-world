"""Tests for config module."""

from unittest.mock import patch

import pytest

from lonely_world.config import ensure_config, load_config, save_config
from lonely_world.models import GameConfig


class TestLoadSaveConfig:
    def test_round_trip(self, tmp_path, monkeypatch):
        from lonely_world import config as config_module

        monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
        cfg = GameConfig(api_key="secret", base_url="https://api.example.com/v1", model="gpt-4")
        save_config(cfg)
        loaded = load_config()
        assert loaded.api_key == "secret"
        assert loaded.base_url == "https://api.example.com/v1"
        assert loaded.model == "gpt-4"


class TestEnsureConfig:
    def test_env_vars_override(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "env_key")
        monkeypatch.setenv("OPENAI_BASE_URL", "env_base")
        monkeypatch.setenv("LONELY_WORLD_MODEL", "env_model")
        cfg = GameConfig()
        result = ensure_config(cfg)
        assert result.api_key == "env_key"
        assert result.base_url == "env_base"
        assert result.model == "env_model"

    def test_keyring_preferred_over_config(self, monkeypatch):
        from lonely_world import config as config_module

        cfg = GameConfig(api_key="", base_url="https://api.example.com/v1", model="gpt-4")
        monkeypatch.setattr(config_module, "_get_keyring_api_key", lambda: "keyring_key")
        result = ensure_config(cfg)
        assert result.api_key == "keyring_key"

    def test_migration_from_config_to_keyring(self, monkeypatch):
        from lonely_world import config as config_module

        cfg = GameConfig(api_key="old_config_key")
        monkeypatch.setattr(config_module, "_get_keyring_api_key", lambda: "")
        set_calls = []
        monkeypatch.setattr(
            config_module, "_set_keyring_api_key", lambda k: set_calls.append(k) or True
        )
        monkeypatch.setenv("OPENAI_API_KEY", "")
        monkeypatch.setenv("LONELY_WORLD_API_KEY", "")
        monkeypatch.setenv("OPENAI_BASE_URL", "base")
        monkeypatch.setenv("LONELY_WORLD_MODEL", "model")
        result = ensure_config(cfg)
        assert "old_config_key" in set_calls
        assert result.api_key == ""

    @patch("lonely_world.config.input", side_effect=["https://api.example.com/v1", "gpt-4"])
    @patch("lonely_world.config.getpass", return_value="typed_key")
    def test_prompt_fallback(self, mock_getpass, mock_input, monkeypatch):
        from lonely_world import config as config_module

        monkeypatch.setattr(config_module, "_get_keyring_api_key", lambda: "")
        monkeypatch.setenv("OPENAI_API_KEY", "")
        monkeypatch.setenv("LONELY_WORLD_API_KEY", "")
        monkeypatch.setenv("OPENAI_BASE_URL", "")
        monkeypatch.setenv("LONELY_WORLD_MODEL", "")
        monkeypatch.setattr(config_module, "_set_keyring_api_key", lambda k: True)
        cfg = GameConfig()
        result = ensure_config(cfg)
        assert result.api_key == ""

    @patch("lonely_world.config.getpass", return_value="")
    def test_prompt_empty_exits(self, mock_getpass, monkeypatch):
        from lonely_world import config as config_module

        monkeypatch.setattr(config_module, "_get_keyring_api_key", lambda: "")
        monkeypatch.setenv("OPENAI_API_KEY", "")
        monkeypatch.setenv("LONELY_WORLD_API_KEY", "")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://api.example.com/v1")
        monkeypatch.setenv("LONELY_WORLD_MODEL", "gpt-4")
        cfg = GameConfig()
        with pytest.raises(SystemExit):
            ensure_config(cfg)
