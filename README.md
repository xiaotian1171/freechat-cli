# FreeChat CLI

A zero-config command-line AI chat tool. No API key required — just install and start chatting.

Powered by [Pollinations.ai](https://pollinations.ai) free API by default. Optionally bring your own API key for any OpenAI-compatible endpoint.

## Features

- 🚀 **Zero config** — works out of the box with Pollinations free API
- 🤖 **Multi-model** — switch between openai, mistral, deepseek, qwen, gemini, llama, grok, claude and more
- ⚡ **Streaming** — real-time streaming output with Markdown rendering
- 💬 **Multi-turn** — conversation context preserved across messages
- 💾 **Save/Load** — persist and resume conversations
- 🎨 **Rich UI** — Markdown rendering, syntax highlighting, and themed panels
- 🔧 **Configurable** — custom API endpoints, system prompts, timeout settings
- 📋 **Clipboard** — copy last response with `/copy`

## Installation

### From PyPI (recommended)

```bash
pip install freechat-cli
```

### From source

```bash
git clone https://github.com/xiaotian1171/freechat-cli.git
cd freechat-cli
pip install .
```

### For development

```bash
pip install -e ".[dev]"
```

## Quick Start

Just chat — no setup needed:

```bash
freechat "Explain quantum computing in simple terms"
```

Interactive mode:

```bash
freechat
```

Specify a model:

```bash
freechat -m deepseek "Write a haiku about debugging"
```

## Usage

### One-shot Query

```bash
freechat "your question here"
```

### Interactive Chat

```bash
freechat
```

### Interactive Commands

| Command | Description |
|---------|-------------|
| `/model <name>` | Switch model (auto-saves config) |
| `/system <prompt>` | Set system prompt |
| `/save [file]` | Save conversation |
| `/load <file>` | Load conversation |
| `/clear` | Clear conversation history |
| `/reset` | Reset conversation (alias for /clear) |
| `/models` | List available models |
| `/config` | Show current config |
| `/config save` | Save current config |
| `/copy` | Copy last response to clipboard |
| `/last` | Show last response |
| `/help` | Show commands |
| `/quit` | Exit |

### CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--model`, `-m` | openai | Model to use |
| `--system`, `-s` | none | System prompt |
| `--api-key` | none | API key (not required for Pollinations) |
| `--base-url` | https://text.pollinations.ai/openai | API base URL |
| `--max-history` | 20 | Max conversation turns to keep |
| `--timeout` | 60 | Request timeout in seconds |
| `--no-stream` | false | Disable streaming output |
| `--list-models` | — | List available models and exit |
| `--version`, `-v` | — | Show version |

### Examples

Chat with DeepSeek:
```bash
freechat --model deepseek "Explain transformers architecture"
```

Use a custom provider:
```bash
freechat --base-url https://api.groq.com/openai/v1 --api-key gsk_xxx --model llama33-70b
```

Set a system prompt:
```bash
freechat --system "You are a helpful coding assistant" --model openai
```

Increase timeout for slow models:
```bash
freechat --timeout 120 --model deepseek-r1 "Solve this math problem: ..."
```

## Available Free Models (Pollinations)

Run `/models` in interactive mode or:

```bash
freechat --list-models
```

Common models: `openai`, `openai-large`, `mistral`, `mistral-large`, `deepseek`, `deepseek-r1`, `qwen`, `qwen-coder`, `gemini`, `llama`, `grok`, `claude`

## Configuration

Create `~/.freechat/config.json` for persistent settings:

```json
{
  "model": "openai",
  "system_prompt": "You are a helpful assistant.",
  "max_history": 20,
  "api_key": "",
  "base_url": "https://text.pollinations.ai/openai",
  "timeout": 60
}
```

Or set environment variable:
```bash
export FREECHAT_API_KEY=your-key-here
```

## Clipboard Support

For the `/copy` command, install the optional dependency:

```bash
pip install freechat-cli[clipboard]
```

Or install pyperclip directly:
```bash
pip install pyperclip
```

Without pyperclip, `/copy` will attempt to use system clipboard tools (pbcopy/xclip/clip).

## Requirements

- Python 3.8+
- openai >= 1.0
- rich >= 13.0

## License

MIT
