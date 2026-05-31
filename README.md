# FreeChat CLI

A zero-config command-line chat tool powered by free AI APIs. No API key required — just install and start chatting.

Powered by [Pollinations.ai](https://pollinations.ai) free API by default. Optionally bring your own API key for any OpenAI-compatible endpoint.

## Features

- Zero config — works out of the box with Pollinations free API
- Multi-model switching (openai, mistral, deepseek, qwen, gemini, etc.)
- Streaming responses with real-time output
- Multi-turn conversation with context memory
- Conversation save/load
- Markdown rendering in terminal
- Optional custom API key and base URL
- System prompt support

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

Just chat — no setup needed:

```bash
python -m freechat_cli "Explain quantum computing in simple terms"
```

Interactive mode:

```bash
python -m freechat_cli
```

Specify a model:

```bash
python -m freechat_cli --model mistral "Write a haiku about debugging"
```

## Usage

### One-shot Query

```bash
python -m freechat_cli "your question here"
```

### Interactive Chat

```bash
python -m freechat_cli
```

In interactive mode:
- Type your message and press Enter
- `/model <name>` — switch model
- `/system <prompt>` — set system prompt
- `/save [file]` — save conversation
- `/load <file>` — load conversation
- `/clear` — clear conversation history
- `/models` — list available models
- `/help` — show commands
- `/quit` — exit

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--model` | openai | Model to use |
| `--system` | none | System prompt |
| `--api-key` | none | API key (not required for Pollinations) |
| `--base-url` | https://text.pollinations.ai/openai | API base URL |
| `--max-history` | 20 | Max conversation turns to keep |
| `--no-stream` | false | Disable streaming output |

### Examples

Chat with DeepSeek:
```bash
python -m freechat_cli --model deepseek "Explain transformers architecture"
```

Use a custom provider:
```bash
python -m freechat_cli --base-url https://api.groq.com/openai/v1 --api-key gsk_xxx --model llama33-70b
```

Set a system prompt:
```bash
python -m freechat_cli --system "You are a helpful coding assistant" --model openai
```

## Available Free Models (Pollinations)

Run `/models` in interactive mode or:

```bash
python -m freechat_cli --list-models
```

Common models: `openai`, `mistral`, `deepseek`, `qwen`, `gemini`, `llama`, `grok`

## Configuration

Create `~/.freechat/config.json` for persistent settings:

```json
{
  "model": "openai",
  "system_prompt": "You are a helpful assistant.",
  "max_history": 20,
  "api_key": "",
  "base_url": "https://text.pollinations.ai/openai"
}
```

## Requirements

- Python 3.8+
- openai >= 1.0
- rich >= 13.0

## License

MIT
