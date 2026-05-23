"""대화 히스토리 관리."""

from dataclasses import dataclass


@dataclass
class Message:
    role: str  # "user" or "character"
    content: str


class ConversationMemory:
    """세션 내 대화 히스토리를 관리."""

    def __init__(self, max_messages: int = 20):
        self.messages: list[Message] = []
        self.max_messages = max_messages

    def add(self, role: str, content: str):
        self.messages.append(Message(role=role, content=content))
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def format_for_prompt(self, character_name: str = "Character") -> str:
        """대화 히스토리를 프롬프트용 문자열로 포맷."""
        if not self.messages:
            return "(No conversation history yet)"

        lines = []
        for msg in self.messages:
            label = "User" if msg.role == "user" else character_name
            lines.append(f"{label}: {msg.content}")
        return "\n".join(lines)

    def clear(self):
        self.messages.clear()
