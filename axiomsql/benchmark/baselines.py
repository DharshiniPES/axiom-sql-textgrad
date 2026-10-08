"""
Baseline Text-to-SQL approaches for empirical comparison:
- Zero-Shot Prompting
- Few-Shot Prompting
- Naive Reflexion / Self-Correction
"""

from dataclasses import dataclass
import time
from typing import Optional
from axiomsql.engine.database import DatabaseSandbox, ExecutionResult
from axiomsql.engine.llm_backend import BaseLLM
from axiomsql.engine.parser import SQLParser


@dataclass
class BaselineResult:
    method: str
    query: str
    execution_result: ExecutionResult
    is_correct: bool
    iterations: int
    duration_seconds: float


class ZeroShotBaseline:
    """Conventional Zero-Shot Text-to-SQL Prompting."""

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def run(self, question: str, sandbox: DatabaseSandbox, gold_result: Optional[ExecutionResult] = None) -> BaselineResult:
        t0 = time.perf_counter()
        schema = sandbox.get_schema_summary()
        prompt = f"""
Given the following SQLite schema:
{schema}

Write a single valid SQLite query to answer:
{question}

Return only the query inside ```sql ... ```.
"""
        raw = self.llm.generate(prompt=prompt, system_prompt="You are a SQL expert.")
        sql = SQLParser.extract_sql(raw)
        res = sandbox.execute_query(sql)
        duration = time.perf_counter() - t0

        is_correct = False
        if gold_result and gold_result.success and res.success:
            is_correct = SQLParser.compare_execution_results(res.data, gold_result.data)

        return BaselineResult(
            method="Zero-Shot",
            query=sql,
            execution_result=res,
            is_correct=is_correct,
            iterations=1,
            duration_seconds=round(duration, 3),
        )


class FewShotBaseline:
    """Few-Shot In-Context Learning Text-to-SQL."""

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def run(self, question: str, sandbox: DatabaseSandbox, gold_result: Optional[ExecutionResult] = None) -> BaselineResult:
        t0 = time.perf_counter()
        schema = sandbox.get_schema_summary()
        examples = """
Example 1:
Question: What is the highest balance in accounts?
Query: SELECT MAX(balance) FROM accounts;

Example 2:
Question: Find customer names and their accounts.
Query: SELECT c.name, a.account_id FROM customers c JOIN accounts a ON c.customer_id = a.customer_id;
"""
        prompt = f"""
Database Schema:
{schema}

{examples}

Question:
{question}

Query:
"""
        raw = self.llm.generate(prompt=prompt, system_prompt="Answer with valid SQLite.")
        sql = SQLParser.extract_sql(raw)
        res = sandbox.execute_query(sql)
        duration = time.perf_counter() - t0

        is_correct = False
        if gold_result and gold_result.success and res.success:
            is_correct = SQLParser.compare_execution_results(res.data, gold_result.data)

        return BaselineResult(
            method="Few-Shot",
            query=sql,
            execution_result=res,
            is_correct=is_correct,
            iterations=1,
            duration_seconds=round(duration, 3),
        )


class NaiveReflexionBaseline:
    """Standard Self-Correction / Reflexion without TextGrad or Adaptive Stopping."""

    def __init__(self, llm: BaseLLM, max_retries: int = 3):
        self.llm = llm
        self.max_retries = max_retries

    def run(self, question: str, sandbox: DatabaseSandbox, gold_result: Optional[ExecutionResult] = None) -> BaselineResult:
        t0 = time.perf_counter()
        schema = sandbox.get_schema_summary()

        current_prompt = f"Schema:\n{schema}\n\nQuestion: {question}\nWrite SQL:"
        current_sql = ""
        current_res = ExecutionResult(query="", success=False)
        attempts = 0

        for attempt in range(1, self.max_retries + 1):
            attempts = attempt
            raw = self.llm.generate(prompt=current_prompt)
            current_sql = SQLParser.extract_sql(raw)
            current_res = sandbox.execute_query(current_sql)

            if current_res.success and current_res.row_count > 0:
                break

            # Naive error regurgitation
            err = current_res.error_message or "Query returned 0 rows."
            current_prompt += f"\nPrevious attempt '{current_sql}' failed: {err}\nPlease fix it and output new SQL:"

        duration = time.perf_counter() - t0
        is_correct = False
        if gold_result and gold_result.success and current_res.success:
            is_correct = SQLParser.compare_execution_results(current_res.data, gold_result.data)

        return BaselineResult(
            method="Naive-Reflexion",
            query=current_sql,
            execution_result=current_res,
            is_correct=is_correct,
            iterations=attempts,
            duration_seconds=round(duration, 3),
        )
