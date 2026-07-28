"""Core engine combining character, retrieval, timeline, and memory context."""

from src.claude_cli import call_claude, parse_json_response
from src.characters import CHARACTERS
from src.character.profile import load_profile
from src.character.prompt_builder import build_system_prompt, build_timeline_safe_profile
from src.character.arc_tracker import (
    format_arc_for_prompt,
    get_future_only_entities,
    get_state_at_position,
    load_arc,
)
from src.character.theory_of_mind import infer_other_perspective, format_tom_for_prompt
from src.character.logic_extractor import load_logic, format_logic_for_prompt
from src.memory.conversation import ConversationMemory
from src.memory.retriever import search

class CharacterEngine:
    """캐릭터 에이전트의 핵심 엔진."""

    def __init__(self, character_id: str, persistent_memory=None, config: dict = None):
        self.character_id = character_id
        self.profile = load_profile(character_id)
        self.character_name = self.profile.get("name", character_id)
        self.memory = ConversationMemory(max_messages=20)
        spec = CHARACTERS.get(character_id)
        self.book_id = spec.book_id if spec else character_id
        self.persistent_memory = persistent_memory
        self.bdi_state = {"beliefs": [], "desires": [], "intentions": []}
        self.arc_snapshots = load_arc(character_id)
        self.narrative_position = None  # None = 전체 지식, int = 해당 챕터까지만
        self.reader_position = None    # None = 전체, int = 독자가 읽은 챕터까지
        self.tom_state = {}
        self._tom_turn_count = 0
        self.character_logic = load_logic(character_id)

        # Feature flags for demos and diagnostics.
        cfg = config or {}
        self.use_rag = cfg.get("use_rag", True)
        self.use_temporal_filter = cfg.get("use_temporal_filter", True)
        self.use_unknown_list = cfg.get("use_unknown_list", True)
        self.use_arc_state = cfg.get("use_arc_state", True)
        self.use_logic = cfg.get("use_logic", True)
        self.use_tom = cfg.get("use_tom", True)

    def set_narrative_position(self, position):
        """캐릭터의 서사 시점을 설정. 더 이른 시점으로 이동하면 대화를 초기화."""
        self._validate_position(position, "narrative")
        previous_boundary = self._effective_position()
        self.narrative_position = position
        self._clear_state_for_stricter_boundary(previous_boundary)

    def set_reader_position(self, position):
        """독자의 진행도를 설정. 더 이른 시점으로 이동하면 대화를 초기화."""
        self._validate_position(position, "reader")
        previous_boundary = self._effective_position()
        self.reader_position = position
        self._clear_state_for_stricter_boundary(previous_boundary)

    def _validate_position(self, position, label: str) -> None:
        if position is None:
            return
        if not isinstance(position, int) or isinstance(position, bool) or position < 0:
            raise ValueError(f"{label} position must be a non-negative integer or None")
        if self.arc_snapshots and position > len(self.arc_snapshots):
            raise ValueError(
                f"{label} position must be between 0 and {len(self.arc_snapshots)}"
            )

    def _effective_position(self):
        """Return the strictest active story boundary, or None for full knowledge."""
        positions = [
            position
            for position in (self.narrative_position, self.reader_position)
            if position is not None
        ]
        return min(positions) if positions else None

    def _clear_state_for_stricter_boundary(self, previous_boundary) -> None:
        current_boundary = self._effective_position()
        became_stricter = (
            current_boundary is not None
            and (
                previous_boundary is None
                or current_boundary < previous_boundary
            )
        )
        if not became_stricter:
            return

        # Prior character replies, BDI, and theory-of-mind state may have been
        # generated with broader story knowledge. Reusing them would bypass the
        # new retrieval boundary.
        self.memory.clear()
        self.bdi_state = {"beliefs": [], "desires": [], "intentions": []}
        self.tom_state = {}
        self._tom_turn_count = 0

    def respond(self, user_input: str) -> str:
        """사용자 입력에 대해 캐릭터로서 응답."""
        effective_position = self._effective_position()

        # Retrieve story context inside the active timeline boundary.
        rag_context = "(No specific story context retrieved)"
        if self.use_rag:
            max_story_number = (
                effective_position
                if self.use_temporal_filter and effective_position is not None
                else None
            )
            rag_results = search(
                user_input,
                book_id=self.book_id,
                n_results=3,
                max_story_number=max_story_number,
            )
            rag_context = self._format_rag_context(rag_results)

        # Assemble conversation, mental-state, and persistent-memory context.
        conversation_history = self.memory.format_for_prompt(self.character_name)
        bdi_text = self._format_bdi() if effective_position is None else ""
        persistent_context = ""
        if self.persistent_memory and effective_position is None:
            persistent_context = self.persistent_memory.recall(user_input)

        if persistent_context:
            rag_context = f"{rag_context}\n\n## Memories from Previous Conversations\n{persistent_context}"

        # Add the character's cumulative state and future-unknown list.
        arc_context = ""
        if effective_position is not None:
            state = {}
            if self.use_arc_state and self.arc_snapshots:
                state = get_state_at_position(self.arc_snapshots, effective_position)
            arc_context = format_arc_for_prompt(
                state,
                effective_position,
                (
                    self.arc_snapshots
                    if self.use_unknown_list and self.arc_snapshots
                    else None
                ),
            )

        if arc_context:
            rag_context = f"{arc_context}\n\n{rag_context}"

        # Refresh theory-of-mind context every third turn.
        tom_text = ""
        self._tom_turn_count += 1
        should_refresh_tom = (
            self.use_tom
            and effective_position is None
            and self._tom_turn_count % 3 == 0
            and len(self.memory.messages) >= 4
        )
        if should_refresh_tom:
            self.tom_state = infer_other_perspective(
                self.character_name, "the user", user_input,
                self.profile, conversation_history,
            )
            tom_text = format_tom_for_prompt(self.tom_state)

        if tom_text:
            bdi_text = f"{bdi_text}\n\n{tom_text}" if bdi_text else tom_text

        # Full-book behavioral rules are not timeline-tagged yet, so they are
        # unsafe inside a bounded conversation.
        if self.use_logic and effective_position is None:
            logic_text = format_logic_for_prompt(self.character_logic)
            if logic_text:
                bdi_text = f"{bdi_text}\n\n{logic_text}" if bdi_text else logic_text

        prompt_profile = self.profile
        if effective_position is not None:
            blocked_entities = get_future_only_entities(
                self.arc_snapshots,
                effective_position,
            )
            prompt_profile = build_timeline_safe_profile(
                self.profile,
                blocked_entities,
            )

        system_prompt = build_system_prompt(
            prompt_profile,
            rag_context,
            conversation_history,
            bdi_text,
            timeline_position=effective_position,
        )

        try:
            response = self._call_claude(system_prompt, user_input)
        except RuntimeError as exc:
            return f"[Unable to generate a response: {exc}]"

        # Save only successful turns.
        self.memory.add("user", user_input)
        self.memory.add("character", response)

        if self.persistent_memory:
            self.persistent_memory.save_turn(user_input, response)

        if effective_position is None:
            self._update_bdi()

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

    def _update_bdi(self):
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
            text = call_claude(prompt, timeout=60)
            self.bdi_state = parse_json_response(text, expected_type=dict)
        except Exception:
            pass  # BDI 업데이트 실패는 무시

    def _call_claude(self, system_prompt: str, user_input: str) -> str:
        prompt = f"User says: {user_input}\n\nRespond as {self.character_name}:"
        return call_claude(prompt, timeout=180, system_prompt=system_prompt)

    def reset(self):
        self.memory.clear()
        self.bdi_state = {"beliefs": [], "desires": [], "intentions": []}
        self._tom_turn_count = 0
        self.tom_state = {}
