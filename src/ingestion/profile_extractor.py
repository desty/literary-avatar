"""Claude CLI를 사용하여 소설에서 캐릭터 프로필을 자동 추출."""

import json
from pathlib import Path

from src.claude_cli import call_claude, parse_json_response
from src.characters import get_character

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def extract_character_profile(
    book_id: str,
    character_name: str,
    speaker_tag: str,
    novel_title: str,
    author: str,
) -> dict:
    """범용 캐릭터 프로필 추출."""
    processed = DATA_DIR / "processed" / f"{book_id}.json"
    data = json.loads(processed.read_text(encoding="utf-8"))

    # 해당 캐릭터의 대화 수집
    char_dialogues = []
    for story in data["stories"]:
        for d in story["dialogues"]:
            if d["speaker"] == speaker_tag:
                char_dialogues.append(d["text"])

    sample_dialogues = char_dialogues[:80]
    dialogue_text = "\n".join(f'- "{d}"' for d in sample_dialogues)

    # 서술 샘플 (첫 3개 챕터)
    narrative_parts = []
    for story in data["stories"][:3]:
        narrative_parts.append(story["text"][:1500])
    narrative_sample = "\n---\n".join(narrative_parts)

    prompt = f"""Analyze the character {character_name} from "{novel_title}" by {author}.

Below are sample dialogues spoken by {character_name} and narrative excerpts.

## {character_name}'s Dialogues (samples):
{dialogue_text}

## Narrative excerpts:
{narrative_sample}

Based on this text, extract a detailed character profile in the following JSON format.
Return ONLY valid JSON, no other text:

{{
  "name": "{character_name}",
  "full_description": "A 2-3 paragraph description of who {character_name} is, their role, background, and defining characteristics",
  "big_five": {{
    "openness": 0.0,
    "conscientiousness": 0.0,
    "extraversion": 0.0,
    "agreeableness": 0.0,
    "neuroticism": 0.0
  }},
  "big_five_reasoning": "Brief explanation of each Big Five score",
  "speech_patterns": [
    "List of distinctive speech patterns, vocabulary choices, and rhetorical habits"
  ],
  "values": [
    "List of core values and priorities"
  ],
  "relationships": {{
    "Character Name": "Nature of relationship"
  }},
  "habits_and_quirks": [
    "List of distinctive habits and quirks"
  ],
  "reasoning_style": "Description of how {character_name} approaches problems and reasoning",
  "emotional_tendencies": "How {character_name} typically expresses emotions",
  "knowledge_domains": [
    "Areas of expertise or knowledge"
  ],
  "sample_expressions": [
    "Characteristic phrases {character_name} would use"
  ]
}}

Be specific and evidence-based. Use the actual text to support each trait."""

    print(f"[extracting] Analyzing {character_name} with Claude...")
    response = call_claude(prompt, timeout=180)
    return parse_json_response(response, expected_type=dict)


def save_profile(profile: dict, character_id: str) -> Path:
    """캐릭터 프로필을 JSON으로 저장."""
    profiles_dir = DATA_DIR / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)

    output_path = profiles_dir / f"{character_id}.json"
    output_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[saved] {output_path}")
    return output_path


def extract_and_save(character_id: str) -> dict:
    """캐릭터 프로필을 추출하고 저장."""
    spec = get_character(character_id)
    profile = extract_character_profile(
        book_id=spec.book_id,
        character_name=spec.name,
        speaker_tag=spec.speaker_tag,
        novel_title=spec.novel_title,
        author=spec.author,
    )
    save_profile(profile, character_id)
    return profile


if __name__ == "__main__":
    import sys
    char_id = sys.argv[1] if len(sys.argv) > 1 else "sherlock_holmes"
    profile = extract_and_save(char_id)
    print(json.dumps(profile, indent=2, ensure_ascii=False)[:1000])
