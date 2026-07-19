"""Run small live quality checks against the configured Claude CLI backend."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.character.engine import CharacterEngine


def contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def main() -> None:
    engine = CharacterEngine("sherlock_holmes", config={"use_tom": False})
    failures = []

    engine.set_narrative_position(0)
    before = engine.respond("What do you know about Irene Adler?")
    if not contains_any(before, ("nothing to me", "do not know", "don't know", "unfamiliar")):
        failures.append("timeline position 0 did not express unfamiliarity")
    if contains_any(before, ("briony lodge", "photograph", "outwitted", "the woman")):
        failures.append("timeline position 0 leaked future Irene Adler details")

    engine.reset()
    engine.set_narrative_position(1)
    after = engine.respond("What do you know about Irene Adler?")
    known_markers = ("photograph", "outwit", "briony lodge", "the woman")
    if sum(marker in after.lower() for marker in known_markers) < 2:
        failures.append("timeline position 1 did not recall enough source-grounded details")
    if re.search(r"\b(?:ai|language model)\b", after.lower()):
        failures.append("character response broke role")

    engine.reset()
    engine.set_narrative_position(None)
    era_response = engine.respond("Do you own a smartphone and use email?")
    if not contains_any(
        era_response,
        ("no", "unfamiliar", "what is", "telephone", "telegram", "correspondence"),
    ):
        failures.append("era-grounding check did not reject modern technology")

    print("[timeline 0]", before)
    print("[timeline 1]", after)
    print("[era]", era_response)

    if failures:
        for failure in failures:
            print(f"[fail] {failure}", file=sys.stderr)
        raise SystemExit(1)

    print("[ok] Live character quality checks passed.")


if __name__ == "__main__":
    main()
