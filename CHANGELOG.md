# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

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
- Better error handling: rate limit, timeout, connection errors
- Optional clipboard dependency (`pip install freechat-cli[clipboard]`)
- CHANGELOG.md

### Fixed
- `/load` command no longer creates broken ChatClient shell object
- Streaming output now renders progressively instead of waiting for full response
- One-shot mode no longer mixes print() and rich output
- Conversation load supports both old (bare list) and new (with metadata) formats

### Changed
- Default model list fallback updated with more Pollinations models
- Version bumped to 1.1.0

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
