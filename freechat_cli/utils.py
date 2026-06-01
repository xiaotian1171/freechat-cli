"""Utility functions: token estimation, retry logic, export helpers."""

import functools
import time
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def estimate_tokens(text: str) -> int:
    """Estimate token count for text.

    Uses tiktoken with cl100k_base encoding if available, otherwise
    falls back to a heuristic (~4 chars/token English, ~1.5 chars/token CJK).
    """
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except (ImportError, Exception):
        pass
    # Heuristic: CJK chars cost more tokens
    cjk = sum(
        1
        for c in text
        if "\u4e00" <= c <= "\u9fff" or "\u3400" <= c <= "\u4dbf" or "\u3000" <= c <= "\u303f"
    )
    other = len(text) - cjk
    return int(cjk * 1.5 + other * 0.25)


def estimate_messages_tokens(messages: list) -> int:
    """Estimate total tokens for a list of chat messages."""
    total = 0
    for msg in messages:
        # Each message has ~4 tokens overhead (role, separators)
        total += 4
        total += estimate_tokens(msg.get("content", ""))
    return total


def retry_with_backoff(
    max_retries: int = 2,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retryable_exceptions: tuple = (Exception,),
) -> Callable[[F], F]:
    """Decorator: retry a function with exponential backoff.

    Args:
        max_retries: Maximum number of retries (total attempts = max_retries + 1).
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay between retries.
        retryable_exceptions: Exception types that trigger a retry.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = base_delay
            last_exc: Exception = RuntimeError("unreachable")
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as exc:
                    last_exc = exc
                    if attempt < max_retries:
                        time.sleep(min(delay, max_delay))
                        delay *= 2
            raise last_exc

        return wrapper  # type: ignore[return-value]

    return decorator


def format_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-readable string."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.0f}s"
