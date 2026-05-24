"""소설 텍스트를 구조화된 데이터로 파싱."""

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"

# 12개 단편 제목 (정확한 매칭용)
SHERLOCK_STORIES = [
    "A SCANDAL IN BOHEMIA",
    "THE RED-HEADED LEAGUE",
    "A CASE OF IDENTITY",
    "THE BOSCOMBE VALLEY MYSTERY",
    "THE FIVE ORANGE PIPS",
    "THE MAN WITH THE TWISTED LIP",
    "THE ADVENTURE OF THE BLUE CARBUNCLE",
    "THE ADVENTURE OF THE SPECKLED BAND",
    "THE ADVENTURE OF THE ENGINEER\u2019S THUMB",
    "THE ADVENTURE OF THE NOBLE BACHELOR",
    "THE ADVENTURE OF THE BERYL CORONET",
    "THE ADVENTURE OF THE COPPER BEECHES",
]


@dataclass
class Dialogue:
    speaker: str
    text: str
    context: str = ""


@dataclass
class Story:
    number: int
    title: str
    text: str
    dialogues: list[Dialogue] = field(default_factory=list)


@dataclass
class ParsedNovel:
    title: str
    author: str
    stories: list[Story] = field(default_factory=list)


def parse_sherlock_holmes(text: str) -> ParsedNovel:
    """셜록 홈즈 단편집을 개별 스토리로 분리하고 대화를 추출."""
    novel = ParsedNovel(
        title="The Adventures of Sherlock Holmes",
        author="Arthur Conan Doyle",
    )

    # 스토리 제목 패턴: "I. A SCANDAL IN BOHEMIA" (로마 숫자 + 3단어 이상의 대문자 제목)
    title_pattern = re.compile(
        r"^([IVXLC]+)\.\s+([A-Z][A-Z\s\u2019\'\-]{10,})$",
        re.MULTILINE,
    )

    matches = list(title_pattern.finditer(text))

    if not matches:
        story = Story(number=1, title="Complete Text", text=text)
        story.dialogues = extract_dialogues(text)
        novel.stories.append(story)
        return novel

    for i, match in enumerate(matches):
        title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        story_text = text[start:end].strip()

        story = Story(
            number=i + 1,
            title=title.title(),
            text=story_text,
        )
        story.dialogues = extract_dialogues(story_text)
        novel.stories.append(story)

    return novel


def extract_dialogues(text: str) -> list[Dialogue]:
    """텍스트에서 대화(인용문)를 추출. 유니코드 따옴표 지원."""
    dialogues = []

    # 유니코드 curly quotes: \u201c = ", \u201d = "
    pattern = re.compile(r'\u201c([^\u201d]{10,}?)\u201d', re.DOTALL)

    for match in pattern.finditer(text):
        quote = match.group(1).strip()
        # 줄바꿈 정리
        quote = re.sub(r'\s+', ' ', quote)
        # 대화 앞뒤 컨텍스트
        ctx_start = max(0, match.start() - 300)
        ctx_end = min(len(text), match.end() + 100)
        before = text[ctx_start:match.start()]
        after = text[match.end():ctx_end]

        speaker = guess_speaker(before, after)
        dialogues.append(Dialogue(
            speaker=speaker,
            text=quote,
            context=re.sub(r'\s+', ' ', before[-120:]).strip(),
        ))

    return dialogues


def guess_speaker(before: str, after: str) -> str:
    """컨텍스트에서 발화자를 추측."""
    speech_verbs = (
        r"said|cried|asked|replied|answered|remarked|observed|exclaimed|"
        r"whispered|murmured|continued|added|shouted|returned|ejaculated|"
        r"muttered|groaned|laughed|snarled|gasped|interrupted|suggested|"
        r"roared|shrieked|yelled"
    )

    skip_words = {
        "i", "he", "she", "it", "we", "they", "the", "a", "my", "his",
        "her", "our", "that", "this", "but", "and", "not", "with", "who",
        "as", "at", "to", "in", "on", "of", "for", "no", "so", "up",
        "an", "or", "if", "do", "be", "by", "is", "was", "had", "has",
    }

    # 대명사 → 이름 매핑 (홈즈 단편에서)
    pronoun_map = {"he": None, "she": None}

    # Pattern 1: "said Holmes" / "cried Watson" (바로 뒤에)
    after_clean = re.sub(r'\s+', ' ', after[:100])
    m = re.match(rf'\s*(?:{speech_verbs})\s+(\w+)', after_clean, re.IGNORECASE)
    if m and m.group(1).lower() not in skip_words:
        return m.group(1)

    # Pattern 2: "Holmes said" (바로 뒤에)
    m = re.match(rf'\s*(\w+)\s+(?:{speech_verbs})', after_clean, re.IGNORECASE)
    if m and m.group(1).lower() not in skip_words:
        return m.group(1)

    # Pattern 3: said Holmes 뒤에 콤마/마침표 후 (after에서 더 넓게)
    m = re.search(rf'(?:{speech_verbs})\s+(\w+)', after_clean, re.IGNORECASE)
    if m and m.group(1).lower() not in skip_words:
        return m.group(1)

    # Pattern 4: before context에서 직전 발화 태그
    last_lines = re.sub(r'\s+', ' ', before[-250:])

    # "Holmes/Watson turned to me and said" 패턴
    m = re.search(rf'(\w+)\s+(?:\w+\s+)*(?:{speech_verbs})\s*$', last_lines, re.IGNORECASE)
    if m and m.group(1).lower() not in skip_words:
        return m.group(1)

    # 직전 문장에서 발화 동사 + 이름
    m = re.search(rf'(?:{speech_verbs})\s+(\w+)', last_lines, re.IGNORECASE)
    if m and m.group(1).lower() not in skip_words:
        return m.group(1)

    return "Unknown"


def save_parsed_novel(novel: ParsedNovel, book_id: str = None) -> Path:
    """파싱된 소설을 JSON으로 저장.

    Args:
        novel: 파싱된 소설 객체
        book_id: 저장 파일명에 사용할 ID (예: 'sherlock_holmes').
                 None이면 제목에서 자동 생성.
    """
    processed_dir = DATA_DIR / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    output = {
        "title": novel.title,
        "author": novel.author,
        "story_count": len(novel.stories),
        "total_dialogues": sum(len(s.dialogues) for s in novel.stories),
        "stories": [],
    }

    for story in novel.stories:
        output["stories"].append({
            "number": story.number,
            "title": story.title,
            "text_length": len(story.text),
            "dialogue_count": len(story.dialogues),
            "dialogues": [asdict(d) for d in story.dialogues],
            "text": story.text,
        })

    if book_id is None:
        slug = novel.title.lower().replace(" ", "_").replace("'", "")
        slug = re.sub(r"[^a-z0-9_]", "", slug)
    else:
        slug = book_id
    output_path = processed_dir / f"{slug}.json"
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[saved] {output_path}")
    print(f"  Stories: {len(novel.stories)}")
    print(f"  Total dialogues: {output['total_dialogues']}")
    return output_path


def parse_pride_and_prejudice(text: str) -> ParsedNovel:
    """오만과 편견을 챕터별로 분리하고 대화를 추출."""
    novel = ParsedNovel(
        title="Pride and Prejudice",
        author="Jane Austen",
    )

    chapter_pattern = re.compile(
        r"(Chapter|CHAPTER)\s+([IVXLC]+)\s*\.?\s*\]?\s*$",
        re.MULTILINE | re.IGNORECASE,
    )

    matches = list(chapter_pattern.finditer(text))

    if not matches:
        story = Story(number=1, title="Complete Text", text=text)
        story.dialogues = extract_dialogues(text)
        novel.stories.append(story)
        return novel

    for i, match in enumerate(matches):
        roman = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chapter_text = text[start:end].strip()

        story = Story(
            number=i + 1,
            title=f"Chapter {roman}",
            text=chapter_text,
        )
        story.dialogues = extract_dialogues(chapter_text)
        novel.stories.append(story)

    return novel


PARSERS = {
    "sherlock_holmes": parse_sherlock_holmes,
    "pride_and_prejudice": parse_pride_and_prejudice,
}


def parse_novel(book_id: str, text: str) -> ParsedNovel:
    """book_id에 맞는 파서로 소설을 파싱."""
    parser = PARSERS.get(book_id)
    if not parser:
        raise ValueError(f"Unknown book_id: {book_id}. Available: {list(PARSERS.keys())}")
    return parser(text)
