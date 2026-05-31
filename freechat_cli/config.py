"""Configuration management for FreeChat CLI."""

import json
import os
from pathlib import Path
from typing import Optional

DEFAULT_BASE_URL = "https://text.pollinations.ai/openai"
DEFAULT_MODEL = "openai"
DEFAULT_MAX_HISTORY = 20
CONFIG_DIR = Path.home() / ".freechat"
CONFIG_FILE = CONFIG_DIR / "config.json"


class Config:
    """Manages FreeChat configuration."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        system_prompt: Optional[str] = None,
        max_history: int = DEFAULT_MAX_HISTORY,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.max_history = max_history
        self.api_key = api_key
        self.base_url = base_url

    @classmethod
    def load(cls) -> "Config":
        """Load config from file, falling back to defaults."""
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                return cls(
                    model=data.get("model", DEFAULT_MODEL),
                    system_prompt=data.get("system_prompt"),
                    max_history=data.get("max_history", DEFAULT_MAX_HISTORY),
                    api_key=data.get("api_key") or os.environ.get("FREECHAT_API_KEY"),
                    base_url=data.get("base_url", DEFAULT_BASE_URL),
                )
            except (json.JSONDecodeError, KeyError):
                pass

        return cls(
            api_key=os.environ.get("FREECHAT_API_KEY"),
        )

    def save(self):
        """Save current config to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "model": self.model,
            "system_prompt": self.system_prompt,
            "max_history": self.max_history,
            "api_key": self.api_key or "",
            "base_url": self.base_url,
        }
        CONFIG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "system_prompt": self.system_prompt,
            "max_history": self.max_history,
            "api_key": "***" if self.api_key else "(none)",
            "base_url": self.base_url,
        }
