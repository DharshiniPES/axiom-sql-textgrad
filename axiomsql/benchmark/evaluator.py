"""
Comprehensive evaluation harness for Execution Accuracy (EX), Valid SQL (VA),
and Iteration efficiency across schema complexity tiers.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd
from axiomsql.benchmark.datasets import BENCHMARK_SUITE, BenchmarkQuery, create_benchmark_sandbox
from axiomsql.benchmark.baselines import ZeroShotBaseline, FewShotBaseline, NaiveReflexionBaseline
from axiomsql.core.pipeline import AxiomSQLPipeline, PipelineConfig
from axiomsql.adaptive.stopping_policy import StoppingStrategy
from axiomsql.engine.llm_backend import BaseLLM, OfflineNeuralSimulator


@dataclass
class MethodMetrics:
    method_name: str
    total_queries: int
    valid_sql_count: int
    execution_correct_count: int
    total_iterations: int
    total_latency_seconds: float

    @property
    def valid_sql_rate(self) -> float:
        return (self.valid_sql_count / self.total_queries) * 100.0 if self.total_queries > 0 else 0.0

    @property
    def execution_accuracy(self) -> float:
        return (self.execution_correct_count / self.total_queries) * 100.0 if self.total_queries > 0 else 0.0

    @property
    def avg_iterations(self) -> float:
        return (self.total_iterations / self.total_queries) if self.total_queries > 0 else 0.0

    @property
    def avg_latency_ms(self) -> float:
        return (self.total_latency_seconds * 1000.0 / self.total_queries) if self.total_queries > 0 else 0.0


class BenchmarkEvaluator:
    """Evaluates multiple approaches against relational databases across complexity tiers."""

    def __init__(self, llm: Optional[BaseLLM] = None):
        self.llm = llm or OfflineNeuralSimulator()

    def evaluate_all(
        self,
        queries: Optional[List[BenchmarkQuery]] = None,
        max_iterations: int = 4,
        stopping_strategy: StoppingStrategy = StoppingStrategy.EXECUTION_GATED,
    ) -> pd.DataFrame:
        target_queries = queries or BENCHMARK_SUITE

        methods = {
            "Zero-Shot": ZeroShotBaseline(self.llm),
            "Few-Shot": FewShotBaseline(self.llm),
            "Naive-Reflexion": NaiveReflexionBaseline(self.llm, max_retries=max_iterations),
            "AxiomSQL (Ours)": AxiomSQLPipeline(
                llm=self.llm,
                config=PipelineConfig(
                    max_iterations=max_iterations,
                    stopping_strategy=stopping_strategy,
                )
            ),
        }

        records = []
        for q in target_queries:
            sandbox = create_benchmark_sandbox(q.db_id)
            gold_res = sandbox.execute_query(q.gold_sql)

            for m_name, runner in methods.items():
                if isinstance(runner, AxiomSQLPipeline):
                    p_res = runner.run(
                        question=q.question,
                        sandbox=sandbox,
                        gold_result=gold_res,
                    )
                    records.append({
                        "query_id": q.id,
                        "db_id": q.db_id,
                        "difficulty": q.difficulty,
                        "method": m_name,
                        "valid_sql": p_res.execution_result.success,
                        "exec_match": bool(p_res.is_correct),
                        "iterations": p_res.total_iterations,
                        "latency_sec": p_res.total_duration_seconds,
                    })
                else:
                    b_res = runner.run(
                        question=q.question,
                        sandbox=sandbox,
                        gold_result=gold_res,
                    )
                    records.append({
                        "query_id": q.id,
                        "db_id": q.db_id,
                        "difficulty": q.difficulty,
                        "method": m_name,
                        "valid_sql": b_res.execution_result.success,
                        "exec_match": bool(b_res.is_correct),
                        "iterations": b_res.iterations,
                        "latency_sec": b_res.duration_seconds,
                    })

        df = pd.DataFrame(records)
        return df

    @staticmethod
    def compute_summary_table(df: pd.DataFrame) -> pd.DataFrame:
        """Aggregates metrics by method into presentation-ready summary table."""
        summary = []
        for method, group in df.groupby("method"):
            total = len(group)
            va = (group["valid_sql"].sum() / total) * 100.0
            ex = (group["exec_match"].sum() / total) * 100.0
            avg_iter = group["iterations"].mean()
            avg_lat = group["latency_sec"].mean() * 1000.0

            summary.append({
                "Method": method,
                "Valid SQL (%)": round(va, 2),
                "Exec Accuracy EX (%)": round(ex, 2),
                "Avg Iterations (K)": round(avg_iter, 2),
                "Avg Latency (ms)": round(avg_lat, 2),
            })
        return pd.DataFrame(summary).sort_values("Exec Accuracy EX (%)", ascending=False)
