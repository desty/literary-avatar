"""캐릭터 인지 엔진: 프로필 + RAG + 메모리 + BDI + 아크 추적을 조합하여 캐릭터 응답 생성."""

import subprocess

from src.character.profile import load_profile
from src.character.prompt_builder import build_system_prompt
from src.character.arc_tracker import load_arc, get_state_at_position, format_arc_for_prompt
from src.character.theory_of_mind import infer_other_perspective, format_tom_for_prompt
from src.character.logic_extractor import load_logic, format_logic_for_prompt
from src.memory.conversation import ConversationMemory
from src.memory.retriever import search

# 캐릭터 ID → RAG book_id 매핑
CHARACTER_BOOK_MAP = {
    "sherlock_holmes": "sherlock_holmes",
    "elizabeth_bennet": "pride_and_prejudice",
}


class CharacterEngine:
    """캐릭터 에이전트의 핵심 엔진."""

    def __init__(self, character_id: str, persistent_memory=None):
        self.character_id = character_id
        self.profile = load_profile(character_id)
        self.character_name = self.profile.get("name", character_id)
        self.memory = ConversationMemory(max_messages=20)
        self.book_id = CHARACTER_BOOK_MAP.get(character_id, character_id)
        self.persistent_memory = persistent_memory
        self.bdi_state = {"beliefs": [], "desires": [], "intentions": []}
        self.arc_snapshots = load_arc(character_id)
        self.narrative_position = None  # None = 전체 지식, int = 해당 챕터까지만
        self.tom_enabled = True
        self.tom_state = {}
        self._tom_turn_count = 0
        self.character_logic = load_logic(character_id)

    def set_narrative_position(self, position):
        """캐릭터의 서사 시점을 설정. None이면 전체 지식."""
        self.narrative_position = position

    def respond(self, user_input: str) -> str:
        """사용자 입력에 대해 캐릭터로서 응답."""
        # 1. RAG 검색 (서사 시점 필터 적용)
        rag_results = search(user_input, book_id=self.book_id, n_results=5)
        if self.narrative_position is not None:
            rag_results = [
                r for r in rag_results
                if r["metadata"].get("story_number", 0) <= self.narrative_position
            ]
        rag_results = rag_results[:3]
        rag_context = self._format_rag_context(rag_results)

        # 2. 대화 히스토리
        conversation_history = self.memory.format_for_prompt(self.character_name)

        # 3. BDI 상태
        bdi_text = self._format_bdi()

        # 4. 영속 메모리에서 관련 기억 검색
        persistent_context = ""
        if self.persistent_memory:
            persistent_context = self.persistent_memory.recall(user_input)

        if persistent_context:
            rag_context = f"{rag_context}\n\n## Memories from Previous Conversations\n{persistent_context}"

        # 5. 캐릭터 아크 상태 (서사 시점이 설정된 경우)
        arc_context = ""
        if self.narrative_position is not None and self.arc_snapshots:
            state = get_state_at_position(self.arc_snapshots, self.narrative_position)
            arc_context = format_arc_for_prompt(state, self.narrative_position, self.arc_snapshots)

        if arc_context:
            rag_context = f"{arc_context}\n\n{rag_context}"

        # 6. Theory of Mind (3턴마다 사용자 관점 추론)
        tom_text = ""
        self._tom_turn_count += 1
        if self.tom_enabled and self._tom_turn_count % 3 == 0 and len(self.memory.messages) >= 4:
            self.tom_state = infer_other_perspective(
                self.character_name, "the user", user_input,
                self.profile, conversation_history,
            )
            tom_text = format_tom_for_prompt(self.tom_state)

        if tom_text:
            bdi_text = f"{bdi_text}\n\n{tom_text}" if bdi_text else tom_text

        # 8. 캐릭터 로직 규칙
        logic_text = format_logic_for_prompt(self.character_logic)
        if logic_text:
            bdi_text = f"{bdi_text}\n\n{logic_text}" if bdi_text else logic_text

        # 9. 시스템 프롬프트 구성
        system_prompt = build_system_prompt(
            self.profile, rag_context, conversation_history, bdi_text,
        )

        # 6. Claude CLI 호출
        response = self._call_claude(system_prompt, user_input)

        # 7. 메모리 업데이트
        self.memory.add("user", user_input)
        self.memory.add("character", response)

        # 8. 영속 메모리 저장
        if self.persistent_memory:
            self.persistent_memory.save_turn(user_input, response)

        # 9. BDI 업데이트 (비동기적으로 하면 좋지만 MVP에서는 동기)
        self._update_bdi(user_input, response)

        return response

    def _format_rag_context(self, results: list[dict]) -> str:
        if not results:
            return "(No specific story context retrieved)"
        lines = []
        for r in results:
            title = r["metadata"]["story_title"]
            text = r["text"][:400]
            lines.append(f'[From "{title}"]:\n{text}')
        return "\n\n".join(lines)

    def _format_bdi(self) -> str:
        if not any(self.bdi_state.values()):
            return ""
        parts = []
        if self.bdi_state["beliefs"]:
            parts.append("Beliefs: " + "; ".join(self.bdi_state["beliefs"]))
        if self.bdi_state["desires"]:
            parts.append("Desires: " + "; ".join(self.bdi_state["desires"]))
        if self.bdi_state["intentions"]:
            parts.append("Intentions: " + "; ".join(self.bdi_state["intentions"]))
        return "\n".join(parts)

    def _update_bdi(self, user_input: str, response: str):
        """대화 내용에 기반하여 BDI 상태를 업데이트."""
        # 매 턴마다 하면 느리므로 5턴마다 업데이트
        if len(self.memory.messages) % 10 != 0:
            return

        recent = self.memory.format_for_prompt(self.character_name)
        prompt = f"""Given this conversation as {self.character_name}, extract the current mental state.

{recent}

Return JSON only:
{{"beliefs": ["what {self.character_name} currently believes about the situation/user"],
"desires": ["what {self.character_name} wants"],
"intentions": ["what {self.character_name} plans to do next"]}}"""

        try:
            result = subprocess.run(
                ["claude", "-p", "--output-format", "text", prompt],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0:
                import json
                text = result.stdout.strip()
                if "```" in text:
                    text = text.split("```json")[-1].split("```")[0] if "```json" in text else text.split("```")[1].split("```")[0]
                self.bdi_state = json.loads(text.strip())
        except Exception:
            pass  # BDI 업데이트 실패는 무시

    def _call_claude(self, system_prompt: str, user_input: str) -> str:
        full_prompt = f"{system_prompt}\n\n---\n\nUser says: {user_input}\n\nRespond as {self.character_name}:"
        result = subprocess.run(
            ["claude", "-p", "--output-format", "text", full_prompt],
            capture_output=True, text=True, timeout=180,
        )
        if result.returncode != 0:
            return f"[Error: {result.stderr[:200]}]"
        return result.stdout.strip()

    def reset(self):
        self.memory.clear()
        self.bdi_state = {"beliefs": [], "desires": [], "intentions": []}
