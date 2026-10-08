"""
Differentiable Computational Graph for AxiomSQL.
Orchestrates forward multi-stage synthesis and backward textual gradient backpropagation.
"""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional, Tuple
from axiomsql.core.variable import TextVariable, TextGradReport
from axiomsql.core.loss import ExecutionLoss, ExecutionLossOutput
from axiomsql.engine.database import DatabaseSandbox, ExecutionResult
from axiomsql.engine.llm_backend import BaseLLM
from axiomsql.engine.parser import SQLParser


@dataclass
class IterationTrace:
    """Detailed telemetry for a single optimization iteration."""
    iteration: int
    plan_value: str
    sql_value: str
    execution_result: ExecutionResult
    loss_output: ExecutionLossOutput
    sql_gradient: Optional[str] = None
    plan_gradient: Optional[str] = None
    gradient_norm: float = 0.0
    duration_seconds: float = 0.0
    exit_decision: Optional[str] = None


class SQLComputationalGraph:
    """
    Two-stage differentiable computational graph:
    [V_nl, V_schema] -> V_plan -> V_sql -> DatabaseSandbox -> ExecutionLoss
                       ^         ^
                       |_________| (Backward TextGrad Flow)
    """

    def __init__(
        self,
        llm: BaseLLM,
        sandbox: DatabaseSandbox,
        loss_fn: Optional[ExecutionLoss] = None,
    ):
        self.llm = llm
        self.sandbox = sandbox
        self.loss_fn = loss_fn or ExecutionLoss()
        self.variables: Dict[str, TextVariable] = {}
        self.iteration_history: List[IterationTrace] = []

    def initialize_graph(self, question: str, schema_summary: str) -> Tuple[TextVariable, TextVariable]:
        """Sets up the initial computation graph nodes."""
        self.v_nl = TextVariable(
            value=question,
            role_description="Natural language user question specifying data retrieval intent.",
            name="v_nl",
            trainable=False,
        )
        self.v_schema = TextVariable(
            value=schema_summary,
            role_description="Relational database schema containing tables, columns, and foreign keys.",
            name="v_schema",
            trainable=False,
        )

        # Trainable Stage 1: Query Planner
        self.v_plan = TextVariable(
            value="",
            role_description="High-level schema linking, table join plan, and projection strategy.",
            name="v_plan",
            trainable=True,
            predecessors=[self.v_nl, self.v_schema],
        )

        # Trainable Stage 2: SQL Synthesizer
        self.v_sql = TextVariable(
            value="",
            role_description="Synthesized executable SQL query matching target dialect.",
            name="v_sql",
            trainable=True,
            predecessors=[self.v_plan, self.v_schema],
        )

        self.variables = {
            "v_nl": self.v_nl,
            "v_schema": self.v_schema,
            "v_plan": self.v_plan,
            "v_sql": self.v_sql,
        }
        return self.v_plan, self.v_sql

    def forward_plan(self) -> str:
        """Executes forward pass for Stage 1: Schema-Linking & Query Plan."""
        planner_prompt = f"""
You are an expert Relational Database Query Planner.
Given the user question and database schema, formulate a structured Schema-Linking & Query Plan.

Database Schema:
{self.v_schema.value}

User Question:
{self.v_nl.value}

Produce a structured plan containing:
1. Target Tables to query
2. Required Columns & Aggregations
3. Join Path / Conditions using Schema Foreign Keys
4. Filters & WHERE Predicates
5. Grouping or Ordering specifications
"""
        plan_text = self.llm.generate(
            prompt=planner_prompt,
            system_prompt="Formulate an explicit, step-by-step SQL Query Execution Plan.",
            temperature=0.2,
        )
        self.v_plan.update_value(plan_text)
        return plan_text

    def forward_sql(self) -> str:
        """Executes forward pass for Stage 2: SQL Synthesis from Plan and Schema."""
        synthesizer_prompt = f"""
You are an expert SQL Synthesizer.
Generate a valid SQLite query satisfying the given Schema-Linking Plan and User Question.

Database Schema:
{self.v_schema.value}

User Question:
{self.v_nl.value}

Schema-Linking Plan:
{self.v_plan.value}

Requirements:
- Output ONLY the valid executable SQLite query inside ```sql ... ``` code block.
- Use explicit JOIN syntax with ON conditions.
- Ensure column names exactly match the schema.
"""
        raw_output = self.llm.generate(
            prompt=synthesizer_prompt,
            system_prompt="Generate clean, valid SQLite code matching the schema and plan.",
            temperature=0.2,
        )
        sql_query = SQLParser.extract_sql(raw_output)
        self.v_sql.update_value(sql_query)
        return sql_query

    def forward_execute(self, gold_result: Optional[ExecutionResult] = None) -> Tuple[ExecutionResult, ExecutionLossOutput]:
        """Executes synthesized SQL against the database sandbox and calculates loss."""
        sql_query = self.v_sql.value
        exec_result = self.sandbox.execute_query(sql_query)
        loss_output = self.loss_fn.compute(
            pred_result=exec_result,
            question=self.v_nl.value,
            schema_summary=self.v_schema.value,
            gold_result=gold_result,
        )
        return exec_result, loss_output

    def backward(self, loss_output: ExecutionLossOutput, step: int) -> Tuple[str, str, float]:
        """
        Backpropagates execution loss through the computational graph:
        1. Calculates gradient nabla_{v_sql} L_exec
        2. Propagates gradient upstream to nabla_{v_plan} L_exec
        """
        self.v_sql.zero_grad()
        self.v_plan.zero_grad()

        # Step 1: Backward pass to v_sql
        sql_critic_prompt = f"""
You are an Automatic Differentiation Critic evaluating SQL code execution errors.
User Question: {self.v_nl.value}
Schema:
{self.v_schema.value}

Candidate SQL:
{self.v_sql.value}

Execution Feedback & Loss:
{loss_output.textual_critique_prompt}

TASK:
Compute the textual gradient (criticism and required gradient direction) for the SQL Synthesizer.
Identify what specific SQL clauses, columns, joins, or logic need to change.
End with: 'GRADIENT_ENERGY: <float between 0.0 and 1.0>' representing the magnitude of error.
"""
        sql_gradient = self.llm.generate(
            prompt=sql_critic_prompt,
            system_prompt="Compute exact textual gradient for SQL Synthesizer variable.",
            temperature=0.1,
        )
        norm_sql = self._parse_gradient_energy(sql_gradient, loss_output.scalar_loss)
        report_sql = TextGradReport(
            step=step,
            target_variable="v_sql",
            gradient_text=sql_gradient,
            loss_summary=loss_output.error_category,
            gradient_norm=norm_sql,
        )
        self.v_sql.accumulate_gradient(sql_gradient, norm=norm_sql, report=report_sql)

        # Step 2: Upstream Backward pass to v_plan
        plan_critic_prompt = f"""
You are an Automatic Differentiation Critic evaluating high-level Query Plans.
The downstream SQL Synthesizer failed or required correction with the following gradient:

Downstream SQL Gradient:
{sql_gradient}

Current High-Level Plan:
{self.v_plan.value}

Database Schema:
{self.v_schema.value}

TASK:
Compute the upstream textual gradient for the Query Plan variable.
Did the high-level plan fail to link the correct tables, specify wrong join keys, or omit necessary groupings?
End with: 'GRADIENT_ENERGY: <float between 0.0 and 1.0>'.
"""
        plan_gradient = self.llm.generate(
            prompt=plan_critic_prompt,
            system_prompt="Compute upstream textual gradient for Schema Linking Plan variable.",
            temperature=0.1,
        )
        norm_plan = self._parse_gradient_energy(plan_gradient, norm_sql * 0.8)
        report_plan = TextGradReport(
            step=step,
            target_variable="v_plan",
            gradient_text=plan_gradient,
            loss_summary=loss_output.error_category,
            gradient_norm=norm_plan,
        )
        self.v_plan.accumulate_gradient(plan_gradient, norm=norm_plan, report=report_plan)

        avg_norm = (norm_sql + norm_plan) / 2.0
        return sql_gradient, plan_gradient, avg_norm

    def _parse_gradient_energy(self, text: str, fallback: float) -> float:
        import re
        match = re.search(r"GRADIENT_ENERGY:\s*([0-9\.]+)", text, re.IGNORECASE)
        if match:
            try:
                val = float(match.group(1))
                return max(0.0, min(1.0, val))
            except ValueError:
                pass
        return max(0.0, min(1.0, fallback))
