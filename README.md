# FreeChat CLI

Zero-config AI chat in your terminal. No API key required — install and start chatting.

Powered by [Pollinations.ai](https://pollinations.ai) free API. Optionally bring your own API key for any OpenAI-compatible endpoint.

## Features

- **Zero config** — works out of the box with Pollinations free API
- **Multi-model** — openai, mistral, deepseek, qwen, gemini, llama, grok, claude and more
- **Streaming** — real-time streaming with Markdown rendering
- **Multi-turn** — conversation context preserved, with token estimation
- **Presets** — built-in role presets: coding, creative, translator, shell, tutor…
- **Persistence** — save/load conversations (JSON), export to Markdown
- **Pipe mode** — pipe input from stdin for scripting
- **Image generation** — generate image URLs via Pollinations
- **Clipboard** — copy responses with `/copy`
- **Retry** — automatic retry with exponential backoff
- **Rich UI** — syntax highlighting, tables, panels, progress info

## Installation

```bash
pip install freechat-cli
```

Or from source:

```bash
git clone https://github.com/xiaotian1171/freechat-cli.git
cd freechat-cli
pip install .
```

## Quick Start

```bash
# Just chat — no setup needed
freechat "Explain quantum computing simply"

# Interactive mode
freechat

# Use a different model
freechat -m deepseek "Write a haiku about debugging"

# Apply a preset
freechat -p coding "Write a Python web scraper"

# Pipe input
echo "Explain this error:" | cat - error.log | freechat
```

## Interactive Commands

| Command | Description |
|---------|-------------|
| `/model <name>` | Switch model (auto-saves config) |
| `/system <prompt>` | Set system prompt |
| `/preset [name]` | List or apply role preset |
| `/save [file]` | Save conversation to JSON |
| `/load <file>` | Load conversation |
| `/export [file]` | Export as Markdown |
| `/history` | List saved conversations |
| `/clear` | Clear conversation history |
| `/reset` | Reset conversation (alias for /clear) |
| `/undo` | Undo last exchange |
| `/models` | List available models |
| `/tokens` | Show estimated token usage |
| `/config` | Show current config |
| `/config save` | Save current config |
| `/copy` | Copy last response to clipboard |
| `/last` | Show last response |
| `/image <desc>` | Generate image URL |
| `/help` | Show commands |
| `/quit` | Exit (also /q, /exit) |

## CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `query` | — | One-shot query (omit for interactive) |
| `--model`, `-m` | openai | Model to use |
| `--system`, `-s` | none | System prompt |
| `--preset`, `-p` | — | Apply a role preset |
| `--api-key` | none | API key (not required for Pollinations) |
| `--base-url` | https://text.pollinations.ai/openai | API base URL |
| `--max-history` | 20 | Max conversation turns to keep |
| `--timeout` | 120 | Request timeout in seconds |
| `--max-retries` | 2 | Max retries on rate limit/timeout |
| `--no-stream` | false | Disable streaming output |
| `--list-models` | — | List available models and exit |
| `--version`, `-v` | — | Show version |

## Role Presets

Built-in presets for common use cases:

| Preset | Description |
|--------|-------------|
| `coding` | Expert coding assistant |
| `creative` | Creative writing partner |
| `translator` | Professional translator (EN↔ZH) |
| `concise` | Brief and direct answers |
| `detailed` | Thorough explanations with examples |
| `shell` | Shell and CLI expert |
| `tutor` | Patient step-by-step tutor |
| `reviewer` | Code review with severity ratings |

```bash
# Apply preset via CLI
freechat -p coding "Refactor this function"

# Or in interactive mode
/preset coding
```

## Examples

```bash
# One-shot with DeepSeek
freechat -m deepseek "Explain transformer architecture"

# Custom provider with API key
freechat --base-url https://api.groq.com/openai/v1 --api-key gsk_xxx -m llama33-70b "Hello"

# Coding preset with system prompt override
freechat -p coding -s "Focus on Python" "Write a FastAPI app"

# Slow model with higher timeout
freechat --timeout 180 -m deepseek-r1 "Solve: prove the Riemann hypothesis"

# Pipe a file into the chat
cat error.log | freechat "What's wrong with this output?"

# Generate an image URL (interactive mode)
/image a cat wearing sunglasses on a beach

# Export conversation to Markdown
/export my-chat.md
```

## Configuration

`~/.freechat/config.json`:

```json
{
  "model": "openai",
  "system_prompt": "",
  "max_history": 20,
  "api_key": "",
  "base_url": "https://text.pollinations.ai/openai",
  "timeout": 120,
  "max_retries": 2
}
```

Environment variable: `FREECHAT_API_KEY`

## Available Free Models

```bash
freechat --list-models
```

Common: `openai`, `openai-large`, `mistral`, `mistral-large`, `deepseek`, `deepseek-r1`, `qwen`, `qwen-coder`, `gemini`, `llama`, `grok`, `claude`

## Optional Dependencies

```bash
# Clipboard support for /copy
pip install freechat-cli[clipboard]

# More accurate token estimation
pip install freechat-cli[token-accuracy]
```

## Development

```bash
git clone https://github.com/xiaotian1171/freechat-cli.git
cd freechat-cli
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check .
ruff format .
```

## Requirements

- Python 3.9+
- openai >= 1.0
- rich >= 13.0

## License

MIT
