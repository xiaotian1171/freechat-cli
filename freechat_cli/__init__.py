"""FreeChat CLI — Zero-config AI chat in your terminal."""

from ._version import __version__
from .chat import ChatClient, Conversation
from .config import Config

__all__ = ["ChatClient", "Conversation", "Config", "__version__"]
