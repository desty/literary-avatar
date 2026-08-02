"""Avatar Demo — 제품 기능 쇼케이스 자동 실행."""

import sys

sys.path.insert(0, ".")

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.character.engine import CharacterEngine
from src.character.arc_tracker import load_arc
from src.character.logic_extractor import load_logic

console = Console()


def demo_section(title: str):
    console.print()
    console.rule(f"[bold cyan]{title}[/bold cyan]")
    console.print()


def ask(engine: CharacterEngine, question: str, label: str = ""):
    info = f" [dim]({label})[/dim]" if label else ""
    console.print(f"[green]You:[/green] {question}{info}")
    response = engine.respond(question)
    console.print(Panel(
        response,
        title=f"[cyan]{engine.character_name}[/cyan]",
        border_style="cyan",
        padding=(0, 2),
    ))
    console.print()
    return response


def main():
    console.print(Panel(
        "[bold]Avatar — Literary Character AI Agent[/bold]\n"
        "Timeline-aware character chat demo",
        border_style="bold cyan",
    ))

    # === 1. 캐릭터 전환 ===
    demo_section("1. Two Characters — Holmes & Elizabeth")

    holmes = CharacterEngine("sherlock_holmes")
    elizabeth = CharacterEngine("elizabeth_bennet")

    ask(holmes, "Good evening, Mr. Holmes. How would you describe yourself in one sentence?", "Holmes")
    ask(elizabeth, "Miss Bennet, how would you describe yourself in one sentence?", "Elizabeth")

    # === 2. RAG 기반 소설 지식 ===
    demo_section("2. RAG — Novel-Grounded Knowledge")

    holmes.reset()
    ask(holmes, "Tell me about the Red-Headed League case.", "RAG retrieves relevant story")

    # === 3. 다국어 ===
    demo_section("3. Multilingual Character Voice")

    holmes.reset()
    ask(holmes, "홈즈 씨, 범죄자를 추적할 때 가장 중요한 것은 무엇인가요?", "Korean")

    # === 4. 타임라인 제어 ===
    demo_section("4. Timeline Control")

    console.print("[dim]Setting timeline to position 0 (before any story)...[/dim]")
    holmes.reset()
    holmes.set_narrative_position(0)
    ask(holmes, "Mr. Holmes, what do you think of Irene Adler?", "pos=0: should NOT know")

    console.print("[dim]Setting timeline to position 1 (after 'A Scandal in Bohemia')...[/dim]")
    holmes.reset()
    holmes.set_narrative_position(1)
    ask(holmes, "Mr. Holmes, what do you think of Irene Adler?", "pos=1: should KNOW")

    # === 5. 행동 로직 ===
    demo_section("5. ⭐ Auto-Extracted Behavioral Logic")

    logic = load_logic("sherlock_holmes")
    if logic:
        table = Table(title=f"Holmes's Behavioral Rules ({logic['total_rules']} total)")
        table.add_column("Type", style="cyan", width=15)
        table.add_column("Trigger", width=35)
        table.add_column("Action", width=35)

        for r in logic["rules"][:8]:
            table.add_row(r.get("type", "?"), r["trigger"][:35], r["action"][:35])

        console.print(table)
        console.print(f"\n[dim]Categories: {logic.get('by_category', {})}[/dim]")

    # === 6. 타임라인 스냅샷 ===
    demo_section("6. Timeline Snapshots")

    arc = load_arc("sherlock_holmes")
    if arc:
        table = Table(title="Character Arc Snapshots (12 stories)")
        table.add_column("#", width=3)
        table.add_column("Story", width=30)
        table.add_column("Emotional State", width=40)

        for s in arc:
            table.add_row(
                str(s.get("story_number", "?")),
                s.get("story_title", "?")[:30],
                s.get("emotional_state", "?")[:40],
            )
        console.print(table)

    # === Summary ===
    demo_section("Summary")

    table = Table(title="Avatar System Features")
    table.add_column("Feature", style="bold")
    table.add_column("Status", style="green")
    table.add_column("Detail")

    features = [
        ("Novel Ingestion", "✅", "2 novels, 3,918 dialogues, 73 chapters"),
        ("Character Profiles", "✅", "Big Five, speech patterns, relationships"),
        ("RAG Search", "✅", "Local SQLite FTS5/BM25 index"),
        ("Timeline Control", "Ready", "Story-position-aware responses"),
        ("Behavioral Guidance", "Ready", "Auto-extracted rules from text"),
        ("Theory of Mind", "Ready", "User perspective inference"),
        ("BDI Module", "✅", "Belief-Desire-Intention tracking"),
        ("Persistent Memory", "✅", "Cross-session recall + user profiling"),
        ("Multilingual", "✅", "Korean + English character voice"),
        ("Zero API Cost", "✅", "Claude Code CLI backend"),
    ]

    for name, status, detail in features:
        table.add_row(name, status, detail)

    console.print(table)
    console.print()
    console.print("[bold cyan]Demo complete.[/bold cyan]")


if __name__ == "__main__":
    main()
