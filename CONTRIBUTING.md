# Contributing to FreeChat CLI

Thanks for your interest! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/xiaotian1171/freechat-cli.git
cd freechat-cli
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v
```

## Linting

```bash
ruff check .
ruff format .
```

## Making Changes

1. Create a branch: `git checkout -b feature/my-feature`
2. Make your changes
3. Run tests and lint
4. Commit with a clear message
5. Open a pull request

## Code Style

- Follow PEP 8 (enforced by ruff)
- Line length: 100 characters
- Type annotations on all function signatures
- Docstrings on public functions and classes

## Adding a Preset

Add your preset to `freechat_cli/presets.py`:

```python
"my-preset": {
    "system_prompt": "Your system prompt here...",
    "model": "openai",  # optional default model
    "description": "Short description for /preset listing",
},
```

## Reporting Issues

Open an issue at https://github.com/xiaotian1171/freechat-cli/issues with:
- What you expected
- What actually happened
- Steps to reproduce
- Your Python version and OS
