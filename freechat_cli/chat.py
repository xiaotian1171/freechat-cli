"""Core chat client and conversation management.

Provides Conversation (history + serialization) and ChatClient (API calls).
"""

import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Generator, List, Optional
from urllib.parse import quote

from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError

from ._version import __version__
from .config import Config
from .utils import estimate_messages_tokens

SAVE_DIR = Path.home() / ".freechat" / "conversations"


class Conversation:
    """Manages conversation history with save/load, export, and undo."""

    def __init__(
        self,
        max_history: int = 20,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.max_history = max_history
        self.model = model
        self.messages: List[dict] = []
        self.created_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    # ── Properties ──────────────────────────────────────────────

    @property
    def system_prompt(self) -> Optional[str]:
        """Return the current system prompt, or None."""
        for msg in self.messages:
            if msg["role"] == "system":
                return msg["content"]
        return None

    @system_prompt.setter
    def system_prompt(self, value: str) -> None:
        self.messages = [m for m in self.messages if m["role"] != "system"]
        if value:
            self.messages.insert(0, {"role": "system", "content": value})

    @property
    def turn_count(self) -> int:
        return sum(1 for m in self.messages if m["role"] == "user")

    @property
    def last_response(self) -> Optional[str]:
        """Return the last assistant message content."""
        for msg in reversed(self.messages):
            if msg["role"] == "assistant":
                return msg["content"]
        return None

    @property
    def estimated_tokens(self) -> int:
        """Estimate total tokens in current context window."""
        return estimate_messages_tokens(self.get_context())

    # ── Message management ──────────────────────────────────────

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def get_context(self) -> List[dict]:
        """Return messages trimmed to max_history turns (excluding system)."""
        system_msgs = [m for m in self.messages if m["role"] == "system"]
        non_system = [m for m in self.messages if m["role"] != "system"]
        max_msgs = self.max_history * 2
        trimmed = non_system[-max_msgs:] if len(non_system) > max_msgs else non_system
        return system_msgs + trimmed

    def clear(self) -> None:
        """Clear all messages except system prompt."""
        system = self.system_prompt
        self.messages = []
        if system:
            self.messages.append({"role": "system", "content": system})

    def undo(self) -> int:
        """Remove the last exchange (assistant + user). Returns count of removed messages."""
        removed = 0
        # Remove trailing assistant first, then user
        while removed < 2 and self.messages and self.messages[-1]["role"] != "system":
            self.messages.pop()
            removed += 1
            # Stop after removing one user-assistant pair
            if removed >= 2:
                break
            # If we hit user without assistant, keep going
        return removed

    # ── Persistence ─────────────────────────────────────────────

    def save(self, path: Optional[str] = None) -> Path:
        """Save conversation to JSON file with metadata."""
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        if not path:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            path = f"chat_{timestamp}.json"
        if not path.endswith(".json"):
            path += ".json"
        filepath = SAVE_DIR / path
        data = {
            "version": 2,
            "model": self.model,
            "created_at": self.created_at,
            "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "turn_count": self.turn_count,
            "estimated_tokens": self.estimated_tokens,
            "messages": self.messages,
        }
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return filepath

    @classmethod
    def load(cls, path: str, max_history: int = 20) -> "Conversation":
        """Load conversation from file. Supports v1 (bare list) and v2 (with metadata)."""
        filepath = SAVE_DIR / path if not Path(path).is_absolute() else Path(path)
        if not filepath.exists():
            raise FileNotFoundError(f"Conversation not found: {filepath}")
        data = json.loads(filepath.read_text(encoding="utf-8"))
        conv = cls(max_history=max_history)
        if isinstance(data, list):
            conv.messages = data
        else:
            conv.messages = data.get("messages", [])
            conv.model = data.get("model")
            conv.created_at = data.get("created_at", "")
        return conv

    @classmethod
    def list_saved(cls, limit: int = 20) -> List[dict]:
        """List saved conversations with metadata. Returns list of dicts."""
        if not SAVE_DIR.exists():
            return []
        files = sorted(SAVE_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        results = []
        for f in files[:limit]:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    results.append(
                        {
                            "filename": f.name,
                            "model": data.get("model", "?"),
                            "turns": data.get("turn_count", len(data.get("messages", [])) // 2),
                            "saved_at": data.get("saved_at", ""),
                        }
                    )
                else:
                    results.append(
                        {
                            "filename": f.name,
                            "model": "?",
                            "turns": len(data) // 2,
                            "saved_at": "",
                        }
                    )
            except Exception:
                results.append({"filename": f.name, "model": "?", "turns": "?", "saved_at": ""})
        return results

    def export_markdown(self, path: Optional[str] = None) -> Path:
        """Export conversation to a Markdown file."""
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        if not path:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            path = f"chat_{timestamp}.md"
        if not path.endswith(".md"):
            path += ".md"
        filepath = SAVE_DIR / path

        lines = ["# FreeChat Conversation", ""]
        if self.model:
            lines.append(f"**Model**: `{self.model}`  ")
        lines.append(f"**Date**: {self.created_at}  ")
        lines.append(f"**Turns**: {self.turn_count}  ")
        lines.append(f"**Estimated tokens**: {self.estimated_tokens}  ")
        lines.append("")
        lines.append("---")
        lines.append("")

        for msg in self.messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                lines.append(f"> **System**: {content}")
                lines.append("")
            elif role == "user":
                lines.append("## 👤 User")
                lines.append("")
                lines.append(content)
                lines.append("")
            elif role == "assistant":
                lines.append("## 🤖 Assistant")
                lines.append("")
                lines.append(content)
                lines.append("")
            lines.append("---")
            lines.append("")

        filepath.write_text("\n".join(lines), encoding="utf-8")
        return filepath


class ChatClient:
    """Client for chat completions via OpenAI-compatible API.

    Supports streaming, retry with backoff, and image generation.
    """

    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or Config.load()

        client_kwargs: dict = {
            "api_key": self.config.api_key or "freechat-no-key",
            "base_url": self.config.base_url,
            "timeout": self.config.timeout,
        }
        self.client = OpenAI(**client_kwargs)
        self.conversation = Conversation(
            max_history=self.config.max_history,
            system_prompt=self.config.system_prompt,
            model=self.config.model,
        )

    def chat(self, message: str, stream: bool = True) -> Generator[str, None, None]:
        """Send a message and yield response chunks.

        Routes to the native Pollinations legacy endpoint when base_url points
        at text.pollinations.ai, otherwise uses the OpenAI-compatible client.
        On rate limit or timeout, automatically retries with exponential backoff
        up to config.max_retries times before raising RuntimeError.
        """
        self.conversation.add_user(message)
        context = self.conversation.get_context()

        if self._is_legacy_pollinations():
            return self._chat_legacy(context, stream=stream)

        retries_remaining = self.config.max_retries
        delay = 1.0

        while True:
            try:
                if stream:
                    return self._chat_stream(context)
                else:
                    return self._chat_sync(context)
            except RateLimitError:
                if retries_remaining > 0:
                    retries_remaining -= 1
                    time.sleep(min(delay, 30.0))
                    delay *= 2
                    continue
                raise RuntimeError(
                    "Rate limited — too many requests after retries. Please wait and try again."
                )
            except APITimeoutError:
                if retries_remaining > 0:
                    retries_remaining -= 1
                    time.sleep(min(delay, 10.0))
                    delay *= 2
                    continue
                raise RuntimeError(
                    f"Request timed out ({self.config.timeout}s) after retries. "
                    "Try --timeout to increase."
                )
            except APIConnectionError:
                raise RuntimeError("Cannot connect to API. Check your network or base URL.")
            except Exception as e:
                msg = getattr(e, "message", str(e))
                raise RuntimeError(f"API error: {msg}")

    def _chat_stream(self, context: list) -> Generator[str, None, None]:
        """Streaming chat completion."""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=context,
            stream=True,
        )
        full_response = ""
        for chunk in response:
            if chunk.choices:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    full_response += delta.content
                    yield delta.content
        self.conversation.add_assistant(full_response or "")

    def _chat_sync(self, context: list) -> Generator[str, None, None]:
        """Non-streaming chat completion."""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=context,
            stream=False,
        )
        content = response.choices[0].message.content or ""
        self.conversation.add_assistant(content)
        yield content

    # ── Native Pollinations legacy endpoint ─────────────────────

    def _is_legacy_pollinations(self) -> bool:
        """True when base_url points at the native text.pollinations.ai endpoint."""
        return self.config.base_url.rstrip("/").endswith("text.pollinations.ai")

    def _legacy_request(self, context: list, stream: bool) -> dict:
        """Build the HTTP request for the legacy Pollinations POST endpoint.

        The anonymous free tier serves its default model; explicitly passing a
        model name can route the request into a paid tier (HTTP 402/500), so it
        is intentionally omitted.
        """
        body = {"messages": context}
        if stream:
            body["stream"] = True
        headers = {"Content-Type": "application/json", "User-Agent": f"freechat-cli/{__version__}"}
        if stream:
            headers["Accept"] = "text/event-stream"
        return urllib.request.Request(
            self.config.base_url.rstrip("/") + "/",
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )

    def _chat_legacy(self, context: list, stream: bool) -> Generator[str, None, None]:
        """Dispatch a legacy-endpoint request and return the response generator.

        This is intentionally NOT a generator function: the request (and its
        retry/backoff loop) must fire eagerly when chat() is called, returning
        the inner streaming/plain generator directly.
        """
        retries_remaining = self.config.max_retries
        delay = 1.0

        while True:
            try:
                req = self._legacy_request(context, stream=stream)
                resp = urllib.request.urlopen(req, timeout=self.config.timeout)
                if stream:
                    return self._legacy_consume_sse(resp)
                return self._legacy_consume_plain(resp)
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504) and retries_remaining > 0:
                    retries_remaining -= 1
                    time.sleep(min(delay, 30.0))
                    delay *= 2
                    continue
                raise RuntimeError(f"Pollinations API error: HTTP {e.code}")
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                reason = getattr(e, "reason", e)
                raise RuntimeError(f"Cannot connect to Pollinations: {reason}")

    def _legacy_consume_plain(self, resp) -> Generator[str, None, None]:
        """Read a non-streaming (text/plain) response body."""
        text = resp.read().decode("utf-8", errors="replace").strip()
        if text.startswith("{"):
            try:
                data = json.loads(text)
                if isinstance(data, dict) and "error" in data:
                    raise RuntimeError(f"Pollinations API error: {data['error']}")
            except json.JSONDecodeError:
                pass
        self.conversation.add_assistant(text)
        yield text

    def _legacy_consume_sse(self, resp) -> Generator[str, None, None]:
        """Parse an SSE stream of OpenAI-style chunks from the legacy endpoint."""
        full_response = ""
        for raw in resp:
            line = raw.decode("utf-8", errors="replace").strip()
            if not line.startswith("data:"):
                continue
            payload = line[len("data:"):].strip()
            if not payload or payload == "[DONE]":
                if payload == "[DONE]":
                    break
                continue
            try:
                chunk = json.loads(payload)
            except json.JSONDecodeError:
                continue
            if isinstance(chunk, dict) and "error" in chunk:
                raise RuntimeError(f"Pollinations API error: {chunk['error']}")
            choices = chunk.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            content = delta.get("content")
            if content:
                full_response += content
                yield content
        self.conversation.add_assistant(full_response or "")

    def _legacy_list_models(self) -> List[str]:
        """Fetch model names from the legacy /models endpoint."""
        url = self.config.base_url.rstrip("/") + "/models"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        names = set()
        for item in data if isinstance(data, list) else []:
            name = item.get("name")
            if name:
                names.add(name)
        return sorted(names)

    def list_models(self) -> List[str]:
        """Fetch available models from the API endpoint."""
        try:
            if self._is_legacy_pollinations():
                models = self._legacy_list_models()
                if models:
                    return models
                raise RuntimeError("empty model list")
            models = self.client.models.list()
            return sorted(m.id for m in models.data)
        except Exception:
            return [
                "openai",
                "openai-large",
                "mistral",
                "mistral-large",
                "deepseek",
                "deepseek-r1",
                "qwen",
                "qwen-coder",
                "gemini",
                "llama",
                "llama-scale",
                "grok",
                "claude",
                "claude-hybridspace",
            ]

    def generate_image_url(
        self, prompt: str, model: str = "flux", width: int = 1024, height: int = 1024
    ) -> str:
        """Generate an image via Pollinations image API. Returns the image URL."""
        encoded = quote(prompt)
        return (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?model={model}&width={width}&height={height}&nologo=true"
        )

    def set_model(self, model: str) -> None:
        self.config.model = model
        self.conversation.model = model

    def set_system_prompt(self, prompt: str) -> None:
        self.conversation.system_prompt = prompt
