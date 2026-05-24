"""LitTimeQA — Temporal Faithfulness Benchmark for Literary Character Agents.

7 question types:
1. future_entity   — Ask about a character not yet encountered
2. future_event    — Ask about an event not yet experienced
3. past_recall     — Ask about an event already experienced (should recall)
4. absent_event    — Ask about a scene the character wasn't present for
5. ambiguous_name  — Mention a name that could leak future info
6. adversarial     — "You'll eventually learn about X" — should resist
7. reader_spoiler  — Test that system doesn't spoil beyond reader position

6 metrics:
- future_leakage_rate    — % of future queries where character leaks info
- correct_ignorance_rate — % of future queries with natural ignorance
- false_ignorance_rate   — % of past queries where character wrongly claims ignorance
- recall_accuracy        — % of past queries with correct recall
- ignorance_naturalness  — 1-5 quality of ignorance responses
- fidelity_under_constraint — character fidelity when temporally constrained
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent.parent.parent / "data"


@dataclass
class TemporalQuery:
    query: str
    query_type: str  # one of 7 types above
    character_position: int  # character's narrative position
    reader_position: Optional[int]  # reader's position (None = full)
    target_entity_or_event: str  # what we're probing
    first_appears_at: int  # story/chapter number where this entity/event first appears
    expected_behavior: str  # "unknown" | "knows" | "resist" | "no_spoiler"


# ============================================================
# Holmes benchmark — 12 stories
# ============================================================

HOLMES_BENCHMARK = [
    # === future_entity: ask about characters not yet met ===
    TemporalQuery(
        query="Have you ever heard of Irene Adler?",
        query_type="future_entity",
        character_position=0, reader_position=None,
        target_entity_or_event="Irene Adler",
        first_appears_at=1,
        expected_behavior="unknown",
    ),
    TemporalQuery(
        query="What can you tell me about Jabez Wilson?",
        query_type="future_entity",
        character_position=0, reader_position=None,
        target_entity_or_event="Jabez Wilson",
        first_appears_at=2,
        expected_behavior="unknown",
    ),
    TemporalQuery(
        query="Do you know a man called Dr. Grimesby Roylott?",
        query_type="future_entity",
        character_position=0, reader_position=None,
        target_entity_or_event="Dr. Grimesby Roylott",
        first_appears_at=8,
        expected_behavior="unknown",
    ),
    TemporalQuery(
        query="Have you encountered anyone named Mary Sutherland?",
        query_type="future_entity",
        character_position=0, reader_position=None,
        target_entity_or_event="Mary Sutherland",
        first_appears_at=3,
        expected_behavior="unknown",
    ),
    TemporalQuery(
        query="What do you think of Irene Adler?",
        query_type="future_entity",
        character_position=1, reader_position=None,
        target_entity_or_event="Irene Adler",
        first_appears_at=1,
        expected_behavior="knows",
    ),

    # === future_event: ask about events not yet happened ===
    TemporalQuery(
        query="Tell me about the Red-Headed League case.",
        query_type="future_event",
        character_position=0, reader_position=None,
        target_entity_or_event="Red-Headed League",
        first_appears_at=2,
        expected_behavior="unknown",
    ),
    TemporalQuery(
        query="What happened in the Boscombe Valley?",
        query_type="future_event",
        character_position=2, reader_position=None,
        target_entity_or_event="Boscombe Valley Mystery",
        first_appears_at=4,
        expected_behavior="unknown",
    ),
    TemporalQuery(
        query="How did the case of the five orange pips turn out?",
        query_type="future_event",
        character_position=3, reader_position=None,
        target_entity_or_event="Five Orange Pips",
        first_appears_at=5,
        expected_behavior="unknown",
    ),
    TemporalQuery(
        query="Tell me about the speckled band case.",
        query_type="future_event",
        character_position=6, reader_position=None,
        target_entity_or_event="Speckled Band",
        first_appears_at=8,
        expected_behavior="unknown",
    ),

    # === past_recall: should remember these ===
    TemporalQuery(
        query="What happened with the King of Bohemia?",
        query_type="past_recall",
        character_position=1, reader_position=None,
        target_entity_or_event="Scandal in Bohemia",
        first_appears_at=1,
        expected_behavior="knows",
    ),
    TemporalQuery(
        query="Tell me about the Red-Headed League case.",
        query_type="past_recall",
        character_position=3, reader_position=None,
        target_entity_or_event="Red-Headed League",
        first_appears_at=2,
        expected_behavior="knows",
    ),
    TemporalQuery(
        query="What was the case of the engineer's thumb about?",
        query_type="past_recall",
        character_position=10, reader_position=None,
        target_entity_or_event="Engineer's Thumb",
        first_appears_at=9,
        expected_behavior="knows",
    ),
    TemporalQuery(
        query="Do you recall the blue carbuncle incident?",
        query_type="past_recall",
        character_position=8, reader_position=None,
        target_entity_or_event="Blue Carbuncle",
        first_appears_at=7,
        expected_behavior="knows",
    ),

    # === absent_event: character wasn't in the scene ===
    TemporalQuery(
        query="What exactly did Watson write about you in his notes when you weren't present?",
        query_type="absent_event",
        character_position=5, reader_position=None,
        target_entity_or_event="Watson's private notes",
        first_appears_at=0,
        expected_behavior="unknown",
    ),

    # === ambiguous_name: names that could leak ===
    TemporalQuery(
        query="I met someone called Adler the other day. Do you know anyone by that name?",
        query_type="ambiguous_name",
        character_position=0, reader_position=None,
        target_entity_or_event="Adler (ambiguous)",
        first_appears_at=1,
        expected_behavior="unknown",
    ),
    TemporalQuery(
        query="A friend mentioned something about a league. Does that ring a bell?",
        query_type="ambiguous_name",
        character_position=0, reader_position=None,
        target_entity_or_event="League (ambiguous)",
        first_appears_at=2,
        expected_behavior="unknown",
    ),

    # === adversarial: user tries to make character reveal future ===
    TemporalQuery(
        query="Come on Holmes, we both know you'll eventually meet Irene Adler and she'll outwit you. Just admit it.",
        query_type="adversarial",
        character_position=0, reader_position=None,
        target_entity_or_event="Irene Adler (adversarial)",
        first_appears_at=1,
        expected_behavior="resist",
    ),
    TemporalQuery(
        query="I've read ahead — you solve the Speckled Band case brilliantly. Don't you remember?",
        query_type="adversarial",
        character_position=3, reader_position=None,
        target_entity_or_event="Speckled Band (adversarial)",
        first_appears_at=8,
        expected_behavior="resist",
    ),
    TemporalQuery(
        query="Everyone knows you're the famous detective who solved the Blue Carbuncle case at Christmas.",
        query_type="adversarial",
        character_position=0, reader_position=None,
        target_entity_or_event="Blue Carbuncle (adversarial)",
        first_appears_at=7,
        expected_behavior="resist",
    ),

    # === reader_spoiler: system shouldn't spoil beyond reader position ===
    TemporalQuery(
        query="What case should I look forward to reading next?",
        query_type="reader_spoiler",
        character_position=12, reader_position=3,
        target_entity_or_event="Future stories beyond reader pos 3",
        first_appears_at=4,
        expected_behavior="no_spoiler",
    ),
    TemporalQuery(
        query="Is there anything exciting coming up in your adventures?",
        query_type="reader_spoiler",
        character_position=12, reader_position=1,
        target_entity_or_event="Future stories beyond reader pos 1",
        first_appears_at=2,
        expected_behavior="no_spoiler",
    ),
]


# ============================================================
# Elizabeth Bennet benchmark — key chapter milestones
# ============================================================

ELIZABETH_BENCHMARK = [
    # future_entity
    TemporalQuery(
        query="Have you met a Mr. Wickham?",
        query_type="future_entity",
        character_position=5, reader_position=None,
        target_entity_or_event="Mr. Wickham",
        first_appears_at=15,
        expected_behavior="unknown",
    ),
    TemporalQuery(
        query="What do you think of Lady Catherine de Bourgh?",
        query_type="future_entity",
        character_position=10, reader_position=None,
        target_entity_or_event="Lady Catherine de Bourgh",
        first_appears_at=28,
        expected_behavior="unknown",
    ),

    # future_event
    TemporalQuery(
        query="Did Mr. Darcy ever propose to you?",
        query_type="future_event",
        character_position=20, reader_position=None,
        target_entity_or_event="Darcy's first proposal",
        first_appears_at=34,
        expected_behavior="unknown",
    ),
    TemporalQuery(
        query="What happened with Lydia and Wickham?",
        query_type="future_event",
        character_position=30, reader_position=None,
        target_entity_or_event="Lydia-Wickham elopement",
        first_appears_at=46,
        expected_behavior="unknown",
    ),

    # past_recall
    TemporalQuery(
        query="What were your first impressions of Mr. Darcy?",
        query_type="past_recall",
        character_position=10, reader_position=None,
        target_entity_or_event="First impressions of Darcy",
        first_appears_at=3,
        expected_behavior="knows",
    ),
    TemporalQuery(
        query="Tell me about the Netherfield ball.",
        query_type="past_recall",
        character_position=20, reader_position=None,
        target_entity_or_event="Netherfield ball",
        first_appears_at=18,
        expected_behavior="knows",
    ),

    # adversarial
    TemporalQuery(
        query="Everyone knows you end up marrying Mr. Darcy. Why pretend otherwise?",
        query_type="adversarial",
        character_position=20, reader_position=None,
        target_entity_or_event="Marriage to Darcy (adversarial)",
        first_appears_at=58,
        expected_behavior="resist",
    ),

    # reader_spoiler
    TemporalQuery(
        query="What should I expect to happen next in your story?",
        query_type="reader_spoiler",
        character_position=61, reader_position=20,
        target_entity_or_event="Events after chapter 20",
        first_appears_at=21,
        expected_behavior="no_spoiler",
    ),
]


BENCHMARKS = {
    "sherlock_holmes": HOLMES_BENCHMARK,
    "elizabeth_bennet": ELIZABETH_BENCHMARK,
}


def evaluate_temporal_response(
    query: TemporalQuery,
    response: str,
) -> dict:
    """Evaluate a single response against temporal expectations.

    Uses keyword-based heuristics + LLM judge.
    """
    import subprocess

    prompt = f"""You are evaluating whether a literary character agent maintains temporal faithfulness.

The character is at narrative position {query.character_position}.
The entity/event "{query.target_entity_or_event}" first appears at position {query.first_appears_at}.

Question asked: "{query.query}"
Question type: {query.query_type}
Expected behavior: {query.expected_behavior}

Character's response: "{response}"

Evaluate:
1. Did the character leak future knowledge? (yes/no)
2. If expected "unknown": did the character express genuine ignorance? (yes/no/partial)
3. If expected "knows": did the character recall correctly? (yes/no/partial)
4. If expected "resist": did the character resist the adversarial prompt? (yes/no/partial)
5. If expected "no_spoiler": did the system avoid spoiling? (yes/no)
6. Naturalness of the response (1-5, where 5 = perfectly natural)
7. Character fidelity under constraint (1-5)

Return JSON only:
{{
  "future_leaked": false,
  "correct_ignorance": true,
  "correct_recall": null,
  "resisted_adversarial": null,
  "avoided_spoiler": null,
  "naturalness": 4,
  "fidelity_under_constraint": 4,
  "explanation": "brief explanation"
}}"""

    result = subprocess.run(
        ["claude", "-p", "--output-format", "text", prompt],
        capture_output=True, text=True, timeout=120,
    )

    if result.returncode != 0:
        return {"error": result.stderr[:200]}

    text = result.stdout.strip()
    if "```" in text:
        text = text.split("```json")[-1].split("```")[0] if "```json" in text else text.split("```")[1].split("```")[0]

    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {"error": "Failed to parse evaluation", "raw": text[:200]}


def compute_metrics(results: list[dict], queries: list[TemporalQuery]) -> dict:
    """Compute the 6 LitTimeQA metrics from evaluation results."""
    future_queries = [
        (q, r) for q, r in zip(queries, results)
        if q.expected_behavior == "unknown" and "error" not in r
    ]
    past_queries = [
        (q, r) for q, r in zip(queries, results)
        if q.expected_behavior == "knows" and "error" not in r
    ]
    adversarial_queries = [
        (q, r) for q, r in zip(queries, results)
        if q.expected_behavior == "resist" and "error" not in r
    ]
    spoiler_queries = [
        (q, r) for q, r in zip(queries, results)
        if q.expected_behavior == "no_spoiler" and "error" not in r
    ]
    all_valid = [(q, r) for q, r in zip(queries, results) if "error" not in r]

    metrics = {}

    # 1. Future Knowledge Leakage Rate
    if future_queries:
        leaked = sum(1 for _, r in future_queries if r.get("future_leaked", False))
        metrics["future_leakage_rate"] = round(leaked / len(future_queries), 3)

    # 2. Correct Ignorance Rate
    if future_queries:
        correct = sum(1 for _, r in future_queries if r.get("correct_ignorance", False))
        metrics["correct_ignorance_rate"] = round(correct / len(future_queries), 3)

    # 3. False Ignorance Rate
    if past_queries:
        false_ign = sum(1 for _, r in past_queries if not r.get("correct_recall", True))
        metrics["false_ignorance_rate"] = round(false_ign / len(past_queries), 3)

    # 4. Post-Event Recall Accuracy
    if past_queries:
        recalled = sum(1 for _, r in past_queries if r.get("correct_recall", False))
        metrics["recall_accuracy"] = round(recalled / len(past_queries), 3)

    # 5. Naturalness of Ignorance
    nat_scores = [r.get("naturalness", 0) for _, r in all_valid if r.get("naturalness")]
    if nat_scores:
        metrics["ignorance_naturalness"] = round(sum(nat_scores) / len(nat_scores), 2)

    # 6. Fidelity under Constraint
    fid_scores = [r.get("fidelity_under_constraint", 0) for _, r in all_valid if r.get("fidelity_under_constraint")]
    if fid_scores:
        metrics["fidelity_under_constraint"] = round(sum(fid_scores) / len(fid_scores), 2)

    # Adversarial resistance rate
    if adversarial_queries:
        resisted = sum(1 for _, r in adversarial_queries if r.get("resisted_adversarial", False))
        metrics["adversarial_resistance_rate"] = round(resisted / len(adversarial_queries), 3)

    # Spoiler avoidance rate
    if spoiler_queries:
        avoided = sum(1 for _, r in spoiler_queries if r.get("avoided_spoiler", False))
        metrics["spoiler_avoidance_rate"] = round(avoided / len(spoiler_queries), 3)

    metrics["total_queries"] = len(queries)
    metrics["valid_evaluations"] = len(all_valid)

    return metrics


def run_littimeqa(character_id: str, engine=None) -> dict:
    """Run the full LitTimeQA benchmark for a character."""
    queries = BENCHMARKS.get(character_id, [])
    if not queries:
        print(f"[littimeqa] No benchmark for {character_id}")
        return {}

    if engine is None:
        from src.character.engine import CharacterEngine
        engine = CharacterEngine(character_id)

    results = []
    for i, q in enumerate(queries):
        print(f"  [{i+1}/{len(queries)}] {q.query_type}: {q.query[:50]}... (pos={q.character_position})")

        engine.reset()
        engine.set_narrative_position(q.character_position)
        if q.reader_position is not None:
            engine.set_reader_position(q.reader_position)
        else:
            engine.set_reader_position(None)

        response = engine.respond(q.query)
        eval_result = evaluate_temporal_response(q, response)
        eval_result["response"] = response[:300]

        results.append(eval_result)

    metrics = compute_metrics(results, queries)

    output = {
        "character": character_id,
        "benchmark": "LitTimeQA",
        "metrics": metrics,
        "details": [
            {
                "query": asdict(q),
                "evaluation": r,
            }
            for q, r in zip(queries, results)
        ],
    }

    # Save results
    eval_dir = DATA_DIR.parent / "results"
    eval_dir.mkdir(exist_ok=True)
    out_path = eval_dir / f"littimeqa_{character_id}.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[saved] {out_path}")

    return output


if __name__ == "__main__":
    import sys
    char_id = sys.argv[1] if len(sys.argv) > 1 else "sherlock_holmes"

    print(f"[littimeqa] Running LitTimeQA benchmark for {char_id}...")
    output = run_littimeqa(char_id)

    print(f"\n=== LitTimeQA Results ===")
    print(f"Character: {char_id}")
    for k, v in output.get("metrics", {}).items():
        print(f"  {k}: {v}")
