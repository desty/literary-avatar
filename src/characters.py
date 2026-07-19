"""Built-in character metadata shared by the runtime and asset pipeline."""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class CharacterSpec:
    character_id: str
    name: str
    book_id: str
    novel_title: str
    author: str
    year: int
    speaker_tag: str
    gutenberg_url: str
    avatar: str

    @property
    def novel_label(self) -> str:
        return f"{self.novel_title} ({self.year})"


CHARACTERS: Dict[str, CharacterSpec] = {
    "sherlock_holmes": CharacterSpec(
        character_id="sherlock_holmes",
        name="Sherlock Holmes",
        book_id="sherlock_holmes",
        novel_title="The Adventures of Sherlock Holmes",
        author="Arthur Conan Doyle",
        year=1892,
        speaker_tag="Holmes",
        gutenberg_url="https://www.gutenberg.org/cache/epub/1661/pg1661.txt",
        avatar="🔍",
    ),
    "elizabeth_bennet": CharacterSpec(
        character_id="elizabeth_bennet",
        name="Elizabeth Bennet",
        book_id="pride_and_prejudice",
        novel_title="Pride and Prejudice",
        author="Jane Austen",
        year=1813,
        speaker_tag="Elizabeth",
        gutenberg_url="https://www.gutenberg.org/cache/epub/1342/pg1342.txt",
        avatar="📖",
    ),
}

DEFAULT_CHARACTER_ID = "sherlock_holmes"


def get_character(character_id: str) -> CharacterSpec:
    """Return a built-in character specification with a useful error."""
    try:
        return CHARACTERS[character_id]
    except KeyError as exc:
        available = ", ".join(sorted(CHARACTERS))
        raise ValueError(
            f"Unknown character_id: {character_id}. Available: {available}"
        ) from exc
