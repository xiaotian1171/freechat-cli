# FreeChat CLI

[![PyPI version](https://img.shields.io/pypi/v/freechat-cli.svg)](https://pypi.org/project/freechat-cli/)
[![Python](https://img.shields.io/pypi/pyversions/freechat-cli.svg)](https://pypi.org/project/freechat-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/xiaotian1171/freechat-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/xiaotian1171/freechat-cli/actions)

Zero-config AI chat in your terminal. No API key required — install and start chatting.

Powered by the [Pollinations.ai](https://pollinations.ai) free API. Optionally bring your own key for any OpenAI-compatible endpoint.

## Demo

```text
$ freechat "Explain quantum computing in one sentence"

⚡ FreeChat — zero-config AI chat in your terminal
  model     openai-fast
  endpoint  https://text.pollinations.ai/

You > Explain quantum computing in one sentence

Quantum computing harnesses quantum-mechanical phenomena such as
superposition and entanglement to process information in ways that
classical computers cannot.

3.2s · ~48 tokens · turn 1
```

## Features

- **Zero config** — works out of the box with the Pollinations free API
- **Streaming** — real-time output with Markdown rendering and a thinking spinner
- **Multi-turn** — conversation context preserved, with token estimation
- **Role presets** — built-in presets: coding, creative, translator, shell, tutor…
- **Model switching** — `/model` at runtime; point `--base-url` at any OpenAI-compatible endpoint to use your own key
- **Persistence** — save/load conversations (JSON), export to Markdown
- **Pipe mode** — pipe input from stdin for scripting
- **Image generation** — generate Pollinations image URLs via `/image`
- **Session stats** — turns, tokens and timing via `/stats`
- **Clipboard** — copy responses with `/copy`
- **Retry** — automatic retry with exponential backoff on rate limits
- **Rich UI** — syntax highlighting, tables, panels, live spinners

> **Note on models:** the anonymous Pollinations free tier currently serves the `openai-fast` model (GPT-OSS 20B). For more models, configure any OpenAI-compatible endpoint with `--base-url` / `--api-key`.

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

Requires Python 3.9+. Optional extras: `pyperclip` (cross-platform clipboard), `tiktoken` (accurate token counts).

## Quick Start

```bash
# Just chat — no setup needed
freechat "Explain quantum computing simply"

# Interactive mode
freechat

# Use a different model
freechat -m openai-fast "Write a haiku about debugging"

# Apply a role preset
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
| `/save [file]` | Save conversation (JSON) |
| `/load <file>` | Load a saved conversation |
| `/export [file]` | Export conversation as Markdown |
| `/history` | List saved conversations |
| `/stats` | Show session statistics |
| `/tokens` | Show estimated token usage |
| `/undo` | Undo the last exchange |
| `/clear` | Clear conversation history |
| `/models` | List available models |
| `/config [save]` | Show or save current config |
| `/last` | Re-print the last response |
| `/copy` | Copy last response to clipboard |
| `/image <desc>` | Generate an image URL |
| `/help` | Show help |
| `/quit` | Exit (`/q`, `/exit`) |

## Configuration

Config is stored at `~/.freechat/config.json`. Every field can be overridden by CLI flags or environment variables.

| Field | Flag | Env var | Default |
|-------|------|---------|---------|
| `model` | `--model` | — | `openai` |
| `base_url` | `--base-url` | — | Pollinations native API |
| `api_key` | `--api-key` | `FREECHAT_API_KEY` | *(none — not needed)* |
| `system_prompt` | `--system` | — | *(none)* |
| `max_history` | `--max-history` | — | `20` |
| `timeout` | `--timeout` | — | `120` |
| `max_retries` | `--max-retries` | — | `2` |

## FAQ

**Is it really free?**
Yes. The default endpoint is Pollinations' anonymous free tier — no account, no key.

**Which models can I use?**
Anonymous access currently maps to `openai-fast` (GPT-OSS 20B). To use other models, bring your own OpenAI-compatible endpoint:

```bash
freechat --base-url https://api.example.com/v1 --api-key sk-... -m my-model
```

**I hit a rate limit (HTTP 429). What now?**
Free-tier rate limits reset over time; FreeChat retries automatically with exponential backoff. Wait a moment and try again.

**Does it work on Windows / macOS / Linux?**
Yes — pure Python with cross-platform dependencies.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Pollinations API error: HTTP 429` | Rate limited — retry later or reduce request frequency |
| `Cannot connect to Pollinations` | Check network/DNS; corporate proxies may block the endpoint |
| Clipboard does nothing | `pip install pyperclip`, or use OS tools (`xclip`/`pbcopy`) |
| Token counts look rough | `pip install tiktoken` for exact counts |

## Development

```bash
git clone https://github.com/xiaotian1171/freechat-cli.git
cd freechat-cli
pip install -e . -r requirements.txt
python -m pytest tests/ -v
```

## License

[MIT](LICENSE) © [xiaotian1171](https://github.com/xiaotian1171)

## Acknowledgements

- [Pollinations.ai](https://pollinations.ai) — free AI APIs powering the default endpoint
- [Rich](https://github.com/Textualize/rich) — terminal UI
