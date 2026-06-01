"""Tests for utility functions."""

from freechat_cli.utils import (
    estimate_messages_tokens,
    estimate_tokens,
    format_duration,
    retry_with_backoff,
)


class TestEstimateTokens:
    """Test token estimation."""

    def test_empty_string(self):
        assert estimate_tokens("") == 0

    def test_english_text(self):
        tokens = estimate_tokens("Hello, how are you today?")
        assert tokens > 0
        # Should be roughly ~6 tokens for this sentence
        assert 3 <= tokens <= 15

    def test_cjk_text(self):
        tokens = estimate_tokens("你好世界")
        assert tokens > 0
        # CJK characters are estimated at ~1.5 tokens each
        assert tokens >= 4

    def test_mixed_text(self):
        tokens = estimate_tokens("Hello 你好 world 世界")
        assert tokens > 0


class TestEstimateMessagesTokens:
    """Test message-level token estimation."""

    def test_empty_messages(self):
        assert estimate_messages_tokens([]) == 0

    def test_single_message(self):
        messages = [{"role": "user", "content": "Hello"}]
        tokens = estimate_messages_tokens(messages)
        assert tokens > 4  # 4 overhead + content tokens


class TestFormatDuration:
    """Test duration formatting."""

    def test_milliseconds(self):
        assert format_duration(0.5) == "500ms"

    def test_seconds(self):
        assert format_duration(3.2) == "3.2s"

    def test_minutes(self):
        result = format_duration(125.5)
        assert "2m" in result
        assert "5s" in result or "6s" in result  # 125.5s = 2m 5.5s ≈ 2m 6s

    def test_exact_minute(self):
        result = format_duration(60.0)
        assert "1m" in result


class TestRetryWithBackoff:
    """Test retry decorator."""

    def test_no_retry_on_success(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = succeed()
        assert result == "ok"
        assert call_count == 1

    def test_retry_on_failure(self):
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.01, retryable_exceptions=(ValueError,))
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "ok"

        result = fail_then_succeed()
        assert result == "ok"
        assert call_count == 3

    def test_max_retries_exceeded(self):
        @retry_with_backoff(max_retries=1, base_delay=0.01, retryable_exceptions=(ValueError,))
        def always_fail():
            raise ValueError("nope")

        try:
            always_fail()
            assert False, "Should have raised"
        except ValueError as e:
            assert str(e) == "nope"
