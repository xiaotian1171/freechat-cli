"""Interactive and CLI interface for FreeChat."""

import argparse
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from .chat import ChatClient
from .config import Config

console = Console()


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
  /model <name>     Switch model
  /system <prompt>  Set system prompt
  /save [file]      Save conversation
  /load <file>      Load conversation
  /clear            Clear history
  /models           List available models
  /config           Show current config
  /help             Show this help
  /quit             Exit
"""
    console.print(Panel(help_text, title="Help", border_style="blue"))


def handle_command(client: ChatClient, line: str) -> bool:
    """Handle a slash command. Returns False if should exit."""
    parts = line.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd == "/quit" or cmd == "/exit":
        console.print("[dim]Goodbye![/dim]")
        return False
    elif cmd == "/help":
        print_help()
    elif cmd == "/model":
        if not arg:
            console.print(f"Current model: [cyan]{client.config.model}[/cyan]")
        else:
            client.set_model(arg)
            console.print(f"Switched to model: [cyan]{arg}[/cyan]")
    elif cmd == "/system":
        if not arg:
            prompt = client.conversation.system_prompt
            console.print(f"System prompt: {prompt or '(none)'}")
        else:
            client.set_system_prompt(arg)
            console.print(f"System prompt set: [dim]{arg[:80]}...[/dim]" if len(arg) > 80 else f"System prompt set: [dim]{arg}[/dim]")
    elif cmd == "/save":
        try:
            path = client.conversation.save(arg if arg else None)
            console.print(f"Conversation saved: [dim]{path}[/dim]")
        except Exception as e:
            console.print(f"[red]Save failed: {e}[/red]")
    elif cmd == "/load":
        try:
            client.conversation = ChatClient.__new__(ChatClient)
            # Reload conversation
            from .chat import Conversation
            loaded = Conversation.load(arg, max_history=client.config.max_history)
            client.conversation = loaded
            console.print(f"Loaded conversation: [dim]{arg}[/dim] ({loaded.turn_count} turns)")
        except FileNotFoundError as e:
            console.print(f"[red]{e}[/red]")
        except Exception as e:
            console.print(f"[red]Load failed: {e}[/red]")
    elif cmd == "/clear":
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
        info = client.config.to_dict()
        lines = [f"  [bold]{k}[/bold]: {v}" for k, v in info.items()]
        console.print(Panel("\n".join(lines), title="Config", border_style="yellow"))
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

        # Send message and stream response
        console.print()
        try:
            if no_stream:
                response_text = ""
                for chunk in client.chat(user_input, stream=False):
                    response_text += chunk
                console.print(Markdown(response_text))
            else:
                response_text = ""
                with console.status("[dim]Thinking...[/dim]", spinner="dots"):
                    first_chunk = True
                    for chunk in client.chat(user_input, stream=True):
                        if first_chunk:
                            first_chunk = False
                        response_text += chunk
                    # Render full markdown response
                    console.print(Markdown(response_text))

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted.[/yellow]")
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
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming")
    parser.add_argument("--list-models", action="store_true", help="List available models and exit")

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

    client = ChatClient(config=config)

    if args.list_models:
        models = client.list_models()
        for m in models:
            console.print(f"  {m}")
        return

    if args.query:
        # One-shot mode
        try:
            response_text = ""
            for chunk in client.chat(args.query, stream=not args.no_stream):
                if args.no_stream:
                    response_text += chunk
                else:
                    print(chunk, end="", flush=True)
                    response_text += chunk
            if args.no_stream:
                console.print(Markdown(response_text))
            else:
                print()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]", file=sys.stderr)
            sys.exit(1)
    else:
        interactive_mode(client, no_stream=args.no_stream)


if __name__ == "__main__":
    main()
