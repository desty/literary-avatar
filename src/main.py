"""Avatar — Literary Character AI Agent CLI."""

import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.theme import Theme

from src.character.engine import CharacterEngine
from src.characters import CHARACTERS
from src.generation import get_generation_backend
from src.memory.persistent import PersistentMemory
from src import __version__

theme = Theme({
    "character": "bold cyan",
    "user": "bold green",
    "system": "dim yellow",
})
console = Console(theme=theme)

BANNER = """
    ╔═══════════════════════════════════════════════════════════╗
    ║              AVATAR — Character Agent                    ║
    ║                                                           ║
    ║   Talk with literary characters from classic novels.      ║
    ╚═══════════════════════════════════════════════════════════╝
"""


def select_character() -> str:
    """캐릭터 선택 메뉴."""
    choices = {
        str(index): character_id
        for index, character_id in enumerate(CHARACTERS, start=1)
    }
    console.print()
    console.print("  Choose a character:", style="system")
    console.print()
    for key, character_id in choices.items():
        spec = CHARACTERS[character_id]
        console.print(f"    [{key}] {spec.name}  —  {spec.novel_title}")
    console.print()

    choice = Prompt.ask("  Select", choices=list(choices), default="1")
    return choices[choice]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="avatar",
        description="Timeline-aware chat with literary characters.",
    )
    parser.add_argument(
        "--backend",
        choices=("claude", "mock"),
        help=(
            "Text-generation backend. Defaults to "
            "AVATAR_GENERATION_BACKEND or claude."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Avatar {__version__}",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    generation_backend = get_generation_backend(args.backend)
    console.print(BANNER, style="bold cyan")

    # 캐릭터 선택
    character_id = select_character()
    char_name = CHARACTERS[character_id].name

    console.print(f"\nLoading {char_name}...", style="system")

    try:
        persistent = PersistentMemory(
            character_id,
            generation_backend=generation_backend,
        )
        engine = CharacterEngine(
            character_id,
            persistent_memory=persistent,
            generation_backend=generation_backend,
        )
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    # 이전 대화 기억 표시
    if persistent.episodes:
        last = persistent.episodes[-1]
        console.print(
            f"  [dim](Previous session: {last.get('summary', 'unknown')[:80]}...)[/dim]"
        )

    console.print()
    console.print(Panel(
        f"[character]{char_name}[/character] is ready.\n"
        "Commands: [dim]/reset[/dim] | [dim]/switch[/dim] | "
        "[dim]/memory[/dim] | [dim]/forget[/dim] | [dim]/bdi[/dim] | "
        "[dim]/quit[/dim]",
        title="Ready",
        border_style="cyan",
    ))
    console.print()

    while True:
        try:
            user_input = console.input("[user]You > [/user]")
        except (EOFError, KeyboardInterrupt):
            persistent.end_session()
            console.print("\n[system]Goodbye.[/system]")
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        if user_input.lower() in ("/quit", "/exit"):
            persistent.end_session()
            console.print("[system]Session saved. Goodbye.[/system]")
            break

        if user_input.lower() in ("/reset", "/new"):
            persistent.end_session()
            engine.reset()
            console.print("[system]Conversation reset. Memories saved.[/system]")
            continue

        if user_input.lower() == "/switch":
            persistent.end_session()
            character_id = select_character()
            char_name = CHARACTERS[character_id].name
            console.print(f"\nLoading {char_name}...", style="system")
            persistent = PersistentMemory(
                character_id,
                generation_backend=generation_backend,
            )
            engine = CharacterEngine(
                character_id,
                persistent_memory=persistent,
                generation_backend=generation_backend,
            )
            console.print(f"[character]{char_name}[/character] is ready.\n")
            continue

        if user_input.lower() == "/memory":
            if persistent.episodes:
                console.print(Panel(
                    "\n".join(
                        f"[{ep.get('date', '?')}] {ep.get('summary', '?')}"
                        for ep in persistent.episodes[-5:]
                    ),
                    title="Recent Memories",
                    border_style="dim",
                ))
            else:
                console.print("[system]No memories yet.[/system]")
            user_facts = persistent.user_profile.get("known_facts", [])
            if user_facts:
                console.print(f"  [dim]Known about you: {', '.join(user_facts[:5])}[/dim]")
            continue

        if user_input.lower() == "/forget":
            confirm = Prompt.ask(
                "  Delete all local memories for this character?",
                choices=["y", "n"],
                default="n",
            )
            if confirm == "y":
                persistent.clear_all()
                engine.reset()
                console.print("[system]Local memories deleted.[/system]")
            else:
                console.print("[system]Memory deletion cancelled.[/system]")
            continue

        if user_input.lower() == "/bdi":
            bdi = engine.bdi_state
            console.print(Panel(
                f"Beliefs: {', '.join(bdi.get('beliefs', [])) or 'none'}\n"
                f"Desires: {', '.join(bdi.get('desires', [])) or 'none'}\n"
                f"Intentions: {', '.join(bdi.get('intentions', [])) or 'none'}",
                title=f"{char_name}'s Mental State (BDI)",
                border_style="dim",
            ))
            continue

        if user_input.lower().startswith("/timeline"):
            parts = user_input.split()
            if len(parts) == 1:
                pos = engine.narrative_position
                total = len(engine.arc_snapshots)
                if pos is None:
                    console.print(
                        f"[system]Timeline: full knowledge "
                        f"({total} snapshots available)[/system]"
                    )
                else:
                    console.print(f"[system]Timeline: chapter/story {pos} of {total}[/system]")
                console.print("  [dim]Usage: /timeline 3  (set to chapter 3)[/dim]")
                console.print("  [dim]       /timeline all (reset to full knowledge)[/dim]")
            elif parts[1].lower() == "all":
                engine.set_narrative_position(None)
                console.print("[system]Timeline reset — full knowledge.[/system]")
            else:
                try:
                    n = int(parts[1])
                    engine.set_narrative_position(n)
                    console.print(
                        f"[system]Timeline set to chapter/story {n}. "
                        "Character only knows events up to this point.[/system]"
                    )
                except ValueError:
                    console.print("[system]Usage: /timeline <number> or /timeline all[/system]")
            continue

        if user_input.lower() == "/help":
            console.print(Panel(
                "/reset    — Start new conversation (saves memories)\n"
                "/switch   — Switch character\n"
                "/memory   — Show past session memories\n"
                "/forget   — Delete local memories after confirmation\n"
                "/bdi      — Show character's mental state\n"
                "/timeline — Set narrative position (spoiler control)\n"
                "/quit     — Exit (saves memories)",
                title="Commands",
                border_style="dim",
            ))
            continue

        with console.status("[dim]Thinking...[/dim]", spinner="dots"):
            response = engine.respond(user_input)

        console.print()
        console.print(Panel(
            response,
            title=f"[character]{char_name}[/character]",
            border_style="cyan",
            padding=(1, 2),
        ))
        console.print()


if __name__ == "__main__":
    main()
