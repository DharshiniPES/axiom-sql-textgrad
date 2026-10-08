"""Tests for TextVariable and Differentiable SQL Computational Graph."""

import pytest
from axiomsql.core.variable import TextVariable
from axiomsql.core.computational_graph import SQLComputationalGraph
from axiomsql.engine.database import DatabaseSandbox
from axiomsql.engine.llm_backend import OfflineNeuralSimulator


def test_text_variable_gradient_accumulation():
    var = TextVariable(
        value="SELECT * FROM users;",
        role_description="SQL Synthesizer",
        name="v_sql",
        trainable=True,
    )
    assert var.trainable is True
    assert len(var.gradients) == 0

    var.accumulate_gradient("Missing WHERE condition on age > 21", norm=0.8)
    assert len(var.gradients) == 1
    assert var.average_gradient_norm == 0.8
    assert "Missing WHERE" in (var.current_gradient or "")

    var.zero_grad()
    assert len(var.gradients) == 0


def test_computational_graph_forward_and_backward():
    sandbox = DatabaseSandbox(":memory:")
    sandbox._conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, age INTEGER);")
    sandbox._conn.execute("INSERT INTO users VALUES (1, 25), (2, 30);")
    sandbox._conn.commit()

    llm = OfflineNeuralSimulator()
    graph = SQLComputationalGraph(llm=llm, sandbox=sandbox)
    graph.initialize_graph(
        question="Find users older than 20",
        schema_summary="Table: users\n  Columns: id (INTEGER), age (INTEGER)"
    )

    plan = graph.forward_plan()
    assert len(plan) > 0

    sql = graph.forward_sql()
    assert len(sql) > 0

    res, loss_output = graph.forward_execute()
    assert res is not None
    assert loss_output is not None

    sql_grad, plan_grad, avg_norm = graph.backward(loss_output, step=1)
    assert len(sql_grad) > 0
    assert len(plan_grad) > 0
    assert 0.0 <= avg_norm <= 1.0

    sandbox.close()
