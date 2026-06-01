"""FreeChat CLI — Zero-config AI chat in your terminal."""

from .chat import ChatClient, Conversation
from .config import Config

__all__ = ["ChatClient", "Conversation", "Config"]
__version__ = "1.2.0"
