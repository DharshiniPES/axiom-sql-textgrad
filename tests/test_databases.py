"""Tests for DatabaseSandbox and schema introspection."""

import pytest
from axiomsql.engine.database import DatabaseSandbox
from axiomsql.benchmark.datasets import create_benchmark_sandbox


def test_database_sandbox_execution():
    sandbox = DatabaseSandbox(":memory:")
    sandbox._conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);")
    sandbox._conn.execute("INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob');")
    sandbox._conn.commit()

    res = sandbox.execute_query("SELECT name FROM users WHERE id = 1;")
    assert res.success is True
    assert res.row_count == 1
    assert res.data == [("Alice",)]
    assert res.columns == ["name"]
    sandbox.close()


def test_database_sandbox_syntax_error():
    sandbox = DatabaseSandbox(":memory:")
    res = sandbox.execute_query("SELECT non_existent FROM missing_tbl;")
    assert res.success is False
    assert "SQLite Error" in (res.error_message or "")
    assert res.row_count == 0
    sandbox.close()


def test_benchmark_database_seeding():
    for db_id in ["financial", "ecommerce", "healthcare"]:
        sb = create_benchmark_sandbox(db_id)
        schema = sb.get_schema_summary()
        assert len(schema) > 50
        assert "Table:" in schema
        sb.close()
