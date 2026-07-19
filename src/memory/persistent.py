"""영속 메모리 — 세션 간 대화 기억.

MemGPT 영감의 2-tier 메모리:
- 에피소드 메모리: 과거 대화 세션의 핵심 내용
- 사용자 프로필: 대화에서 파악한 사용자 정보
"""

import json
from datetime import datetime
from pathlib import Path

from src.claude_cli import call_claude

DATA_DIR = Path(__file__).parent.parent.parent / "data"


class PersistentMemory:
    """세션 간 지속되는 장기 메모리."""

    def __init__(self, character_id: str, user_id: str = "default"):
        self.character_id = character_id
        self.user_id = user_id
        self.memory_dir = DATA_DIR / "memory" / character_id / user_id
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.episodes_file = self.memory_dir / "episodes.json"
        self.user_profile_file = self.memory_dir / "user_profile.json"
        self.active_session_file = self.memory_dir / "active_session.json"
        self.session_buffer: list[dict] = self._load_json(self.active_session_file, [])

        self.episodes = self._load_json(self.episodes_file, [])
        self.user_profile = self._load_json(self.user_profile_file, {
            "known_facts": [],
            "preferences": [],
            "relationship_notes": [],
        })

    def _load_json(self, path: Path, default):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return default

    def _save_json(self, path: Path, data):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def save_turn(self, user_input: str, response: str):
        """대화 턴을 세션 버퍼에 저장."""
        self.session_buffer.append({
            "user": user_input,
            "character": response,
            "timestamp": datetime.now().isoformat(),
        })
        self._save_json(self.active_session_file, self.session_buffer)

    def recall(self, query: str) -> str:
        """과거 에피소드에서 관련 기억을 검색."""
        if not self.episodes:
            return ""

        # 간단한 키워드 매칭 (향후 임베딩 검색으로 개선 가능)
        query_words = set(query.lower().split())
        scored = []
        for ep in self.episodes:
            summary_words = set(ep.get("summary", "").lower().split())
            overlap = len(query_words & summary_words)
            if overlap > 0:
                scored.append((overlap, ep))

        scored.sort(key=lambda x: -x[0])
        top = scored[:3]

        if not top:
            # 가장 최근 에피소드 반환
            if self.episodes:
                top = [(0, self.episodes[-1])]
            else:
                return ""

        lines = []
        for _, ep in top:
            lines.append(f"[{ep.get('date', 'unknown')}] {ep.get('summary', '')}")

        # 사용자 프로필 정보 추가
        user_facts = self.user_profile.get("known_facts", [])
        if user_facts:
            lines.append(f"\nKnown about this user: {'; '.join(user_facts[:5])}")

        return "\n".join(lines)

    def clear_all(self) -> None:
        """Delete all persisted and active memory for this character/user pair."""
        self.episodes = []
        self.user_profile = {
            "known_facts": [],
            "preferences": [],
            "relationship_notes": [],
        }
        self.session_buffer = []
        self._save_json(self.episodes_file, self.episodes)
        self._save_json(self.user_profile_file, self.user_profile)
        self._save_json(self.active_session_file, self.session_buffer)

    def end_session(self):
        """세션 종료 시 대화를 요약하여 에피소드 메모리에 저장."""
        if not self.session_buffer:
            return

        # 대화를 요약
        conversation_text = "\n".join(
            f"User: {t['user']}\nCharacter: {t['character']}"
            for t in self.session_buffer
        )

        prompt = f"""Summarize this conversation in 2-3 sentences. Also extract any facts learned about the user.

{conversation_text}

Return JSON only:
{{"summary": "brief summary of what was discussed",
"user_facts": ["any new facts learned about the user"],
"topics": ["key topics discussed"]}}"""

        summary_data = None
        used_fallback = False
        try:
            text = call_claude(prompt, timeout=60)
            if "```" in text:
                text = text.split("```json")[-1].split("```")[0] if "```json" in text else text.split("```")[1].split("```")[0]
            summary_data = json.loads(text.strip())
            if not isinstance(summary_data, dict):
                raise ValueError("Claude summary must be a JSON object")
        except Exception:
            used_fallback = True
            summary_data = {
                "summary": f"Conversation with {len(self.session_buffer)} turns",
                "topics": [],
                "user_facts": [],
            }

        episode = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "summary": summary_data.get("summary", ""),
            "topics": summary_data.get("topics", []),
            "turn_count": len(self.session_buffer),
        }
        if not summary_data.get("summary"):
            episode["summary"] = f"Conversation with {len(self.session_buffer)} turns"

        # LLM 요약을 얻지 못한 경우에도 원본 턴을 보존한다.
        if used_fallback:
            episode["turns"] = list(self.session_buffer)

        self.episodes.append(episode)
        self._save_json(self.episodes_file, self.episodes)

        new_facts = summary_data.get("user_facts", [])
        existing = set(self.user_profile.get("known_facts", []))
        for fact in new_facts:
            if fact and fact not in existing:
                self.user_profile["known_facts"].append(fact)
                existing.add(fact)
        self._save_json(self.user_profile_file, self.user_profile)

        print(f"[memory] Session saved: {episode['summary'][:80]}...")
        self.session_buffer.clear()
        self._save_json(self.active_session_file, self.session_buffer)
