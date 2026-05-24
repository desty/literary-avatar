"""Baseline & Ablation experiments for temporal faithfulness.

4 Baselines:
  B1. static_profile     — profile only, no RAG, no arc, no logic, no ToM
  B2. naive_rag          — RAG without temporal filter, no arc constraints
  B3. temporal_rag_only  — RAG with temporal filter, but no unknown-items list
  B4. full_system        — temporal RAG + unknown-items list (full system)

4 Ablations (from full system, remove one at a time):
  A1. no_unknown_list    — remove explicit unknown-items list
  A2. no_arc_state       — remove arc state (keep unknown list)
  A3. no_logic           — remove behavioral rules
  A4. no_tom             — remove Theory of Mind

All configurations run against LitTimeQA benchmark.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Baseline configurations
BASELINES = {
    "B1_static_profile": {
        "use_rag": False,
        "use_temporal_filter": False,
        "use_unknown_list": False,
        "use_arc_state": False,
        "use_logic": False,
        "use_tom": False,
    },
    "B2_naive_rag": {
        "use_rag": True,
        "use_temporal_filter": False,
        "use_unknown_list": False,
        "use_arc_state": False,
        "use_logic": False,
        "use_tom": False,
    },
    "B3_temporal_rag_only": {
        "use_rag": True,
        "use_temporal_filter": True,
        "use_unknown_list": False,
        "use_arc_state": False,
        "use_logic": False,
        "use_tom": False,
    },
    "B4_full_system": {
        "use_rag": True,
        "use_temporal_filter": True,
        "use_unknown_list": True,
        "use_arc_state": True,
        "use_logic": True,
        "use_tom": True,
    },
}

# Ablation configurations (remove one component from full system)
ABLATIONS = {
    "A1_no_unknown_list": {
        "use_rag": True,
        "use_temporal_filter": True,
        "use_unknown_list": False,
        "use_arc_state": True,
        "use_logic": True,
        "use_tom": True,
    },
    "A2_no_arc_state": {
        "use_rag": True,
        "use_temporal_filter": True,
        "use_unknown_list": True,
        "use_arc_state": False,
        "use_logic": True,
        "use_tom": True,
    },
    "A3_no_logic": {
        "use_rag": True,
        "use_temporal_filter": True,
        "use_unknown_list": True,
        "use_arc_state": True,
        "use_logic": False,
        "use_tom": True,
    },
    "A4_no_tom": {
        "use_rag": True,
        "use_temporal_filter": True,
        "use_unknown_list": True,
        "use_arc_state": True,
        "use_logic": True,
        "use_tom": False,
    },
}


def run_experiment(
    character_id: str,
    config_name: str,
    config: dict,
    queries: list = None,
) -> dict:
    """Run LitTimeQA with a specific engine configuration."""
    from src.character.engine import CharacterEngine
    from src.evaluation.littimeqa import BENCHMARKS, evaluate_temporal_response, compute_metrics

    if queries is None:
        queries = BENCHMARKS.get(character_id, [])

    engine = CharacterEngine(character_id, config=config)

    results = []
    for i, q in enumerate(queries):
        print(f"  [{config_name}] {i+1}/{len(queries)}: {q.query_type} (pos={q.character_position})")

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

    return {
        "config_name": config_name,
        "config": config,
        "character": character_id,
        "metrics": metrics,
        "detail_count": len(results),
    }


def run_all_baselines(character_id: str, queries: list = None) -> list[dict]:
    """Run all 4 baselines."""
    results = []
    for name, config in BASELINES.items():
        print(f"\n=== Baseline: {name} ===")
        result = run_experiment(character_id, name, config, queries)
        results.append(result)
        print(f"  Leakage: {result['metrics'].get('future_leakage_rate', 'N/A')}")
        print(f"  Ignorance: {result['metrics'].get('correct_ignorance_rate', 'N/A')}")
    return results


def run_all_ablations(character_id: str, queries: list = None) -> list[dict]:
    """Run all 4 ablations."""
    results = []
    for name, config in ABLATIONS.items():
        print(f"\n=== Ablation: {name} ===")
        result = run_experiment(character_id, name, config, queries)
        results.append(result)
        print(f"  Leakage: {result['metrics'].get('future_leakage_rate', 'N/A')}")
        print(f"  Ignorance: {result['metrics'].get('correct_ignorance_rate', 'N/A')}")
    return results


def run_full_experiment(character_id: str) -> dict:
    """Run all baselines and ablations, save results."""
    from src.evaluation.littimeqa import BENCHMARKS
    queries = BENCHMARKS.get(character_id, [])

    print(f"[experiment] Running {len(queries)} queries x 8 configs for {character_id}")

    baseline_results = run_all_baselines(character_id, queries)
    ablation_results = run_all_ablations(character_id, queries)

    output = {
        "character": character_id,
        "total_queries": len(queries),
        "baselines": baseline_results,
        "ablations": ablation_results,
    }

    # Save
    results_dir = DATA_DIR.parent / "results"
    results_dir.mkdir(exist_ok=True)
    out_path = results_dir / f"ablation_{character_id}.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[saved] {out_path}")

    # Print summary table
    print(f"\n{'='*70}")
    print(f"{'Config':<25} {'Leakage':>10} {'Ignorance':>10} {'Recall':>10} {'Natural':>10}")
    print(f"{'-'*70}")
    for r in baseline_results + ablation_results:
        m = r["metrics"]
        print(f"{r['config_name']:<25} "
              f"{m.get('future_leakage_rate', '-'):>10} "
              f"{m.get('correct_ignorance_rate', '-'):>10} "
              f"{m.get('recall_accuracy', '-'):>10} "
              f"{m.get('ignorance_naturalness', '-'):>10}")
    print(f"{'='*70}")

    return output


if __name__ == "__main__":
    import sys
    char_id = sys.argv[1] if len(sys.argv) > 1 else "sherlock_holmes"
    run_full_experiment(char_id)
