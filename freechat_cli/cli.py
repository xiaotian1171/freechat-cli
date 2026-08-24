"""Interactive and CLI interface for FreeChat.

Features: real-time streaming, pipe mode, presets, image generation,
conversation export, token estimation, and more.
"""

import argparse
import sys
import time

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table

from . import __version__
from .chat import ChatClient, Conversation
from .config import Config
from .presets import PRESETS
from .utils import estimate_messages_tokens, format_duration

console = Console()
err_console = Console(stderr=True)


# ── UI helpers ──────────────────────────────────────────────────


def print_welcome(client: ChatClient) -> None:
    """Print the welcome banner with a session info table."""
    banner = Panel(
        "[bold green]⚡ FreeChat[/bold green] [dim]— zero-config AI chat in your terminal[/dim]\n"
        "Type [bold]/help[/bold] for commands · [bold]/quit[/bold] to exit",
        title=f"[bold]v{__version__}[/bold]",
        border_style="green",
        padding=(0, 2),
    )
    console.print(banner)

    info = Table(show_header=False, box=None, padding=(0, 1))
    info.add_column(style="dim", justify="right")
    info.add_column()
    info.add_row("model", f"[cyan]{client.config.model}[/cyan]")
    info.add_row("endpoint", f"[dim]{client.config.base_url}[/dim]")
    if client.conversation.system_prompt:
        sp = client.conversation.system_prompt
        display = sp[:60] + "…" if len(sp) > 60 else sp
        info.add_row("system", f"[dim]{display}[/dim]")
    console.print(info)
    console.print()


def print_help() -> None:
    help_text = """
[bold]Conversation[/bold]
  /model <name>      Switch model (auto-saves)
  /system <prompt>   Set system prompt
  /preset [name]     List or apply role preset
  /clear             Clear history
  /reset             Reset conversation (alias for /clear)
  /undo              Undo last exchange

[bold]Persistence[/bold]
  /save [file]       Save conversation (JSON)
  /load <file>       Load conversation
  /export [file]     Export as Markdown
  /history           List saved conversations

[bold]Info[/bold]
  /models            List available models
  /config            Show current config
  /config save       Save current config
  /stats             Show session statistics
  /tokens            Show estimated token usage
  /last              Show last response
  /copy              Copy last response to clipboard

[bold]Image[/bold]
  /image <desc>      Generate image URL via Pollinations

[bold]General[/bold]
  /help              Show this help
  /quit              Exit  (also /q, /exit)
"""
    console.print(Panel(help_text, title="Help", border_style="blue"))


def _copy_to_clipboard(text: str) -> bool:
    """Try to copy text to clipboard. Returns True on success."""
    try:
        import pyperclip

        pyperclip.copy(text)
        return True
    except ImportError:
        pass
    try:
        import subprocess

        if sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=text.encode(), check=True)
        elif sys.platform == "linux":
            subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode(), check=True)
        elif sys.platform == "win32":
            subprocess.run(["clip"], input=text.encode(), check=True)
        else:
            return False
        return True
    except Exception:
        return False


# ── Command handler ─────────────────────────────────────────────


def handle_command(client: ChatClient, line: str) -> bool:
    """Handle a slash command. Returns False if should exit."""
    parts = line.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    # ── Exit ────────────────────────────────────────────────
    if cmd in ("/quit", "/exit", "/q"):
        console.print("[dim]Goodbye![/dim]")
        return False

    # ── Help ────────────────────────────────────────────────
    elif cmd == "/help":
        print_help()

    # ── Model ───────────────────────────────────────────────
    elif cmd == "/model":
        if not arg:
            console.print(f"Current model: [cyan]{client.config.model}[/cyan]")
        else:
            client.set_model(arg)
            client.config.save()
            console.print(f"Switched to model: [cyan]{arg}[/cyan] (config saved)")

    # ── System prompt ───────────────────────────────────────
    elif cmd == "/system":
        if not arg:
            prompt = client.conversation.system_prompt
            console.print(f"System prompt: {prompt or '(none)'}")
        else:
            client.set_system_prompt(arg)
            display = arg[:80] + "..." if len(arg) > 80 else arg
            console.print(f"System prompt set: [dim]{display}[/dim]")

    # ── Preset ──────────────────────────────────────────────
    elif cmd == "/preset":
        if not arg:
            table = Table(title="Available Presets", border_style="magenta")
            table.add_column("Name", style="cyan")
            table.add_column("Description")
            table.add_column("Model", style="dim")
            for name, data in PRESETS.items():
                table.add_row(name, data.get("description", ""), data.get("model", ""))
            console.print(table)
            console.print("[dim]Use /preset <name> to apply[/dim]")
        else:
            name = arg.lower()
            if name not in PRESETS:
                available = ", ".join(sorted(PRESETS.keys()))
                console.print(f"[red]Unknown preset: {name}[/red]")
                console.print(f"[dim]Available: {available}[/dim]")
            else:
                preset = PRESETS[name]
                client.set_system_prompt(preset["system_prompt"])
                if preset.get("model"):
                    client.set_model(preset["model"])
                    client.config.save()
                desc = preset.get("description", "")
                console.print(f"Applied preset: [cyan]{name}[/cyan] — {desc}")

    # ── Save ────────────────────────────────────────────────
    elif cmd == "/save":
        try:
            path = client.conversation.save(arg if arg else None)
            console.print(f"Conversation saved: [dim]{path}[/dim]")
        except Exception as e:
            console.print(f"[red]Save failed: {e}[/red]")

    # ── Load ────────────────────────────────────────────────
    elif cmd == "/load":
        try:
            loaded = Conversation.load(arg, max_history=client.config.max_history)
            client.conversation = loaded
            if loaded.model and loaded.model != client.config.model:
                client.set_model(loaded.model)
                console.print(f"Restored model: [cyan]{loaded.model}[/cyan]")
            console.print(f"Loaded: [dim]{arg}[/dim] ({loaded.turn_count} turns)")
        except FileNotFoundError as e:
            console.print(f"[red]{e}[/red]")
        except Exception as e:
            console.print(f"[red]Load failed: {e}[/red]")

    # ── Export ──────────────────────────────────────────────
    elif cmd == "/export":
        try:
            path = client.conversation.export_markdown(arg if arg else None)
            console.print(f"Exported to markdown: [dim]{path}[/dim]")
        except Exception as e:
            console.print(f"[red]Export failed: {e}[/red]")

    # ── History ─────────────────────────────────────────────
    elif cmd == "/history":
        saved = Conversation.list_saved()
        if not saved:
            console.print("[dim]No saved conversations.[/dim]")
        else:
            table = Table(title="Saved Conversations", border_style="cyan")
            table.add_column("File", style="cyan")
            table.add_column("Turns", justify="right")
            table.add_column("Model", style="dim")
            table.add_column("Saved")
            for item in saved:
                table.add_row(
                    item["filename"],
                    str(item["turns"]),
                    item["model"],
                    item["saved_at"],
                )
            console.print(table)

    # ── Clear / Reset ───────────────────────────────────────
    elif cmd in ("/clear", "/reset"):
        client.conversation.clear()
        console.print("[dim]Conversation cleared.[/dim]")

    # ── Undo ────────────────────────────────────────────────
    elif cmd == "/undo":
        removed = client.conversation.undo()
        if removed:
            console.print(f"[dim]Undid last exchange ({removed} message(s) removed).[/dim]")
        else:
            console.print("[yellow]Nothing to undo.[/yellow]")

    # ── Models ──────────────────────────────────────────────
    elif cmd == "/models":
        console.print("[bold]Fetching models...[/bold]")
        try:
            models = client.list_models()
            model_list = "\n".join(f"  • {m}" for m in models)
            console.print(Panel(model_list, title="Available Models", border_style="cyan"))
        except Exception as e:
            console.print(f"[red]Failed to fetch models: {e}[/red]")

    # ── Config ──────────────────────────────────────────────
    elif cmd == "/config":
        if arg == "save":
            try:
                client.config.save()
                console.print("[green]Config saved.[/green]")
            except Exception as e:
                console.print(f"[red]Save failed: {e}[/red]")
        else:
            info = client.config.to_dict(partial=True)
            lines = [f"  [bold]{k}[/bold]: {v}" for k, v in info.items()]
            console.print(Panel("\n".join(lines), title="Config", border_style="yellow"))

    # ── Stats ───────────────────────────────────────────────
    elif cmd == "/stats":
        conv = client.conversation
        ctx_tokens = estimate_messages_tokens(conv.get_context())
        total_tokens = estimate_messages_tokens(conv.messages)
        stats = Table(show_header=False, box=None, padding=(0, 1))
        stats.add_column(style="dim", justify="right")
        stats.add_column()
        stats.add_row("model", f"[cyan]{conv.model or client.config.model}[/cyan]")
        stats.add_row("created", f"[dim]{conv.created_at}[/dim]")
        stats.add_row("turns", str(conv.turn_count))
        stats.add_row("messages", str(len(conv.messages)))
        stats.add_row("context", f"[cyan]{ctx_tokens}[/cyan] tokens")
        stats.add_row("total", f"[cyan]{total_tokens}[/cyan] tokens")
        console.print(Panel(stats, title="Session Stats", border_style="blue"))

    # ── Tokens ──────────────────────────────────────────────
    elif cmd == "/tokens":
        ctx = client.conversation.get_context()
        ctx_tokens = estimate_messages_tokens(ctx)
        all_tokens = estimate_messages_tokens(client.conversation.messages)
        console.print(
            f"Context: [cyan]{ctx_tokens}[/cyan] tokens "
            f"({len(ctx)} messages)  |  "
            f"Total: [cyan]{all_tokens}[/cyan] tokens "
            f"({len(client.conversation.messages)} messages)"
        )

    # ── Copy ────────────────────────────────────────────────
    elif cmd == "/copy":
        last = client.conversation.last_response
        if not last:
            console.print("[yellow]No response to copy.[/yellow]")
        elif _copy_to_clipboard(last):
            console.print("[green]Copied last response to clipboard.[/green]")
        else:
            console.print("[yellow]Clipboard unavailable. Install: pip install pyperclip[/yellow]")

    # ── Last ────────────────────────────────────────────────
    elif cmd == "/last":
        last = client.conversation.last_response
        if not last:
            console.print("[yellow]No response yet.[/yellow]")
        else:
            console.print(Markdown(last))

    # ── Image ───────────────────────────────────────────────
    elif cmd == "/image":
        if not arg:
            console.print("[yellow]Usage: /image <description>[/yellow]")
        else:
            try:
                url = client.generate_image_url(arg)
                console.print(f"Image URL: [link={url}]{url}[/link]")
            except Exception as e:
                console.print(f"[red]Image generation failed: {e}[/red]")

    # ── Unknown ─────────────────────────────────────────────
    else:
        console.print(f"[yellow]Unknown command: {cmd}. Type /help for commands.[/yellow]")

    return True


# ── Interactive mode ────────────────────────────────────────────


def interactive_mode(client: ChatClient, no_stream: bool = False) -> None:
    """Run interactive chat loop with real-time streaming."""
    print_welcome(client)

    while True:
        try:
            user_input = console.input("[bold green]You[/bold green] > ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            if not handle_command(client, user_input):
                break
            continue

        # ── Send message and stream response ────────────────
        console.print()
        try:
            start_time = time.time()

            if no_stream:
                response_text = ""
                with console.status("[dim]Thinking…[/dim]", spinner="dots"):
                    for chunk in client.chat(user_input, stream=False):
                        response_text += chunk
                console.print(Markdown(response_text))
            else:
                response_text = ""
                with Live(
                    console=console, refresh_per_second=10, vertical_overflow="visible"
                ) as live:
                    live.update(Spinner("dots", text="[dim]Thinking…[/dim]"))
                    for chunk in client.chat(user_input, stream=True):
                        response_text += chunk
                        live.update(Markdown(response_text))
                console.print()

            elapsed = time.time() - start_time
            tokens = estimate_messages_tokens(
                [m for m in client.conversation.messages[-2:] if m["role"] == "assistant"]
            )
            console.print(
                f"[dim]{format_duration(elapsed)} · ~{tokens} tokens · "
                f"turn {client.conversation.turn_count}[/dim]"
            )

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted.[/yellow]")
        except RuntimeError as e:
            console.print(f"[red]{e}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        console.print()


# ── CLI entry point ─────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="freechat",
        description="FreeChat CLI — Zero-config AI chat in your terminal",
    )
    parser.add_argument("query", nargs="?", help="One-shot query (interactive mode if omitted)")
    parser.add_argument("--model", "-m", default=None, help="Model name")
    parser.add_argument("--system", "-s", default=None, help="System prompt")
    parser.add_argument("--preset", "-p", default=None, help="Apply a role preset")
    parser.add_argument("--api-key", default=None, help="API key (not needed for Pollinations)")
    parser.add_argument("--base-url", default=None, help="API base URL")
    parser.add_argument("--max-history", type=int, default=None, help="Max conversation turns")
    parser.add_argument(
        "--timeout", type=int, default=None, help="Request timeout in seconds (default: 120)"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=None,
        help="Max retries on rate limit/timeout (default: 2)",
    )
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming")
    parser.add_argument("--list-models", action="store_true", help="List available models and exit")
    parser.add_argument("--version", "-v", action="version", version=f"%(prog)s {__version__}")

    args = parser.parse_args()

    # Load config and apply CLI overrides
    config = Config.load()
    if args.model:
        config.model = args.model
    if args.system:
        config.system_prompt = args.system
    if args.api_key:
        config.api_key = args.api_key
    if args.base_url:
        config.base_url = args.base_url
    if args.max_history:
        config.max_history = args.max_history
    if args.timeout:
        config.timeout = args.timeout
    if args.max_retries is not None:
        config.max_retries = args.max_retries

    # Apply preset (overrides system prompt and model)
    if args.preset:
        if args.preset.lower() not in PRESETS:
            err_console.print(
                f"[red]Unknown preset: {args.preset}. "
                f"Available: {', '.join(sorted(PRESETS.keys()))}[/red]"
            )
            sys.exit(1)
        preset = PRESETS[args.preset.lower()]
        config.system_prompt = preset["system_prompt"]
        if preset.get("model") and not args.model:
            config.model = preset["model"]

    client = ChatClient(config=config)

    # ── Pipe mode: read from stdin ──────────────────────────
    if not sys.stdin.isatty() and not args.query:
        stdin_text = sys.stdin.read().strip()
        if stdin_text:
            args.query = stdin_text

    # ── List models ─────────────────────────────────────────
    if args.list_models:
        try:
            models = client.list_models()
            for m in models:
                console.print(f"  {m}")
        except Exception as e:
            err_console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
        return

    # ── One-shot mode ───────────────────────────────────────
    if args.query:
        try:
            response_text = ""
            for chunk in client.chat(args.query, stream=not args.no_stream):
                response_text += chunk
                if not args.no_stream:
                    print(chunk, end="", flush=True)
            if args.no_stream:
                console.print(Markdown(response_text))
            else:
                print()
        except RuntimeError as e:
            err_console.print(f"[red]{e}[/red]")
            sys.exit(1)
        except Exception as e:
            err_console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
    else:
        interactive_mode(client, no_stream=args.no_stream)


if __name__ == "__main__":
    main()
