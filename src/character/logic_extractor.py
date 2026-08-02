"""소설 텍스트에서 캐릭터 행동 지침을 자동 추출."""

import json
from pathlib import Path
from src.claude_cli import parse_json_response
from src.characters import get_character
from src.generation import GenerationBackend, get_generation_backend
from src.paths import DATA_DIR

def extract_character_logic(
    book_id: str,
    character_name: str,
    generation_backend: GenerationBackend = None,
) -> dict:
    """소설에서 캐릭터의 행동 규칙을 자동 추출."""

    processed = DATA_DIR / "processed" / f"{book_id}.json"
    data = json.loads(processed.read_text(encoding="utf-8"))

    # 전체 소설에서 캐릭터 관련 장면 수집
    scenes = []
    for story in data["stories"]:
        text = story["text"]
        if len(text) > 2000:
            text = text[:1000] + "\n[...]\n" + text[-500:]
        scenes.append(f"[{story['title']}]\n{text}")

    # 3배치로 나눠서 처리
    batch_size = len(scenes) // 3 + 1
    all_rules = []
    backend = generation_backend or get_generation_backend()

    for i in range(0, len(scenes), batch_size):
        batch = scenes[i:i + batch_size]
        batch_text = "\n\n---\n\n".join(batch)

        prompt = f"""Analyze {character_name}'s behavior patterns in these story excerpts. Extract behavioral rules — "if X situation, then {character_name} does Y" patterns.

{batch_text}

Extract rules in these categories:
1. DETERMINISTIC: Always does this (e.g., "when presented with a mystery → always asks for specific details first")
2. PROBABILISTIC: Usually does this (e.g., "when complimented → 80% deflects, 20% accepts curtly")
3. CONDITIONAL: Depends on context (e.g., "when a woman is in danger → more protective than usual")

Return JSON only:
{{"rules": [
  {{
    "trigger": "the situation or stimulus",
    "action": "what {character_name} does",
    "type": "deterministic|probabilistic|conditional",
    "probability": 1.0,
    "evidence": "brief quote or reference from the text",
    "category": "reasoning|social|emotional|habitual"
  }}
]}}"""

        try:
            text = backend.generate(prompt, timeout=180)
        except RuntimeError:
            continue
        try:
            batch_rules = parse_json_response(text, expected_type=dict)
            all_rules.extend(batch_rules.get("rules", []))
            print(f"  [logic] Batch {i // batch_size + 1}: {len(batch_rules.get('rules', []))} rules")
        except ValueError:
            print(f"  [warn] Failed to parse batch {i // batch_size + 1}")

    # 중복 제거 및 정리
    seen = set()
    unique_rules = []
    for rule in all_rules:
        key = (rule.get("trigger", ""), rule.get("action", ""))
        if key not in seen:
            seen.add(key)
            unique_rules.append(rule)

    return {
        "character": character_name,
        "total_rules": len(unique_rules),
        "rules": unique_rules,
        "by_category": _group_by_category(unique_rules),
        "by_type": _group_by_type(unique_rules),
    }


def _group_by_category(rules: list[dict]) -> dict:
    groups = {}
    for r in rules:
        cat = r.get("category", "other")
        groups.setdefault(cat, []).append(r)
    return {k: len(v) for k, v in groups.items()}


def _group_by_type(rules: list[dict]) -> dict:
    groups = {}
    for r in rules:
        t = r.get("type", "unknown")
        groups.setdefault(t, []).append(r)
    return {k: len(v) for k, v in groups.items()}


def save_logic(logic: dict, character_id: str) -> Path:
    """캐릭터 로직을 저장."""
    logic_dir = DATA_DIR / "logic"
    logic_dir.mkdir(parents=True, exist_ok=True)

    output_path = logic_dir / f"{character_id}.json"
    output_path.write_text(
        json.dumps(logic, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[saved] {output_path} ({logic['total_rules']} rules)")
    return output_path


def load_logic(character_id: str) -> dict:
    """저장된 캐릭터 로직을 로드."""
    path = DATA_DIR / "logic" / f"{character_id}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def format_logic_for_prompt(logic: dict, max_rules: int = 15) -> str:
    """캐릭터 로직을 프롬프트에 삽입할 문자열로 포맷."""
    if not logic or not logic.get("rules"):
        return ""

    rules = logic["rules"][:max_rules]
    lines = ["## Your Behavioral Rules (extracted from your stories)"]
    for r in rules:
        prob = f" ({int(r.get('probability', 1.0) * 100)}%)" if r.get("probability", 1.0) < 1.0 else ""
        lines.append(f"  - When {r['trigger']} → {r['action']}{prob}")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    char_id = sys.argv[1] if len(sys.argv) > 1 else "sherlock_holmes"
    spec = get_character(char_id)

    print(f"[logic] Extracting behavioral rules for {spec.name}...")
    logic = extract_character_logic(spec.book_id, spec.name)
    save_logic(logic, char_id)

    print(f"\nTotal rules: {logic['total_rules']}")
    print(f"By category: {logic['by_category']}")
    print(f"By type: {logic['by_type']}")
    print("\nSample rules:")
    for r in logic["rules"][:5]:
        print(f"  [{r.get('type','?')}] When {r['trigger']} → {r['action']}")
