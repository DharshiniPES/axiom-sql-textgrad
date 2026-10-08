"""Tests for Adaptive Stopping Policy and Dynamic Reiteration Hyperparameter Controller."""

import pytest
from axiomsql.adaptive.stopping_policy import (
    AdaptiveStoppingController,
    StoppingStrategy,
)
from axiomsql.core.loss import ExecutionLossOutput
from axiomsql.engine.database import ExecutionResult


def test_stopping_at_max_iterations_bound():
    controller = AdaptiveStoppingController(
        strategy=StoppingStrategy.FIXED_BUDGET,
        max_iterations=3,
    )
    dummy_exec = ExecutionResult(query="SELECT 1", success=False)
    dummy_loss = ExecutionLossOutput(
        scalar_loss=0.8,
        loss_breakdown={},
        textual_critique_prompt="",
        error_category="SYNTAX_ERROR",
        execution_success=False,
        row_count=0,
    )

    decision_1 = controller.evaluate(1, dummy_exec, dummy_loss, 0.8, [0.8])
    assert decision_1.should_stop is False

    decision_2 = controller.evaluate(2, dummy_exec, dummy_loss, 0.7, [0.8, 0.7])
    assert decision_2.should_stop is False

    decision_3 = controller.evaluate(3, dummy_exec, dummy_loss, 0.7, [0.8, 0.7, 0.7])
    assert decision_3.should_stop is True
    assert "budget reached" in decision_3.reason.lower()


def test_execution_gated_early_exit():
    controller = AdaptiveStoppingController(
        strategy=StoppingStrategy.EXECUTION_GATED,
        max_iterations=5,
        tau_confidence=0.80,
    )
    clean_exec = ExecutionResult(
        query="SELECT name FROM users;",
        success=True,
        data=[("Alice",)],
        columns=["name"],
        row_count=1,
    )
    clean_loss = ExecutionLossOutput(
        scalar_loss=0.05,
        loss_breakdown={"schema": 0.0},
        textual_critique_prompt="Success",
        error_category="SUCCESS",
        execution_success=True,
        row_count=1,
    )

    decision = controller.evaluate(1, clean_exec, clean_loss, 0.05, [0.05])
    assert decision.should_stop is True
    assert "Early Exit" in decision.reason
    assert decision.iteration == 1


def test_gradient_convergence_stopping():
    controller = AdaptiveStoppingController(
        strategy=StoppingStrategy.GRADIENT_CONVERGENCE,
        max_iterations=5,
        grad_energy_threshold=0.10,
    )
    exec_res = ExecutionResult(query="SELECT 1;", success=True, row_count=1)
    loss = ExecutionLossOutput(
        scalar_loss=0.1,
        loss_breakdown={},
        textual_critique_prompt="",
        error_category="SUCCESS",
        execution_success=True,
        row_count=1,
    )

    # First step: high gradient energy -> continue
    d1 = controller.evaluate(1, exec_res, loss, 0.45, [0.45])
    assert d1.should_stop is False

    # Second step: low gradient energy (0.05 < 0.10) -> stop
    d2 = controller.evaluate(2, exec_res, loss, 0.05, [0.45, 0.05])
    assert d2.should_stop is True
    assert "Gradient Convergence" in d2.reason


def test_pareto_utility_stopping():
    controller = AdaptiveStoppingController(
        strategy=StoppingStrategy.PARETO_UTILITY,
        max_iterations=5,
        tau_confidence=0.85,
        cost_penalty_lambda=0.10,
    )
    exec_res = ExecutionResult(query="SELECT 1;", success=True, row_count=1)
    loss = ExecutionLossOutput(
        scalar_loss=0.10,  # confidence = 0.90 >= 0.85
        loss_breakdown={},
        textual_critique_prompt="",
        error_category="SUCCESS",
        execution_success=True,
        row_count=1,
    )

    decision = controller.evaluate(2, exec_res, loss, 0.1, [0.3, 0.1])
    assert decision.should_stop is True
    assert "Pareto Optimal Exit" in decision.reason
