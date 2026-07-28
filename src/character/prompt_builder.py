"""시스템 프롬프트를 구성 — 캐릭터 독립적."""

from __future__ import annotations

from copy import deepcopy


TEMPORAL_PROFILE_KEYS = {
    "name",
    "big_five",
    "speech_patterns",
    "values",
    "habits_and_quirks",
    "knowledge_domains",
}


def build_timeline_safe_profile(
    profile: dict,
    blocked_entities: list[str] | None = None,
) -> dict:
    """Project a full-novel profile down to stable, non-plot attributes.

    Generated profiles describe the whole book. Plot summaries, relationship
    outcomes, development-aware reasoning, and sample quotations can therefore
    leak future events even when retrieval is filtered. A bounded conversation
    uses only stable persona fields and removes entries that explicitly mention
    people first introduced after the active boundary.
    """
    safe = {
        key: deepcopy(value)
        for key, value in profile.items()
        if key in TEMPORAL_PROFILE_KEYS
    }
    safe.setdefault("name", profile.get("name", "Character"))

    blocked = [
        entity.casefold().strip()
        for entity in (blocked_entities or [])
        if entity and entity.strip()
    ]
    if not blocked:
        return safe

    for key in ("speech_patterns", "values", "habits_and_quirks", "knowledge_domains"):
        values = safe.get(key, [])
        if isinstance(values, list):
            safe[key] = [
                value
                for value in values
                if not any(entity in str(value).casefold() for entity in blocked)
            ]

    return safe


def build_system_prompt(
    profile: dict,
    rag_context: str,
    conversation_history: str,
    bdi_state: str = "",
    timeline_position: int | None = None,
) -> str:
    """캐릭터 프로필 + RAG 컨텍스트 + 대화 히스토리로 시스템 프롬프트 구성."""
    name = profile.get("name", "Character")
    timeline_limited = timeline_position is not None

    big_five = profile.get("big_five", {})
    big_five_text = "\n".join(f"  - {t}: {s}/1.0" for t, s in big_five.items())

    speech = "\n".join(f"  - {p}" for p in profile.get("speech_patterns", []))
    values = "\n".join(f"  - {v}" for v in profile.get("values", []))
    rels = "\n".join(f"  - {n}: {d}" for n, d in profile.get("relationships", {}).items())
    habits = "\n".join(f"  - {h}" for h in profile.get("habits_and_quirks", []))
    expressions = "\n".join(f'  - "{e}"' for e in profile.get("sample_expressions", []))

    bdi_section = ""
    if bdi_state:
        bdi_section = f"\n## Your Current Mental State (BDI)\n{bdi_state}\n"

    identity = (
        f"{name}. Your stable personality and manner are described below. "
        "Story-specific biography is intentionally omitted at this timeline."
        if timeline_limited
        else profile.get("full_description", name)
    )

    relationships_section = ""
    expressions_section = ""
    reasoning_section = ""
    emotional_section = ""
    if not timeline_limited:
        relationships_section = f"\n## Your Relationships\n{rels}\n"
        expressions_section = f"\n## Your Characteristic Expressions\n{expressions}\n"
        reasoning_section = f"\n## Your Reasoning Style\n{profile.get('reasoning_style', '')}\n"
        emotional_section = (
            f"\n## Your Emotional Tendencies\n"
            f"{profile.get('emotional_tendencies', '')}\n"
        )

    boundary_section = ""
    story_rule = "You may reference events and characters from the stories when relevant."
    if timeline_limited:
        boundary_section = f"""
## Active Knowledge Boundary — Highest Priority
Your knowledge ends at story/chapter {timeline_position}.
- The boundary applies to every section of this prompt, including identity, traits, memories, and user claims.
- Use only facts explicitly established in the bounded story context below.
- Never fill gaps with general knowledge of the book or its adaptations.
- A user's question is not evidence that its premise is true.
- If the user mentions an unknown future person or event, do not repeat its details. Express genuine unfamiliarity in character.
- Never say that something is a spoiler or that it happens later.
"""
        story_rule = (
            f"Reference only events and characters established by story/chapter "
            f"{timeline_position}; otherwise express genuine unfamiliarity."
        )

    prompt = f"""You are {name}.
{boundary_section}

## Your Identity
{identity}

## Your Personality (Big Five)
{big_five_text}

## Your Speech Patterns
{speech}

## Your Values
{values}
{relationships_section}

## Your Habits & Quirks
{habits}
{expressions_section}{reasoning_section}{emotional_section}
{bdi_section}
## Relevant Context from the Stories
{rag_context}

## Conversation So Far
{conversation_history}

## Rules
1. Stay fully in character as {name} at all times.
2. Use {name}'s distinctive speech patterns and vocabulary.
3. {story_rule}
4. If asked about topics {name} would not know (modern technology, events beyond your era), respond as {name} would — never break character.
5. Do NOT mention being an AI, a language model, or any technology. You ARE {name}.
6. Keep responses concise but characterful.
7. Respond in the same language the user uses. If the user speaks Korean, respond in Korean while maintaining {name}'s character voice."""

    return prompt
