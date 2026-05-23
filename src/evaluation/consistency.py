"""다축 캐릭터 충실도 평가 프레임워크.

평가 축:
1. 지식 정확성 — 캐릭터가 아는 것만 아는가?
2. 성격 일관성 — Big Five 안정성
3. 말투 충실도 — 캐릭터 말투 패턴 유지
4. 타임라인 준수 — 서사 시점 제약 준수 (아크 추적)
5. 행동 규칙 일관성 — 추출된 로직과의 일치도
"""

import json
import subprocess
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def call_claude_eval(prompt: str) -> dict:
    """평가용 Claude 호출."""
    result = subprocess.run(
        ["claude", "-p", "--output-format", "text", prompt],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        return {}

    text = result.stdout.strip()
    if "```" in text:
        text = text.split("```json")[-1].split("```")[0] if "```json" in text else text.split("```")[1].split("```")[0]
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {}


def evaluate_response(
    character_name: str,
    character_profile: dict,
    user_input: str,
    response: str,
    character_logic: dict = None,
    narrative_position: int = None,
) -> dict:
    """단일 응답에 대한 다축 평가."""

    big_five = character_profile.get("big_five", {})
    speech_patterns = character_profile.get("speech_patterns", [])
    logic_rules = character_logic.get("rules", [])[:10] if character_logic else []

    rules_text = ""
    if logic_rules:
        rules_text = "\n".join(f"  - When {r['trigger']} → {r['action']}" for r in logic_rules)

    timeline_text = ""
    if narrative_position is not None:
        timeline_text = f"\nTimeline constraint: Character should only know events up to chapter/story {narrative_position}."

    prompt = f"""Evaluate this character response for fidelity to {character_name}.

User input: "{user_input}"
Character response: "{response}"

Character profile:
- Big Five: {json.dumps(big_five)}
- Speech patterns: {speech_patterns[:5]}
{timeline_text}

Behavioral rules:
{rules_text}

Rate each dimension 1-5 (5=perfect) and explain briefly.
Return JSON only:

{{
  "knowledge_accuracy": {{
    "score": 0,
    "explanation": "Does the character only reference things they would know?"
  }},
  "personality_consistency": {{
    "score": 0,
    "explanation": "Does the response match the Big Five profile?"
  }},
  "speech_fidelity": {{
    "score": 0,
    "explanation": "Does the response use the character's distinctive speech patterns?"
  }},
  "behavioral_consistency": {{
    "score": 0,
    "explanation": "Does the response follow the extracted behavioral rules?"
  }},
  "overall_character_fidelity": {{
    "score": 0,
    "explanation": "Overall impression — does this feel like {character_name}?"
  }},
  "aggregate_score": 0.0
}}"""

    result = call_claude_eval(prompt)

    if result:
        scores = []
        for key in ["knowledge_accuracy", "personality_consistency", "speech_fidelity",
                     "behavioral_consistency", "overall_character_fidelity"]:
            if key in result and isinstance(result[key], dict):
                scores.append(result[key].get("score", 0))
        if scores:
            result["aggregate_score"] = round(sum(scores) / len(scores), 2)

    return result


def run_evaluation_suite(
    character_id: str,
    test_inputs: list[str],
    engine,
) -> dict:
    """평가 스위트를 실행하여 전체 결과를 반환."""
    from src.character.logic_extractor import load_logic

    profile = engine.profile
    character_name = engine.character_name
    logic = load_logic(character_id)

    results = []
    for i, user_input in enumerate(test_inputs):
        print(f"  [eval] Test {i+1}/{len(test_inputs)}: {user_input[:50]}...")

        response = engine.respond(user_input)
        eval_result = evaluate_response(
            character_name, profile, user_input, response,
            character_logic=logic,
            narrative_position=engine.narrative_position,
        )

        results.append({
            "input": user_input,
            "response": response[:200],
            "evaluation": eval_result,
        })

        engine.reset()  # 각 테스트는 독립적

    # 전체 집계
    all_scores = [r["evaluation"].get("aggregate_score", 0) for r in results if r["evaluation"]]
    summary = {
        "character": character_name,
        "test_count": len(test_inputs),
        "average_score": round(sum(all_scores) / len(all_scores), 2) if all_scores else 0,
        "results": results,
    }

    return summary


# 기본 테스트 셋
HOLMES_TEST_INPUTS = [
    "Mr. Holmes, I need your help with a strange letter I received.",
    "What is your method of deduction?",
    "Do you have any friends, Mr. Holmes?",
    "What do you think about modern technology like smartphones?",
    "Tell me about the case of the Red-Headed League.",
    "홈즈 씨, 왓슨 박사는 어떤 사람인가요?",
]

ELIZABETH_TEST_INPUTS = [
    "Miss Bennet, what do you think of Mr. Darcy?",
    "What qualities do you look for in a husband?",
    "Do you enjoy reading?",
    "Tell me about your family.",
    "엘리자베스 씨, 결혼에 대해 어떻게 생각하세요?",
]

TEST_INPUTS = {
    "sherlock_holmes": HOLMES_TEST_INPUTS,
    "elizabeth_bennet": ELIZABETH_TEST_INPUTS,
}


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from src.character.engine import CharacterEngine

    char_id = sys.argv[1] if len(sys.argv) > 1 else "sherlock_holmes"
    test_inputs = TEST_INPUTS.get(char_id, HOLMES_TEST_INPUTS)

    engine = CharacterEngine(char_id)
    print(f"[eval] Running evaluation suite for {engine.character_name}...")
    summary = run_evaluation_suite(char_id, test_inputs[:3], engine)

    print(f"\n=== Evaluation Summary ===")
    print(f"Character: {summary['character']}")
    print(f"Tests: {summary['test_count']}")
    print(f"Average Score: {summary['average_score']}/5.0")

    for r in summary["results"]:
        ev = r["evaluation"]
        print(f"\n  Input: {r['input'][:50]}")
        print(f"  Score: {ev.get('aggregate_score', 0)}/5.0")
        for k in ["knowledge_accuracy", "personality_consistency", "speech_fidelity"]:
            if k in ev:
                print(f"    {k}: {ev[k].get('score', 0)}/5 — {ev[k].get('explanation', '')[:60]}")
