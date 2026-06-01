"""Tests for config module."""

import json
from unittest import mock

from freechat_cli.config import Config


class TestConfig:
    """Test Config class."""

    def test_defaults(self):
        config = Config()
        assert config.model == "openai"
        assert config.system_prompt is None
        assert config.max_history == 20
        assert config.api_key is None
        assert config.base_url == "https://text.pollinations.ai/openai"
        assert config.timeout == 120
        assert config.max_retries == 2

    def test_custom_values(self):
        config = Config(
            model="deepseek",
            system_prompt="You are helpful",
            max_history=10,
            api_key="sk-test",
            base_url="https://api.example.com/v1",
            timeout=30,
            max_retries=5,
        )
        assert config.model == "deepseek"
        assert config.system_prompt == "You are helpful"
        assert config.max_history == 10
        assert config.api_key == "sk-test"
        assert config.base_url == "https://api.example.com/v1"
        assert config.timeout == 30
        assert config.max_retries == 5

    def test_to_dict_masks_api_key(self):
        config = Config(api_key="sk-secret")
        d = config.to_dict(partial=True)
        assert d["api_key"] == "***"

    def test_to_dict_shows_api_key_when_not_partial(self):
        config = Config(api_key="sk-secret")
        d = config.to_dict(partial=False)
        assert d["api_key"] == "sk-secret"

    def test_to_dict_no_api_key(self):
        config = Config()
        d = config.to_dict(partial=True)
        assert d["api_key"] == ""

    def test_save_and_load(self, tmp_path):
        config_dir = tmp_path / ".freechat"
        config_file = config_dir / "config.json"

        with (
            mock.patch("freechat_cli.config.CONFIG_DIR", config_dir),
            mock.patch("freechat_cli.config.CONFIG_FILE", config_file),
        ):
            config = Config(model="mistral", system_prompt="test", api_key="sk-123")
            config.save()

            assert config_file.exists()
            data = json.loads(config_file.read_text(encoding="utf-8"))
            assert data["model"] == "mistral"
            assert data["system_prompt"] == "test"
            assert data["api_key"] == "sk-123"

            # Load it back
            loaded = Config.load()
            assert loaded.model == "mistral"
            assert loaded.system_prompt == "test"
            assert loaded.api_key == "sk-123"

    def test_load_missing_file(self, tmp_path):
        config_file = tmp_path / "nonexistent" / "config.json"
        with mock.patch("freechat_cli.config.CONFIG_FILE", config_file):
            config = Config.load()
            assert config.model == "openai"  # defaults

    def test_load_env_var(self):
        with mock.patch.dict("os.environ", {"FREECHAT_API_KEY": "sk-from-env"}):
            config = Config.load()
            assert config.api_key == "sk-from-env"

    def test_load_invalid_json(self, tmp_path):
        config_dir = tmp_path / ".freechat"
        config_dir.mkdir()
        config_file = config_dir / "config.json"
        config_file.write_text("{invalid json", encoding="utf-8")

        with (
            mock.patch("freechat_cli.config.CONFIG_DIR", config_dir),
            mock.patch("freechat_cli.config.CONFIG_FILE", config_file),
        ):
            config = Config.load()
            assert config.model == "openai"  # falls back to defaults
