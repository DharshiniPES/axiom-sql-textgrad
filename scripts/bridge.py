"""
AxiomSQL Bridge Interface for Node.js Application.
Exposes CLI commands that serialize engine responses into clean JSON.
"""

import os
import sys
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from axiomsql.benchmark.datasets import BENCHMARK_SUITE, create_benchmark_sandbox
from axiomsql.benchmark.evaluator import BenchmarkEvaluator
from axiomsql.core.pipeline import AxiomSQLPipeline, PipelineConfig
from axiomsql.adaptive.stopping_policy import StoppingStrategy
from axiomsql.engine.llm_backend import OfflineNeuralSimulator, GeminiLLM, OpenAILLM
from axiomsql.engine.database import DatabaseSandbox


def get_llm(backend_type: str = "offline", api_key: str = ""):
    if backend_type == "gemini" and api_key:
        return GeminiLLM(api_key=api_key)
    elif backend_type == "openai" and api_key:
        return OpenAILLM(api_key=api_key)
    return OfflineNeuralSimulator()


def cmd_get_metadata():
    dbs = ["financial", "ecommerce", "healthcare"]
    db_metadata = {}

    for db_id in dbs:
        sb = create_benchmark_sandbox(db_id)
        schema_dict = sb.get_schema_dict()
        db_metadata[db_id] = {
            "name": db_id.capitalize(),
            "schema_summary": sb.get_schema_summary(),
            "tables": schema_dict,
        }
        sb.close()

    queries = []
    for q in BENCHMARK_SUITE:
        queries.append({
            "id": q.id,
            "db_id": q.db_id,
            "difficulty": q.difficulty,
            "question": q.question,
            "gold_sql": q.gold_sql,
            "complexity_factors": q.complexity_factors,
        })

    return {
        "databases": db_metadata,
        "benchmark_queries": queries,
        "strategies": [
            {"id": "execution_gated", "name": "Execution-Gated Early Exit (EGEE)", "desc": "Exits when clean execution succeeds with high confidence."},
            {"id": "gradient_convergence", "name": "Gradient Energy Convergence (TGC)", "desc": "Exits when textual gradient norm drops below convergence threshold."},
            {"id": "pareto_utility", "name": "Pareto Cost-Accuracy Utility (PUS)", "desc": "Balances incremental confidence against iteration compute penalty."},
            {"id": "fixed_budget", "name": "Fixed Budget (Exhaust K_max)", "desc": "Unconditionally iterates until max iterations budget is exhausted."}
        ]
    }


def cmd_run_query(payload):
    question = payload.get("question", "")
    db_id = payload.get("db_id", "financial")
    max_k = int(payload.get("max_iterations", 4))
    strat_key = payload.get("stopping_strategy", "execution_gated")
    strategy = StoppingStrategy(strat_key) if strat_key in [s.value for s in StoppingStrategy] else StoppingStrategy.EXECUTION_GATED
    tau = float(payload.get("tau_confidence", 0.85))
    lr = payload.get("learning_rate", "moderate")
    momentum = bool(payload.get("enable_momentum", True))
    annealing = bool(payload.get("enable_annealing", True))
    adversarial = bool(payload.get("enable_adversarial_testing", True))
    backend_type = payload.get("backend", "offline")
    api_key = payload.get("api_key", "")
    weight_cost = float(payload.get("weight_plan_cost", 0.05))

    llm = get_llm(backend_type, api_key)
    sandbox = create_benchmark_sandbox(db_id)

    # Find gold query if present
    gold_sql = None
    for q in BENCHMARK_SUITE:
        if q.question.strip().lower() == question.strip().lower():
            gold_sql = q.gold_sql
            break
    gold_res = sandbox.execute_query(gold_sql) if gold_sql else None

    config = PipelineConfig(
        max_iterations=max_k,
        stopping_strategy=strategy,
        tau_confidence=tau,
        learning_rate=lr,
        enable_momentum=momentum,
        enable_annealing=annealing,
        enable_adversarial_testing=adversarial,
        weight_plan_cost=weight_cost,
    )

    pipeline = AxiomSQLPipeline(llm=llm, config=config)
    result = pipeline.run(
        question=question,
        sandbox=sandbox,
        gold_result=gold_res,
    )

    history_data = []
    for t in result.history:
        history_data.append({
            "iteration": t.iteration,
            "plan_value": t.plan_value,
            "sql_value": t.sql_value,
            "execution_result": {
                "success": t.execution_result.success,
                "row_count": t.execution_result.row_count,
                "columns": t.execution_result.columns,
                "data": t.execution_result.data[:15],
                "error_message": t.execution_result.error_message,
                "execution_time_ms": t.execution_result.execution_time_ms,
                "plan_details": getattr(t.execution_result, "plan_details", []),
            },
            "loss_output": {
                "scalar_loss": round(t.loss_output.scalar_loss, 4),
                "loss_breakdown": {k: round(v, 4) for k, v in t.loss_output.loss_breakdown.items()},
                "error_category": t.loss_output.error_category,
                "execution_success": t.loss_output.execution_success,
                "is_exact_match": t.loss_output.is_exact_match,
            },
            "sql_gradient": t.sql_gradient,
            "plan_gradient": t.plan_gradient,
            "gradient_norm": round(t.gradient_norm, 4),
            "duration_seconds": t.duration_seconds,
            "exit_decision": t.exit_decision,
        })

    sandbox.close()

    return {
        "question": result.question,
        "final_sql": result.final_sql,
        "final_plan": result.final_plan,
        "execution_result": {
            "success": result.execution_result.success,
            "row_count": result.execution_result.row_count,
            "columns": result.execution_result.columns,
            "data": result.execution_result.data[:30],
            "error_message": result.execution_result.error_message,
            "execution_time_ms": result.execution_result.execution_time_ms,
            "plan_details": getattr(result.execution_result, "plan_details", []),
        },
        "total_iterations": result.total_iterations,
        "stopping_decision": {
            "should_stop": result.stopping_decision.should_stop,
            "reason": result.stopping_decision.reason,
            "iteration": result.stopping_decision.iteration,
            "confidence_score": round(result.stopping_decision.confidence_score, 4),
            "current_utility": round(result.stopping_decision.current_utility, 4),
            "strategy_used": result.stopping_decision.strategy_used,
            "details": result.stopping_decision.details,
        },
        "history": history_data,
        "total_duration_seconds": result.total_duration_seconds,
        "is_correct": result.is_correct,
    }


def cmd_run_benchmark(payload):
    max_k = int(payload.get("max_iterations", 4))
    strat_key = payload.get("stopping_strategy", "execution_gated")
    strategy = StoppingStrategy(strat_key) if strat_key in [s.value for s in StoppingStrategy] else StoppingStrategy.EXECUTION_GATED
    backend_type = payload.get("backend", "offline")
    api_key = payload.get("api_key", "")

    llm = get_llm(backend_type, api_key)
    evaluator = BenchmarkEvaluator(llm=llm)

    df_eval = evaluator.evaluate_all(max_iterations=max_k, stopping_strategy=strategy)
    summary_table = BenchmarkEvaluator.compute_summary_table(df_eval)

    return {
        "summary": summary_table.to_dict(orient="records"),
        "detailed": df_eval.to_dict(orient="records"),
    }


def cmd_run_scratchpad(payload):
    db_id = payload.get("db_id", "financial")
    query = payload.get("query", "SELECT 1;")

    sandbox = create_benchmark_sandbox(db_id)
    res = sandbox.execute_query(query)
    sandbox.close()

    return {
        "query": query,
        "success": res.success,
        "columns": res.columns,
        "data": res.data[:50],
        "row_count": res.row_count,
        "error_message": res.error_message,
        "execution_time_ms": res.execution_time_ms,
        "plan_details": getattr(res, "plan_details", []),
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No action provided"}))
        return

    action = sys.argv[1]

    payload = {}
    if len(sys.argv) > 2:
        arg_val = sys.argv[2]
        if os.path.isfile(arg_val):
            try:
                with open(arg_val, "r", encoding="utf-8") as f:
                    payload = json.load(f)
            except Exception:
                payload = {}
        else:
            try:
                payload = json.loads(arg_val)
            except Exception:
                payload = {}

    try:
        if action == "get-metadata":
            res = cmd_get_metadata()
        elif action == "run-query":
            res = cmd_run_query(payload)
        elif action == "run-benchmark":
            res = cmd_run_benchmark(payload)
        elif action == "run-scratchpad":
            res = cmd_run_scratchpad(payload)
        else:
            res = {"error": f"Unknown action: {action}"}

        print(json.dumps(res))
    except Exception as e:
        import traceback
        print(json.dumps({"error": str(e), "traceback": traceback.format_exc()}))


if __name__ == "__main__":
    main()
