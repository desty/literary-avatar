"""사용자 관점 추론.

캐릭터가 다른 캐릭터/사용자의 믿음을 추론해 응답 깊이를 조절한다.

예시:
- 홈즈가 "왓슨이라면 이렇게 생각했을 것이다"라고 추론
- 홈즈가 사용자의 지식 수준을 파악하여 설명 깊이 조절
"""

from src.claude_cli import ClaudeCLIError, call_claude, parse_json_response


def infer_other_perspective(
    character_name: str,
    other_name: str,
    topic: str,
    character_profile: dict,
    conversation_context: str,
) -> dict:
    """캐릭터가 다른 캐릭터/사용자의 관점을 추론."""

    prompt = f"""You are analyzing how {character_name} would reason about {other_name}'s perspective.

{character_name}'s personality: {character_profile.get('reasoning_style', '')}

Topic: {topic}
Recent conversation: {conversation_context[-500:]}

From {character_name}'s perspective, infer:
1. What does {character_name} think {other_name} believes about this topic?
2. What does {character_name} think {other_name} does NOT know?
3. How would {character_name} adjust their communication based on this assessment?

Return JSON only:
{{"other_likely_believes": ["what {other_name} probably thinks"],
"other_likely_ignorant_of": ["what {other_name} probably doesn't know"],
"communication_adjustment": "how {character_name} should adjust their response",
"internal_reasoning": "{character_name}'s private reasoning about {other_name}'s mental state"}}"""

    try:
        text = call_claude(prompt, timeout=60)
    except ClaudeCLIError:
        return {}
    try:
        return parse_json_response(text, expected_type=dict)
    except ValueError:
        return {}


def format_tom_for_prompt(tom_state: dict) -> str:
    """ToM 추론 결과를 프롬프트에 삽입할 문자열로 포맷."""
    if not tom_state:
        return ""

    parts = ["## Your Assessment of the Other Person's Mind"]

    beliefs = tom_state.get("other_likely_believes", [])
    if beliefs:
        parts.append("They likely believe: " + "; ".join(beliefs))

    gaps = tom_state.get("other_likely_ignorant_of", [])
    if gaps:
        parts.append("They likely don't know: " + "; ".join(gaps))

    adj = tom_state.get("communication_adjustment", "")
    if adj:
        parts.append(f"Adjust your communication: {adj}")

    reasoning = tom_state.get("internal_reasoning", "")
    if reasoning:
        parts.append(f"[Private thought: {reasoning}]")

    return "\n".join(parts)
