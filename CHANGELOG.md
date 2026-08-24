# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.3.0] - 2026-08-24

### Added
- **`/stats` command** — session statistics panel (model, turns, messages, token usage)
- **Thinking spinner** — animated indicator while waiting for the first streamed chunk (reasoning models can take a moment before visible output)
- **Status indicator** for `--no-stream` mode
- **Native endpoint test suite** (`tests/test_chat.py`) — SSE parsing, plain-text parsing, request shape, legacy URL detection; no network required
- README overhaul: badges, demo, full command/config reference, FAQ and troubleshooting

### Changed
- Default endpoint switched to the native Pollinations API (`https://text.pollinations.ai/`) per app review feedback, replacing the OpenAI-compatible `/openai` path
- Native endpoint support implemented without the OpenAI SDK: streaming (SSE), non-streaming, model listing, retry with backoff
- Anonymous free tier currently serves the `openai-fast` model (GPT-OSS 20B); point `--base-url` at any OpenAI-compatible endpoint for more

## [1.2.0] - 2026-06-02

### Added
- **Role presets** (`/preset` command, `--preset` CLI flag) — 8 built-in presets: coding, creative, translator, concise, detailed, shell, tutor, reviewer
- **Pipe/stdin mode** — pipe text into freechat for one-shot queries: `echo "text" | freechat`
- **Image generation** — `/image <desc>` generates Pollinations image URLs
- **Conversation export** — `/export [file]` saves conversation as Markdown
- **Conversation history** — `/history` lists saved conversations with metadata
- **Undo** — `/undo` removes the last exchange
- **Token estimation** — `/tokens` shows estimated token usage for context and total
- **Retry with backoff** — automatic retry on rate limit and timeout errors (configurable via `--max-retries`)
- **Response timing** — shows elapsed time and token count after each response
- **New CLI flags** — `--preset`, `--max-retries`
- **New module: `utils.py`** — token estimation, retry decorator, duration formatting
- **New module: `presets.py`** — built-in role presets
- **Unit tests** — pytest suite for config, conversation, and utils (30+ test cases)
- **CI/CD** — GitHub Actions workflow: lint (ruff), test (multi-Python), build, PyPI publish on tag
- **CONTRIBUTING.md**
- Optional `token-accuracy` extra for tiktoken-based estimation

### Changed
- Default timeout increased from 60s to 120s
- Minimum Python version: 3.9 (was 3.8)
- `/models` fallback list updated with more Pollinations models
- Streaming output uses Rich Live with 10fps refresh
- `pyproject.toml` now includes PyPI publishing config, ruff lint settings, pytest config
- README completely rewritten with comprehensive docs

### Fixed
- `/load` no longer creates broken ChatClient shell object
- Streaming renders progressively instead of waiting for full response
- Rate limit and timeout errors now retry automatically before failing
- Conversation load supports both v1 (bare list) and v2 (with metadata) formats

## [1.1.0] - 2026-06-02

### Added
- `pyproject.toml` for pip installable package with `freechat` entry point
- `--version` flag to show version
- `--timeout` flag for request timeout (default: 60s)
- `/copy` command to copy last response to clipboard
- `/last` command to show last response
- `/reset` command (alias for /clear)
- `/config save` subcommand to persist config
- `/model` now auto-saves config after switching
- `/q` as shortcut for /quit
- Conversation save now includes metadata (model, timestamps, turn count)
- Rich Live display for real-time streaming output
- Better error handling: rate limit, timeout, connection errors with friendly messages
- Optional clipboard dependency (`pip install freechat-cli[clipboard]`)
- CHANGELOG.md

### Fixed
- `/load` command no longer creates broken ChatClient shell object (`ChatClient.__new__`)
- Streaming output now renders progressively instead of waiting for full response
- One-shot mode no longer mixes print() and rich output
- Conversation load supports both old (bare list) and new (with metadata) formats

## [1.0.0] - 2026-05-XX

### Added
- Initial release
- Zero-config Pollinations.ai integration
- Multi-model switching
- Streaming responses
- Multi-turn conversation
- Save/load conversations
- Markdown rendering
- System prompt support
