"""
Database execution engine and schema introspector for AxiomSQL.
Provides secure sandboxed execution, schema graph extraction, and foreign key topology.
"""

from dataclasses import dataclass, field
import sqlite3
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ExecutionResult:
    """Encapsulates the execution result of an SQL query against a relational database."""
    query: str
    success: bool
    data: List[Tuple[Any, ...]] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)
    row_count: int = 0
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0

    @property
    def is_empty(self) -> bool:
        return self.success and self.row_count == 0


class DatabaseSandbox:
    """Sandboxed SQLite execution engine with schema introspection and integrity checks."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._enable_foreign_keys()

    def _enable_foreign_keys(self) -> None:
        try:
            self._conn.execute("PRAGMA foreign_keys = ON;")
        except Exception:
            pass

    def execute_query(self, query: str, timeout_seconds: float = 5.0) -> ExecutionResult:
        """Executes a SQL query safely and returns structured ExecutionResult."""
        import time

        clean_query = query.strip().rstrip(";")
        start_time = time.perf_counter()

        # Disallow destructive modifications during read-only evaluation
        prohibited = ["drop", "alter", "vacuum", "attach", "detach"]
        first_token = clean_query.split()[0].lower() if clean_query.split() else ""
        if first_token in prohibited:
            return ExecutionResult(
                query=query,
                success=False,
                error_message=f"Disallowed DDL/administrative operation: {first_token.upper()}",
            )

        try:
            cursor = self._conn.cursor()
            cursor.execute(clean_query)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description] if cursor.description else []
            data = [tuple(row) for row in rows]
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            return ExecutionResult(
                query=query,
                success=True,
                data=data,
                columns=columns,
                row_count=len(data),
                error_message=None,
                execution_time_ms=round(duration_ms, 3),
            )
        except sqlite3.Error as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return ExecutionResult(
                query=query,
                success=False,
                data=[],
                columns=[],
                row_count=0,
                error_message=f"SQLite Error: {str(e)}",
                execution_time_ms=round(duration_ms, 3),
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return ExecutionResult(
                query=query,
                success=False,
                data=[],
                columns=[],
                row_count=0,
                error_message=f"Runtime Error: {str(e)}",
                execution_time_ms=round(duration_ms, 3),
            )

    def get_schema_summary(self) -> str:
        """Extracts schema DDL, columns, and foreign key relations into a prompt-friendly string."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()

        schema_lines = []
        for table_name, create_sql in tables:
            # Get table columns
            cursor.execute(f"PRAGMA table_info('{table_name}');")
            cols = cursor.fetchall()
            col_desc = ", ".join([f"{col['name']} ({col['type']})" for col in cols])

            # Get foreign keys
            cursor.execute(f"PRAGMA foreign_key_list('{table_name}');")
            fks = cursor.fetchall()
            fk_desc = ""
            if fks:
                fk_items = [f"{fk['from']} -> {fk['table']}.{fk['to']}" for fk in fks]
                fk_desc = f" [Foreign Keys: {', '.join(fk_items)}]"

            schema_lines.append(f"Table: {table_name}")
            schema_lines.append(f"  Columns: {col_desc}")
            if fk_desc:
                schema_lines.append(f" {fk_desc}")

        return "\n".join(schema_lines)

    def get_schema_dict(self) -> Dict[str, Dict[str, Any]]:
        """Extracts structured schema dictionary with columns, types, primary keys, and foreign keys."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [r[0] for r in cursor.fetchall()]

        schema_dict = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info('{table}');")
            cols = cursor.fetchall()
            columns = {c['name']: {'type': c['type'], 'pk': bool(c['pk'])} for c in cols}

            cursor.execute(f"PRAGMA foreign_key_list('{table}');")
            fks = cursor.fetchall()
            foreign_keys = [{'from': fk['from'], 'to_table': fk['table'], 'to_col': fk['to']} for fk in fks]

            schema_dict[table] = {
                'columns': columns,
                'foreign_keys': foreign_keys,
            }
        return schema_dict

    def close(self) -> None:
        if self._conn:
            self._conn.close()
