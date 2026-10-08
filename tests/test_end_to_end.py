"""End-to-End integration tests for AxiomSQL."""

import pytest
from axiomsql.core.pipeline import AxiomSQLPipeline, PipelineConfig
from axiomsql.adaptive.stopping_policy import StoppingStrategy
from axiomsql.benchmark.datasets import create_benchmark_sandbox, BENCHMARK_SUITE
from axiomsql.benchmark.evaluator import BenchmarkEvaluator
from axiomsql.engine.llm_backend import OfflineNeuralSimulator


def test_pipeline_end_to_end_financial():
    sandbox = create_benchmark_sandbox("financial")
    query_item = [q for q in BENCHMARK_SUITE if q.id == "fin-01"][0]
    gold_res = sandbox.execute_query(query_item.gold_sql)

    pipeline = AxiomSQLPipeline(
        llm=OfflineNeuralSimulator(),
        config=PipelineConfig(
            max_iterations=4,
            stopping_strategy=StoppingStrategy.EXECUTION_GATED,
        )
    )

    result = pipeline.run(
        question=query_item.question,
        sandbox=sandbox,
        gold_result=gold_res,
    )

    assert result.execution_result.success is True
    assert result.total_iterations >= 1
    assert result.total_iterations <= 4
    assert result.is_correct is True
    assert len(result.history) == result.total_iterations
    assert result.stopping_decision.should_stop is True
    sandbox.close()


def test_benchmark_evaluator_small_run():
    sample_queries = BENCHMARK_SUITE[:3]
    evaluator = BenchmarkEvaluator(llm=OfflineNeuralSimulator())
    df = evaluator.evaluate_all(queries=sample_queries, max_iterations=2)

    assert len(df) == len(sample_queries) * 4  # 4 methods evaluated
    assert "method" in df.columns
    assert "valid_sql" in df.columns
    assert "exec_match" in df.columns

    summary = BenchmarkEvaluator.compute_summary_table(df)
    assert len(summary) == 4
    assert "Exec Accuracy EX (%)" in summary.columns
