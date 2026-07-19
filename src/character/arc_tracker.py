"""챕터별 캐릭터 아크 추적.

소설의 타임라인에 따라 캐릭터의 지식, 감정, 관계 상태를 저장한다.
"""

import json
from pathlib import Path

from src.claude_cli import ClaudeCLIError, call_claude, parse_json_response
from src.characters import get_character

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def generate_arc_snapshots(book_id: str, character_name: str) -> list[dict]:
    """각 스토리/챕터 시점에서의 캐릭터 상태 스냅샷을 생성."""
    processed = DATA_DIR / "processed" / f"{book_id}.json"
    data = json.loads(processed.read_text(encoding="utf-8"))

    stories = data["stories"]
    snapshots = []

    # 누적 컨텍스트: 이전 스토리까지의 핵심 사건
    cumulative_events = []

    # 배치로 처리 (Claude 호출 횟수 줄이기: 3-4개 챕터씩)
    batch_size = 4 if len(stories) > 20 else 3
    for batch_start in range(0, len(stories), batch_size):
        batch = stories[batch_start:batch_start + batch_size]
        batch_summaries = []
        for story in batch:
            # 각 스토리의 핵심 부분만 (앞 1500자 + 뒤 500자)
            text = story["text"]
            if len(text) > 2500:
                excerpt = text[:1500] + "\n[...]\n" + text[-500:]
            else:
                excerpt = text
            batch_summaries.append(
                f"### {story['title']} (#{story['number']})\n{excerpt}"
            )

        previous_context = ""
        if cumulative_events:
            previous_context = "Events so far:\n" + "\n".join(
                f"- {e}" for e in cumulative_events[-10:]
            )

        prompt = f"""Analyze how {character_name}'s character state changes across these chapters/stories.

{previous_context}

{chr(10).join(batch_summaries)}

For EACH chapter/story in this batch, extract the character state at the END of that chapter.
Return JSON array only:

[
  {{
    "story_number": N,
    "story_title": "title",
    "knowledge_gained": ["new things {character_name} learned in this chapter"],
    "emotional_state": "dominant emotion and its cause",
    "relationship_changes": {{"character": "how relationship changed"}},
    "key_events": ["major events involving {character_name}"],
    "character_development": "how {character_name} grew or changed"
  }}
]"""

        try:
            text = call_claude(prompt, timeout=180)
        except ClaudeCLIError:
            continue
        try:
            batch_snapshots = parse_json_response(text, expected_type=list)
            snapshots.extend(batch_snapshots)

            # 누적 이벤트 업데이트
            for snap in batch_snapshots:
                for event in snap.get("key_events", []):
                    cumulative_events.append(event)

            nums = [s.get("story_number", "?") for s in batch_snapshots]
            print(f"  [arc] Processed stories {nums}")

        except ValueError:
            print(f"  [warn] Failed to parse batch starting at {batch_start}")

    return snapshots


def save_arc(snapshots: list[dict], character_id: str) -> Path:
    """캐릭터 아크 스냅샷을 저장."""
    arc_dir = DATA_DIR / "arcs"
    arc_dir.mkdir(parents=True, exist_ok=True)

    output_path = arc_dir / f"{character_id}.json"
    output_path.write_text(
        json.dumps(snapshots, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[saved] {output_path} ({len(snapshots)} snapshots)")
    return output_path


def load_arc(character_id: str) -> list[dict]:
    """저장된 아크 스냅샷을 로드."""
    path = DATA_DIR / "arcs" / f"{character_id}.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def get_state_at_position(snapshots: list[dict], position: int) -> dict:
    """특정 스토리/챕터 시점까지의 누적 캐릭터 상태를 반환."""
    if not snapshots:
        return {}

    cumulative = {
        "knowledge": [],
        "emotional_state": "",
        "relationships": {},
        "key_events": [],
        "development_arc": [],
    }

    for snap in snapshots:
        if snap.get("story_number", 0) > position:
            break

        cumulative["knowledge"].extend(snap.get("knowledge_gained", []))
        cumulative["emotional_state"] = snap.get("emotional_state", "")
        for char, change in snap.get("relationship_changes", {}).items():
            cumulative["relationships"][char] = change
        cumulative["key_events"].extend(snap.get("key_events", []))
        dev = snap.get("character_development", "")
        if dev:
            cumulative["development_arc"].append(dev)

    return cumulative


def get_unknown_at_position(snapshots: list[dict], position: int) -> list[str]:
    """현재 시점 이후에 알게 될 인물/사건을 추출."""
    unknown = []
    for snap in snapshots:
        if snap.get("story_number", 0) <= position:
            continue
        for k in snap.get("knowledge_gained", []):
            unknown.append(k)
        for char in snap.get("relationship_changes", {}):
            unknown.append(f"the person named {char}")
    return unknown


def format_arc_for_prompt(state: dict, max_position: int, snapshots: list[dict] = None) -> str:
    """아크 상태를 프롬프트에 삽입할 문자열로 포맷."""
    parts = [f"[Your knowledge and state as of story/chapter {max_position}]"]

    if state.get("knowledge"):
        parts.append("What you know:\n" + "\n".join(f"  - {k}" for k in state["knowledge"][-15:]))

    if state.get("emotional_state"):
        parts.append(f"Your current emotional state: {state['emotional_state']}")

    if state.get("relationships"):
        parts.append("Current relationships:\n" + "\n".join(
            f"  - {c}: {r}" for c, r in state["relationships"].items()
        ))

    if state.get("key_events"):
        parts.append("Events you've experienced:\n" + "\n".join(
            f"  - {e}" for e in state["key_events"][-10:]
        ))

    # 아직 모르는 것 명시
    if snapshots:
        unknown = get_unknown_at_position(snapshots, max_position)
        if unknown:
            parts.append(
                "## Things you do NOT know yet (you have NOT encountered these):\n"
                + "\n".join(f"  - {u}" for u in unknown[:20])
            )

    parts.append(
        f"\n## CRITICAL TIMELINE CONSTRAINT — OVERRIDE ALL OTHER KNOWLEDGE ##\n"
        f"You exist at story/chapter {max_position}. This is a HARD constraint.\n"
        f"You must ROLEPLAY as if you truly have not experienced anything beyond this point.\n"
        f"When someone mentions a name, case, or event from your 'do NOT know' list above:\n"
        f"  → You MUST say you do not recognize the name or know of such a matter.\n"
        f"  → Do NOT describe, discuss, or reference anything about them.\n"
        f"  → Respond with genuine unfamiliarity: 'That name means nothing to me.'\n"
        f"This constraint OVERRIDES your general knowledge. Act as if those events have not happened."
    )

    return "\n\n".join(parts)


if __name__ == "__main__":
    import sys
    char_id = sys.argv[1] if len(sys.argv) > 1 else "sherlock_holmes"
    spec = get_character(char_id)

    print(f"[arc] Generating arc snapshots for {spec.name}...")
    snapshots = generate_arc_snapshots(spec.book_id, spec.name)
    save_arc(snapshots, char_id)
