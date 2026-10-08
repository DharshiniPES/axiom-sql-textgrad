"""
Script to execute the complete benchmark suite across all complexity tiers
and print publication-ready empirical comparison tables.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from axiomsql.benchmark.datasets import BENCHMARK_SUITE
from axiomsql.benchmark.evaluator import BenchmarkEvaluator
from axiomsql.adaptive.stopping_policy import StoppingStrategy
from axiomsql.engine.llm_backend import OfflineNeuralSimulator


def main():
    print("=" * 80)
    print("AXIOMSQL BENCHMARK EVALUATION SUITE")
    print("Evaluating: Zero-Shot vs Few-Shot vs Naive Reflexion vs AxiomSQL (Ours)")
    print(f"Total benchmark queries: {len(BENCHMARK_SUITE)} across Financial, E-Commerce, Healthcare")
    print("=" * 80)

    evaluator = BenchmarkEvaluator(llm=OfflineNeuralSimulator())
    df = evaluator.evaluate_all(
        queries=BENCHMARK_SUITE,
        max_iterations=4,
        stopping_strategy=StoppingStrategy.EXECUTION_GATED,
    )

    print("\n### 1. SUMMARY COMPARISON TABLE")
    summary_df = BenchmarkEvaluator.compute_summary_table(df)
    print(summary_df.to_string(index=False))

    print("\n### 2. PERFORMANCE BY DIFFICULTY TIER")
    diff_summary = []
    for (diff, method), grp in df.groupby(["difficulty", "method"]):
        total = len(grp)
        ex = (grp["exec_match"].sum() / total) * 100.0
        va = (grp["valid_sql"].sum() / total) * 100.0
        avg_k = grp["iterations"].mean()
        diff_summary.append({
            "Difficulty": diff,
            "Method": method,
            "Count": total,
            "Valid SQL (%)": round(va, 1),
            "Exec Acc EX (%)": round(ex, 1),
            "Avg K": round(avg_k, 2),
        })

    diff_df = pd.DataFrame(diff_summary)
    # Order by difficulty
    diff_order = {"easy": 1, "medium": 2, "hard": 3, "extra-hard": 4}
    diff_df["order"] = diff_df["Difficulty"].map(diff_order)
    diff_df = diff_df.sort_values(["order", "Exec Acc EX (%)"], ascending=[True, False]).drop(columns=["order"])
    print(diff_df.to_string(index=False))

    print("\n### 3. ABLATION: ADAPTIVE STOPPING STRATEGIES")
    strategies = [
        StoppingStrategy.EXECUTION_GATED,
        StoppingStrategy.GRADIENT_CONVERGENCE,
        StoppingStrategy.PARETO_UTILITY,
        StoppingStrategy.FIXED_BUDGET,
    ]
    ablation_records = []
    for strat in strategies:
        strat_df = evaluator.evaluate_all(
            queries=BENCHMARK_SUITE,
            max_iterations=4,
            stopping_strategy=strat,
        )
        axiom_grp = strat_df[strat_df["method"] == "AxiomSQL (Ours)"]
        ablation_records.append({
            "Stopping Strategy": strat.value,
            "Exec Acc EX (%)": round((axiom_grp["exec_match"].sum() / len(axiom_grp)) * 100.0, 1),
            "Avg Iterations K": round(axiom_grp["iterations"].mean(), 2),
            "Avg Latency (ms)": round(axiom_grp["latency_sec"].mean() * 1000.0, 2),
        })

    abl_df = pd.DataFrame(ablation_records)
    print(abl_df.to_string(index=False))

    print("\nBenchmark completed successfully.")


if __name__ == "__main__":
    main()
