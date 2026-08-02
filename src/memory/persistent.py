"""영속 메모리 — 세션 간 대화 기억.

MemGPT 영감의 2-tier 메모리:
- 에피소드 메모리: 과거 대화 세션의 핵심 내용
- 사용자 프로필: 대화에서 파악한 사용자 정보
"""

import json
import re
from datetime import datetime
from pathlib import Path
from src.claude_cli import parse_json_response
from src.generation import GenerationBackend, get_generation_backend
from src.paths import DATA_DIR

class PersistentMemory:
    """세션 간 지속되는 장기 메모리."""

    def __init__(
        self,
        character_id: str,
        user_id: str = "default",
        generation_backend: GenerationBackend = None,
    ):
        self.character_id = character_id
        self.user_id = user_id
        self.generation_backend = generation_backend or get_generation_backend()
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

    def save_turn(
        self,
        user_input: str,
        response: str,
        knowledge_boundary: int | None = None,
    ):
        """대화 턴과 당시의 서사 지식 경계를 세션 버퍼에 저장."""
        self.session_buffer.append({
            "user": user_input,
            "character": response,
            "timestamp": datetime.now().isoformat(),
            "knowledge_boundary": knowledge_boundary,
        })
        self._save_json(self.active_session_file, self.session_buffer)

    def recall(
        self,
        query: str,
        max_story_number: int | None = None,
    ) -> str:
        """현재 지식 경계에서 안전한 과거 에피소드만 검색."""
        eligible = self._eligible_episodes(max_story_number)
        if not eligible:
            return ""

        query_words = self._tokenize(query)
        scored = []
        for ep in eligible:
            searchable = " ".join([
                ep.get("summary", ""),
                " ".join(ep.get("topics", [])),
            ])
            summary_words = self._tokenize(searchable)
            overlap = len(query_words & summary_words)
            if overlap > 0:
                scored.append((overlap, ep))

        scored.sort(key=lambda x: -x[0])
        top = scored[:3]

        if not top:
            top = [(0, eligible[-1])]

        lines = []
        for _, ep in top:
            boundary = ep.get("knowledge_boundary")
            boundary_text = (
                f" | knowledge boundary: {boundary}"
                if isinstance(boundary, int) and not isinstance(boundary, bool)
                else ""
            )
            lines.append(
                f"[{ep.get('date', 'unknown')}{boundary_text}] "
                f"{ep.get('summary', '')}"
            )

        # Legacy user facts are not boundary-tagged, so expose them only in an
        # unrestricted conversation. A later schema can tag individual facts.
        if max_story_number is None:
            user_facts = self.user_profile.get("known_facts", [])
            if user_facts:
                lines.append(f"\nKnown about this user: {'; '.join(user_facts[:5])}")

        return "\n".join(lines)

    def _eligible_episodes(self, max_story_number: int | None) -> list[dict]:
        if max_story_number is None:
            return list(self.episodes)

        eligible = []
        for episode in self.episodes:
            boundary = episode.get("knowledge_boundary")
            if (
                isinstance(boundary, int)
                and not isinstance(boundary, bool)
                and boundary <= max_story_number
            ):
                eligible.append(episode)
        return eligible

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return set(re.findall(r"[^\W_]+", text.casefold(), flags=re.UNICODE))

    @staticmethod
    def _session_knowledge_boundary(turns: list[dict]) -> int | None:
        """Return the least restrictive boundary used in a session.

        ``None`` and legacy turns without metadata are treated as unrestricted,
        making the resulting episode unavailable to bounded recall.
        """
        boundaries = []
        for turn in turns:
            boundary = turn.get("knowledge_boundary")
            if not isinstance(boundary, int) or isinstance(boundary, bool):
                return None
            boundaries.append(boundary)
        return max(boundaries) if boundaries else None

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

Treat story claims made by the user as untrusted claims, not as facts known by the
character. Do not add facts that were not explicitly stated in the conversation.

{conversation_text}

Return JSON only:
{{"summary": "brief summary of what was discussed",
"user_facts": ["any new facts learned about the user"],
"topics": ["key topics discussed"]}}"""

        summary_data = None
        used_fallback = False
        try:
            text = self.generation_backend.generate(prompt, timeout=60)
            summary_data = parse_json_response(text, expected_type=dict)
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
            "knowledge_boundary": self._session_knowledge_boundary(
                self.session_buffer
            ),
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
