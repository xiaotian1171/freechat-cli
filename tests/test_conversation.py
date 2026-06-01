"""Tests for conversation and chat client."""

import json
from unittest import mock

from freechat_cli.chat import Conversation


class TestConversation:
    """Test Conversation class."""

    def test_empty_conversation(self):
        conv = Conversation()
        assert conv.turn_count == 0
        assert conv.system_prompt is None
        assert conv.last_response is None
        assert len(conv.messages) == 0

    def test_system_prompt(self):
        conv = Conversation(system_prompt="You are helpful")
        assert conv.system_prompt == "You are helpful"
        assert len(conv.messages) == 1

    def test_system_prompt_setter(self):
        conv = Conversation()
        conv.system_prompt = "New prompt"
        assert conv.system_prompt == "New prompt"
        assert len(conv.messages) == 1

    def test_system_prompt_overwrite(self):
        conv = Conversation(system_prompt="Old")
        conv.system_prompt = "New"
        assert conv.system_prompt == "New"
        assert len(conv.messages) == 1

    def test_add_messages(self):
        conv = Conversation()
        conv.add_user("Hello")
        conv.add_assistant("Hi there!")
        assert conv.turn_count == 1
        assert conv.last_response == "Hi there!"
        assert len(conv.messages) == 2

    def test_get_context_respects_max_history(self):
        conv = Conversation(max_history=2)
        conv.add_user("q1")
        conv.add_assistant("a1")
        conv.add_user("q2")
        conv.add_assistant("a2")
        conv.add_user("q3")
        conv.add_assistant("a3")
        ctx = conv.get_context()
        # Should only keep last 2 turns (4 messages)
        assert len(ctx) == 4
        assert ctx[0]["content"] == "q2"

    def test_get_context_preserves_system(self):
        conv = Conversation(max_history=1, system_prompt="System")
        conv.add_user("q1")
        conv.add_assistant("a1")
        conv.add_user("q2")
        conv.add_assistant("a2")
        ctx = conv.get_context()
        assert ctx[0]["role"] == "system"
        assert len(ctx) == 3  # system + 1 turn

    def test_clear(self):
        conv = Conversation(system_prompt="Keep me")
        conv.add_user("Hello")
        conv.clear()
        assert conv.system_prompt == "Keep me"
        assert conv.turn_count == 0

    def test_undo(self):
        conv = Conversation()
        conv.add_user("q1")
        conv.add_assistant("a1")
        conv.add_user("q2")
        conv.add_assistant("a2")
        removed = conv.undo()
        assert removed == 2
        assert conv.turn_count == 1
        assert conv.last_response == "a1"

    def test_undo_empty(self):
        conv = Conversation()
        removed = conv.undo()
        assert removed == 0

    def test_undo_preserves_system(self):
        conv = Conversation(system_prompt="System")
        conv.add_user("q1")
        conv.add_assistant("a1")
        conv.undo()
        assert conv.system_prompt == "System"

    def test_save_and_load(self, tmp_path):
        save_dir = tmp_path / "conversations"
        with mock.patch("freechat_cli.chat.SAVE_DIR", save_dir):
            conv = Conversation(system_prompt="Test", model="openai")
            conv.add_user("Hello")
            conv.add_assistant("Hi!")
            path = conv.save("test_conv.json")
            assert path.exists()

            loaded = Conversation.load("test_conv.json")
            assert loaded.turn_count == 1
            assert loaded.model == "openai"
            assert len(loaded.messages) == 3  # system + user + assistant

    def test_load_old_format(self, tmp_path):
        """Test loading v1 format (bare message list)."""
        save_dir = tmp_path / "conversations"
        save_dir.mkdir()
        filepath = save_dir / "old.json"
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        filepath.write_text(json.dumps(messages), encoding="utf-8")

        with mock.patch("freechat_cli.chat.SAVE_DIR", save_dir):
            loaded = Conversation.load("old.json")
            assert len(loaded.messages) == 3
            assert loaded.turn_count == 1

    def test_load_not_found(self, tmp_path):
        with mock.patch("freechat_cli.chat.SAVE_DIR", tmp_path / "nonexistent"):
            try:
                Conversation.load("missing.json")
                assert False, "Should have raised FileNotFoundError"
            except FileNotFoundError:
                pass

    def test_export_markdown(self, tmp_path):
        save_dir = tmp_path / "conversations"
        with mock.patch("freechat_cli.chat.SAVE_DIR", save_dir):
            conv = Conversation(system_prompt="Test", model="openai")
            conv.add_user("Hello")
            conv.add_assistant("Hi there!")
            path = conv.export_markdown("test_export.md")
            assert path.exists()
            content = path.read_text(encoding="utf-8")
            assert "# FreeChat Conversation" in content
            assert "👤 User" in content
            assert "🤖 Assistant" in content
            assert "Hello" in content

    def test_list_saved_empty(self, tmp_path):
        with mock.patch("freechat_cli.chat.SAVE_DIR", tmp_path / "empty"):
            result = Conversation.list_saved()
            assert result == []

    def test_estimated_tokens(self):
        conv = Conversation()
        conv.add_user("Hello world")
        tokens = conv.estimated_tokens
        assert tokens > 0

    def test_last_response_none(self):
        conv = Conversation()
        conv.add_user("Hello")
        assert conv.last_response is None

    def test_last_response_multiple(self):
        conv = Conversation()
        conv.add_user("q1")
        conv.add_assistant("a1")
        conv.add_user("q2")
        conv.add_assistant("a2")
        assert conv.last_response == "a2"
