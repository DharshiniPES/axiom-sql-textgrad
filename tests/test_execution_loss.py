"""Tests for Multi-Objective Execution Loss computation."""

import pytest
from axiomsql.core.loss import ExecutionLoss
from axiomsql.engine.database import ExecutionResult


def test_execution_loss_syntax_error():
    loss_fn = ExecutionLoss()
    fail_res = ExecutionResult(
        query="SELECT * FROM missing;",
        success=False,
        error_message="no such table: missing"
    )
    loss = loss_fn.compute(
        pred_result=fail_res,
        question="Get all missing records",
        schema_summary="Table: customers\n  Columns: id",
    )

    assert loss.execution_success is False
    assert loss.loss_breakdown["syntax"] == 1.0
    assert loss.scalar_loss >= 0.40
    assert "EXECUTION FAILURE" in loss.textual_critique_prompt
    assert loss.error_category == "SYNTAX_OR_RUNTIME_ERROR"


def test_execution_loss_empty_result_penalty():
    loss_fn = ExecutionLoss()
    empty_res = ExecutionResult(
        query="SELECT * FROM customers WHERE id = 99999;",
        success=True,
        data=[],
        columns=["id", "name"],
        row_count=0,
    )
    loss = loss_fn.compute(
        pred_result=empty_res,
        question="Find customer 99999",
        schema_summary="Table: customers\n  Columns: id, name",
    )

    assert loss.execution_success is True
    assert loss.row_count == 0
    assert loss.loss_breakdown["cardinality"] == 0.8
    assert "EMPTY_RESULT_SET" in loss.error_category
    assert "0 rows" in loss.textual_critique_prompt


def test_execution_loss_success():
    loss_fn = ExecutionLoss()
    success_res = ExecutionResult(
        query="SELECT name FROM customers;",
        success=True,
        data=[("Alice",), ("Bob",)],
        columns=["name"],
        row_count=2,
    )
    loss = loss_fn.compute(
        pred_result=success_res,
        question="Find all customer names",
        schema_summary="Table: customers\n  Columns: name",
    )

    assert loss.execution_success is True
    assert loss.row_count == 2
    assert loss.loss_breakdown["syntax"] == 0.0
    assert loss.loss_breakdown["cardinality"] == 0.0
    assert loss.error_category == "SUCCESS"
