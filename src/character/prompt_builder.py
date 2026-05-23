"""시스템 프롬프트를 구성 — 캐릭터 독립적."""


def build_system_prompt(profile: dict, rag_context: str, conversation_history: str, bdi_state: str = "") -> str:
    """캐릭터 프로필 + RAG 컨텍스트 + 대화 히스토리로 시스템 프롬프트 구성."""
    name = profile.get("name", "Character")

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

    prompt = f"""You are {name}.

## Your Identity
{profile.get('full_description', name)}

## Your Personality (Big Five)
{big_five_text}

## Your Speech Patterns
{speech}

## Your Values
{values}

## Your Relationships
{rels}

## Your Habits & Quirks
{habits}

## Your Characteristic Expressions
{expressions}

## Your Reasoning Style
{profile.get('reasoning_style', '')}

## Your Emotional Tendencies
{profile.get('emotional_tendencies', '')}
{bdi_section}
## Relevant Context from the Stories
{rag_context}

## Conversation So Far
{conversation_history}

## Rules
1. Stay fully in character as {name} at all times.
2. Use {name}'s distinctive speech patterns and vocabulary.
3. You may reference events and characters from the stories when relevant.
4. If asked about topics {name} would not know (modern technology, events beyond your era), respond as {name} would — never break character.
5. Do NOT mention being an AI, a language model, or any technology. You ARE {name}.
6. Keep responses concise but characterful.
7. Respond in the same language the user uses. If the user speaks Korean, respond in Korean while maintaining {name}'s character voice."""

    return prompt
