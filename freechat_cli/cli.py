"""Interactive and CLI interface for FreeChat."""

import argparse
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live

from . import __version__
from .chat import ChatClient, Conversation
from .config import Config

console = Console()
err_console = Console(stderr=True)


def print_welcome(client: ChatClient):
    console.print(
        Panel(
            "[bold green]FreeChat CLI[/bold green] — Zero-config AI chat\n"
            f"Model: [cyan]{client.config.model}[/cyan]  |  "
            f"Endpoint: [dim]{client.config.base_url}[/dim]\n"
            "Type [bold]/help[/bold] for commands, [bold]/quit[/bold] to exit",
            title="Welcome",
            border_style="green",
        )
    )


def print_help():
    help_text = """
[bold]Commands:[/bold]
  /model <name>      Switch model (auto-saves config)
  /system <prompt>   Set system prompt
  /save [file]       Save conversation
  /load <file>       Load conversation
  /clear             Clear history
  /reset             Reset conversation (alias for /clear)
  /models            List available models
  /config            Show current config
  /config save       Save current config to file
  /copy              Copy last response to clipboard
  /last              Show last response
  /help              Show this help
  /quit              Exit
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
    # Fallback: use system clipboard tools
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


def handle_command(client: ChatClient, line: str) -> bool:
    """Handle a slash command. Returns False if should exit."""
    parts = line.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd in ("/quit", "/exit", "/q"):
        console.print("[dim]Goodbye![/dim]")
        return False
    elif cmd == "/help":
        print_help()
    elif cmd == "/model":
        if not arg:
            console.print(f"Current model: [cyan]{client.config.model}[/cyan]")
        else:
            client.set_model(arg)
            client.config.save()
            console.print(f"Switched to model: [cyan]{arg}[/cyan] (config saved)")
    elif cmd == "/system":
        if not arg:
            prompt = client.conversation.system_prompt
            console.print(f"System prompt: {prompt or '(none)'}")
        else:
            client.set_system_prompt(arg)
            display = arg[:80] + "..." if len(arg) > 80 else arg
            console.print(f"System prompt set: [dim]{display}[/dim]")
    elif cmd == "/save":
        try:
            path = client.conversation.save(arg if arg else None)
            console.print(f"Conversation saved: [dim]{path}[/dim]")
        except Exception as e:
            console.print(f"[red]Save failed: {e}[/red]")
    elif cmd == "/load":
        try:
            loaded = Conversation.load(arg, max_history=client.config.max_history)
            client.conversation = loaded
            if loaded.model and loaded.model != client.config.model:
                client.set_model(loaded.model)
                console.print(f"Restored model: [cyan]{loaded.model}[/cyan]")
            console.print(f"Loaded conversation: [dim]{arg}[/dim] ({loaded.turn_count} turns)")
        except FileNotFoundError as e:
            console.print(f"[red]{e}[/red]")
        except Exception as e:
            console.print(f"[red]Load failed: {e}[/red]")
    elif cmd in ("/clear", "/reset"):
        client.conversation.clear()
        console.print("[dim]Conversation cleared.[/dim]")
    elif cmd == "/models":
        console.print("[bold]Fetching models...[/bold]")
        try:
            models = client.list_models()
            console.print(Panel("\n".join(f"  • {m}" for m in models), title="Available Models", border_style="cyan"))
        except Exception as e:
            console.print(f"[red]Failed to fetch models: {e}[/red]")
    elif cmd == "/config":
        if arg == "save":
            try:
                client.config.save()
                console.print("[green]Config saved.[/green]")
            except Exception as e:
                console.print(f"[red]Save failed: {e}[/red]")
        else:
            info = client.config.to_dict()
            lines = [f"  [bold]{k}[/bold]: {v}" for k, v in info.items()]
            console.print(Panel("\n".join(lines), title="Config", border_style="yellow"))
    elif cmd == "/copy":
        last = client.conversation.last_response
        if not last:
            console.print("[yellow]No response to copy.[/yellow]")
        elif _copy_to_clipboard(last):
            console.print("[green]Copied last response to clipboard.[/green]")
        else:
            console.print("[yellow]Clipboard not available. Install pyperclip: pip install pyperclip[/yellow]")
    elif cmd == "/last":
        last = client.conversation.last_response
        if not last:
            console.print("[yellow]No response yet.[/yellow]")
        else:
            console.print(Markdown(last))
    else:
        console.print(f"[yellow]Unknown command: {cmd}. Type /help for commands.[/yellow]")

    return True


def interactive_mode(client: ChatClient, no_stream: bool = False):
    """Run interactive chat loop."""
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

        console.print()
        try:
            if no_stream:
                response_text = ""
                for chunk in client.chat(user_input, stream=False):
                    response_text += chunk
                console.print(Markdown(response_text))
            else:
                response_text = ""
                with Live(console=console, refresh_per_second=8, vertical_overflow="visible") as live:
                    for chunk in client.chat(user_input, stream=True):
                        response_text += chunk
                        live.update(Markdown(response_text))
                console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted.[/yellow]")
        except RuntimeError as e:
            console.print(f"[red]{e}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        console.print()


def main():
    parser = argparse.ArgumentParser(
        prog="freechat",
        description="FreeChat CLI — Zero-config AI chat in your terminal",
    )
    parser.add_argument("query", nargs="?", help="One-shot query (interactive mode if omitted)")
    parser.add_argument("--model", "-m", default=None, help="Model name")
    parser.add_argument("--system", "-s", default=None, help="System prompt")
    parser.add_argument("--api-key", default=None, help="API key (not needed for Pollinations)")
    parser.add_argument("--base-url", default=None, help="API base URL")
    parser.add_argument("--max-history", type=int, default=None, help="Max conversation turns")
    parser.add_argument("--timeout", type=int, default=None, help="Request timeout in seconds (default: 60)")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming")
    parser.add_argument("--list-models", action="store_true", help="List available models and exit")
    parser.add_argument("--version", "-v", action="version", version=f"%(prog)s {__version__}")

    args = parser.parse_args()

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

    client = ChatClient(config=config)

    if args.list_models:
        try:
            models = client.list_models()
            for m in models:
                console.print(f"  {m}")
        except Exception as e:
            err_console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
        return

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
