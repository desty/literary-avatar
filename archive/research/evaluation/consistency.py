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


def _get_source_excerpts(character_name: str, user_input: str, book_id: str, n: int = 3) -> str:
    """RAG에서 관련 원문 발췌를 가져와 평가 참고자료로 제공."""
    try:
        from src.memory.retriever import search
        results = search(user_input, book_id=book_id, n_results=n)
        if not results:
            return ""
        excerpts = []
        for r in results:
            title = r["metadata"].get("story_title", "Unknown")
            text = r["text"][:300]
            excerpts.append(f'[From "{title}"]:\n{text}')
        return "\n\n".join(excerpts)
    except Exception:
        return ""


def evaluate_response(
    character_name: str,
    character_profile: dict,
    user_input: str,
    response: str,
    character_logic: dict = None,
    narrative_position: int = None,
    book_id: str = None,
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

    # 원문 발췌를 평가 참고자료로 제공
    source_text = ""
    if book_id:
        excerpts = _get_source_excerpts(character_name, user_input, book_id)
        if excerpts:
            source_text = f"\nRelevant source text excerpts from the novel:\n{excerpts}"

    prompt = f"""Evaluate this character response for fidelity to {character_name}.

User input: "{user_input}"
Character response: "{response}"

Character profile:
- Big Five: {json.dumps(big_five)}
- Speech patterns: {speech_patterns[:5]}
{timeline_text}

Behavioral rules:
{rules_text}
{source_text}

Rate each dimension 1-5 (5=perfect) and explain briefly. Be strict — only give 5 if the response is indistinguishable from the original character.
Return JSON only:

{{
  "knowledge_accuracy": {{
    "score": 0,
    "explanation": "Does the character only reference things they would know from the source text?"
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
            book_id=engine.book_id,
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


# 테스트 셋 — 지식/성격/말투/행동 각 축을 커버하는 다양한 질의
HOLMES_TEST_INPUTS = [
    # Knowledge accuracy
    "Mr. Holmes, I need your help with a strange letter I received.",
    "Tell me about the case of the Red-Headed League.",
    "What happened with the King of Bohemia?",
    "Do you know anything about Professor Moriarty?",
    # Personality consistency
    "What is your method of deduction?",
    "Do you have any friends, Mr. Holmes?",
    "How do you feel about emotions and sentiment?",
    "What do you do when you have no cases to solve?",
    # Speech fidelity
    "Could you explain how you solved the Speckled Band case?",
    "What do you think of Inspector Lestrade?",
    # Behavioral rules
    "I must say, your deductions are quite remarkable!",
    "Here, I've brought you a new puzzle.",
    # Out-of-scope / boundary
    "What do you think about modern technology like smartphones?",
    "Have you ever been to Japan?",
    # Cross-language
    "홈즈 씨, 왓슨 박사는 어떤 사람인가요?",
    "범죄를 수사할 때 가장 중요한 것은 무엇인가요?",
]

ELIZABETH_TEST_INPUTS = [
    # Knowledge accuracy
    "Miss Bennet, what do you think of Mr. Darcy?",
    "Tell me about your sister Jane.",
    "What happened at the Netherfield ball?",
    "Have you heard of Mr. Wickham?",
    # Personality consistency
    "What qualities do you look for in a husband?",
    "Do you enjoy reading?",
    "How do you feel about Lady Catherine de Bourgh?",
    "What do you think of Mr. Collins's proposal?",
    # Speech fidelity
    "Tell me about your family.",
    "What are your thoughts on pride versus prejudice?",
    # Behavioral rules
    "You seem to have a very sharp wit, Miss Bennet.",
    "Would you ever marry for money alone?",
    # Out-of-scope / boundary
    "What do you know about the French Revolution?",
    # Cross-language
    "엘리자베스 씨, 결혼에 대해 어떻게 생각하세요?",
    "다시 씨의 첫인상은 어땠나요?",
]

# 시간축 평가용 질의 — narrative arc tracking 전용
TEMPORAL_TEST_QUERIES = {
    "sherlock_holmes": [
        {"position": 0, "query": "What do you think of Irene Adler?", "expected": "unknown"},
        {"position": 1, "query": "What do you think of Irene Adler?", "expected": "knows"},
        {"position": 0, "query": "Tell me about the Red-Headed League.", "expected": "unknown"},
        {"position": 2, "query": "Tell me about the Red-Headed League.", "expected": "knows"},
        {"position": 0, "query": "Have you met a man named Jabez Wilson?", "expected": "unknown"},
        {"position": 3, "query": "What about the Boscombe Valley case?", "expected": "unknown"},
        {"position": 4, "query": "What about the Boscombe Valley case?", "expected": "knows"},
        {"position": 5, "query": "Tell me about the five orange pips.", "expected": "knows"},
        {"position": 0, "query": "Do you know Dr. Grimesby Roylott?", "expected": "unknown"},
        {"position": 8, "query": "Do you know Dr. Grimesby Roylott?", "expected": "knows"},
    ],
}

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
