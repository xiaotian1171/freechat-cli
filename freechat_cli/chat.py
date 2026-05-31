"""Core chat client and conversation management."""

import json
import time
from pathlib import Path
from typing import Generator, List, Optional

from openai import OpenAI

from .config import Config

SAVE_DIR = Path.home() / ".freechat" / "conversations"


class Conversation:
    """Manages conversation history."""

    def __init__(self, max_history: int = 20, system_prompt: Optional[str] = None):
        self.max_history = max_history
        self.messages: List[dict] = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    @property
    def system_prompt(self) -> Optional[str]:
        for msg in self.messages:
            if msg["role"] == "system":
                return msg["content"]
        return None

    @system_prompt.setter
    def system_prompt(self, value: str):
        # Remove existing system prompts
        self.messages = [m for m in self.messages if m["role"] != "system"]
        if value:
            self.messages.insert(0, {"role": "system", "content": value})

    def add_user(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    def get_context(self) -> List[dict]:
        """Return messages trimmed to max_history turns (excluding system)."""
        system_msgs = [m for m in self.messages if m["role"] == "system"]
        non_system = [m for m in self.messages if m["role"] != "system"]
        # Keep last max_history message pairs (user + assistant = 2 messages per turn)
        max_msgs = self.max_history * 2
        trimmed = non_system[-max_msgs:] if len(non_system) > max_msgs else non_system
        return system_msgs + trimmed

    def clear(self):
        system = self.system_prompt
        self.messages = []
        if system:
            self.messages.append({"role": "system", "content": system})

    def save(self, path: Optional[str] = None) -> Path:
        """Save conversation to file."""
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        if not path:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            path = f"chat_{timestamp}.json"
        filepath = SAVE_DIR / path
        filepath.write_text(
            json.dumps(self.messages, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return filepath

    @classmethod
    def load(cls, path: str, max_history: int = 20) -> "Conversation":
        """Load conversation from file."""
        filepath = SAVE_DIR / path
        if not filepath.exists():
            raise FileNotFoundError(f"Conversation not found: {filepath}")
        data = json.loads(filepath.read_text(encoding="utf-8"))
        conv = cls(max_history=max_history)
        conv.messages = data
        return conv

    @property
    def turn_count(self) -> int:
        return sum(1 for m in self.messages if m["role"] == "user")


class ChatClient:
    """Client for chat completions via OpenAI-compatible API."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.load()

        client_kwargs = {
            "api_key": self.config.api_key or "freechat-no-key",
            "base_url": self.config.base_url,
        }
        self.client = OpenAI(**client_kwargs)
        self.conversation = Conversation(
            max_history=self.config.max_history,
            system_prompt=self.config.system_prompt,
        )

    def chat(self, message: str, stream: bool = True) -> Generator[str, None, None]:
        """Send a message and yield response chunks (streaming) or full response."""
        self.conversation.add_user(message)
        context = self.conversation.get_context()

        if stream:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=context,
                stream=True,
            )
            full_response = ""
            for chunk in response:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    full_response += delta.content
                    yield delta.content
            self.conversation.add_assistant(full_response)
        else:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=context,
                stream=False,
            )
            content = response.choices[0].message.content or ""
            self.conversation.add_assistant(content)
            yield content

    def list_models(self) -> List[str]:
        """Fetch available models from the API endpoint."""
        try:
            models = self.client.models.list()
            return sorted([m.id for m in models.data])
        except Exception:
            return [
                "openai",
                "mistral",
                "deepseek",
                "qwen",
                "gemini",
                "llama",
                "grok",
                "claude",
            ]

    def set_model(self, model: str):
        self.config.model = model

    def set_system_prompt(self, prompt: str):
        self.conversation.system_prompt = prompt
