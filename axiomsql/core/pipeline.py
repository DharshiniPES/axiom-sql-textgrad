"""
Core AxiomSQL Pipeline orchestrating computational graph execution,
TextGrad backpropagation, and adaptive stopping hyperparameter control.
"""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional
from axiomsql.core.computational_graph import SQLComputationalGraph, IterationTrace
from axiomsql.core.loss import ExecutionLoss, ExecutionLossOutput
from axiomsql.core.optimizer import TextualGradientOptimizer
from axiomsql.adaptive.stopping_policy import (
    AdaptiveStoppingController,
    StoppingDecision,
    StoppingStrategy,
)
from axiomsql.engine.database import DatabaseSandbox, ExecutionResult
from axiomsql.engine.llm_backend import BaseLLM, OfflineNeuralSimulator


@dataclass
class PipelineConfig:
    """Hyperparameters configuring AxiomSQL iterative optimization."""
    max_iterations: int = 4
    stopping_strategy: StoppingStrategy = StoppingStrategy.EXECUTION_GATED
    tau_confidence: float = 0.85
    grad_energy_threshold: float = 0.15
    cost_penalty_lambda: float = 0.08
    learning_rate: str = "moderate"
    enable_momentum: bool = True
    weight_syntax: float = 0.40
    weight_schema: float = 0.25
    weight_cardinality: float = 0.15
    weight_semantic: float = 0.20


@dataclass
class PipelineResult:
    """Final result output from AxiomSQL."""
    question: str
    final_sql: str
    final_plan: str
    execution_result: ExecutionResult
    total_iterations: int
    stopping_decision: StoppingDecision
    history: List[IterationTrace]
    total_duration_seconds: float
    is_correct: Optional[bool] = None

    def summary_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "final_sql": self.final_sql,
            "success": self.execution_result.success,
            "row_count": self.execution_result.row_count,
            "iterations_used": self.total_iterations,
            "stopping_strategy": self.stopping_decision.strategy_used,
            "stopping_reason": self.stopping_decision.reason,
            "confidence": round(self.stopping_decision.confidence_score, 3),
            "duration_sec": round(self.total_duration_seconds, 3),
        }


class AxiomSQLPipeline:
    """End-to-end framework for iterative prompt and query refinement using TextGrad."""

    def __init__(
        self,
        llm: Optional[BaseLLM] = None,
        config: Optional[PipelineConfig] = None,
    ):
        self.llm = llm or OfflineNeuralSimulator()
        self.config = config or PipelineConfig()
        self.loss_fn = ExecutionLoss(
            weight_syntax=self.config.weight_syntax,
            weight_schema=self.config.weight_schema,
            weight_cardinality=self.config.weight_cardinality,
            weight_semantic=self.config.weight_semantic,
        )

    def run(
        self,
        question: str,
        sandbox: DatabaseSandbox,
        schema_summary: Optional[str] = None,
        gold_result: Optional[ExecutionResult] = None,
    ) -> PipelineResult:
        """Executes the iterative TextGrad optimization loop with adaptive stopping."""
        start_time = time.perf_counter()
        schema_text = schema_summary or sandbox.get_schema_summary()

        graph = SQLComputationalGraph(
            llm=self.llm,
            sandbox=sandbox,
            loss_fn=self.loss_fn,
        )
        graph.initialize_graph(question=question, schema_summary=schema_text)

        optimizer = TextualGradientOptimizer(
            llm=self.llm,
            learning_rate=self.config.learning_rate,
            enable_momentum=self.config.enable_momentum,
        )

        controller = AdaptiveStoppingController(
            strategy=self.config.stopping_strategy,
            max_iterations=self.config.max_iterations,
            tau_confidence=self.config.tau_confidence,
            grad_energy_threshold=self.config.grad_energy_threshold,
            cost_penalty_lambda=self.config.cost_penalty_lambda,
        )

        history: List[IterationTrace] = []
        gradient_norms: List[float] = []
        final_decision: Optional[StoppingDecision] = None
        current_sql = ""
        current_plan = ""
        current_exec = ExecutionResult(query="", success=False)

        # Optimization loop: t = 1 to K_max
        for iteration in range(1, self.config.max_iterations + 1):
            iter_start = time.perf_counter()

            # 1. Forward Pass
            if iteration == 1:
                current_plan = graph.forward_plan()
                current_sql = graph.forward_sql()
            else:
                # Optimized updates are already in graph.v_plan.value and graph.v_sql.value
                current_plan = graph.v_plan.value
                current_sql = graph.v_sql.value

            # 2. Forward Database Execution & Loss
            current_exec, loss_output = graph.forward_execute(gold_result=gold_result)

            # 3. Backward Pass (Textual Gradient Calculation)
            sql_grad, plan_grad, avg_norm = graph.backward(loss_output=loss_output, step=iteration)
            gradient_norms.append(avg_norm)

            # 4. Adaptive Stopping Decision
            decision = controller.evaluate(
                iteration=iteration,
                exec_result=current_exec,
                loss_output=loss_output,
                gradient_norm=avg_norm,
                gradient_history=gradient_norms,
            )

            iter_duration = time.perf_counter() - iter_start

            trace = IterationTrace(
                iteration=iteration,
                plan_value=current_plan,
                sql_value=current_sql,
                execution_result=current_exec,
                loss_output=loss_output,
                sql_gradient=sql_grad,
                plan_gradient=plan_grad,
                gradient_norm=avg_norm,
                duration_seconds=round(iter_duration, 3),
                exit_decision=decision.reason if decision.should_stop else "CONTINUE",
            )
            history.append(trace)

            # 5. Check Early Exit Condition
            if decision.should_stop:
                final_decision = decision
                break

            # 6. Apply Textual Gradient Descent Optimizer Steps for next iteration
            graph.v_sql.update_value(optimizer.step(graph.v_sql, schema_context=schema_text))
            graph.v_plan.update_value(optimizer.step(graph.v_plan, schema_context=schema_text))

        if final_decision is None:
            # Fallback if loop ended naturally
            final_decision = StoppingDecision(
                should_stop=True,
                reason="Completed scheduled iteration budget.",
                iteration=len(history),
                confidence_score=1.0 - history[-1].loss_output.scalar_loss if history else 0.0,
                current_utility=0.0,
                strategy_used=self.config.stopping_strategy.value,
                details={"status": "NATURAL_TERMINATION"},
            )

        total_time = time.perf_counter() - start_time

        # Check correctness against gold standard if provided
        is_correct = None
        if gold_result and gold_result.success and current_exec.success:
            from axiomsql.engine.parser import SQLParser
            is_correct = SQLParser.compare_execution_results(current_exec.data, gold_result.data)

        return PipelineResult(
            question=question,
            final_sql=current_sql,
            final_plan=current_plan,
            execution_result=current_exec,
            total_iterations=len(history),
            stopping_decision=final_decision,
            history=history,
            total_duration_seconds=round(total_time, 3),
            is_correct=is_correct,
        )
