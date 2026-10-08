"""
Multi-Objective Execution Loss Engine for Text-to-SQL TextGrad Optimization.
Transforms runtime database feedback into structured, differentiable loss signals.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from axiomsql.engine.database import ExecutionResult
from axiomsql.engine.parser import SQLParser


@dataclass
class ExecutionLossOutput:
    """Structured loss signal containing scalar loss, loss breakdown, and textual feedback."""
    scalar_loss: float  # [0.0, 1.0] (0 = optimal, 1 = failure)
    loss_breakdown: Dict[str, float]
    textual_critique_prompt: str
    error_category: str
    execution_success: bool
    row_count: int
    is_exact_match: Optional[bool] = None


class ExecutionLoss:
    """
    Computes differentiable multi-objective execution loss:
    L_exec = w_syntax * L_syntax + w_schema * L_schema + w_card * L_cardinality + w_sem * L_semantic
    """

    def __init__(
        self,
        weight_syntax: float = 0.40,
        weight_schema: float = 0.25,
        weight_cardinality: float = 0.15,
        weight_semantic: float = 0.20,
    ):
        self.w_syntax = weight_syntax
        self.w_schema = weight_schema
        self.w_cardinality = weight_cardinality
        self.w_semantic = weight_semantic

    def compute(
        self,
        pred_result: ExecutionResult,
        question: str,
        schema_summary: str,
        gold_result: Optional[ExecutionResult] = None,
    ) -> ExecutionLossOutput:
        """Evaluates predicted SQL execution result against database and semantic objectives."""
        loss_components: Dict[str, float] = {}
        error_category = "SUCCESS"

        # 1. Syntax & Execution Feasibility Loss
        if not pred_result.success:
            loss_components["syntax"] = 1.0
            error_category = "SYNTAX_OR_RUNTIME_ERROR"
        else:
            loss_components["syntax"] = 0.0

        # 2. Result Cardinality Loss (Empty Result Trap)
        # In Text-to-SQL, queries that return 0 rows are frequently caused by over-constrained WHERE clauses or wrong JOINs.
        if pred_result.success and pred_result.row_count == 0:
            loss_components["cardinality"] = 0.8
            if error_category == "SUCCESS":
                error_category = "EMPTY_RESULT_SET"
        else:
            loss_components["cardinality"] = 0.0

        # 3. Schema Grounding Loss
        # Detect if query has unresolved identifiers or empty columns
        if pred_result.success and len(pred_result.columns) == 0:
            loss_components["schema"] = 0.7
        else:
            loss_components["schema"] = 0.0

        # 4. Semantic / Ground-Truth Equivalence Loss (if gold result is provided)
        is_exact_match = None
        if gold_result is not None:
            if pred_result.success and gold_result.success:
                matches = SQLParser.compare_execution_results(pred_result.data, gold_result.data)
                is_exact_match = matches
                loss_components["semantic"] = 0.0 if matches else 0.85
                if not matches and error_category == "SUCCESS":
                    error_category = "SEMANTIC_VALUE_MISMATCH"
            else:
                loss_components["semantic"] = 1.0
                is_exact_match = False
        else:
            # Unsupervised execution mode: confidence derived from successful non-empty retrieval
            loss_components["semantic"] = 0.0 if (pred_result.success and pred_result.row_count > 0) else 0.5

        # Weighted aggregate scalar loss
        scalar_loss = (
            self.w_syntax * loss_components["syntax"]
            + self.w_schema * loss_components["schema"]
            + self.w_cardinality * loss_components["cardinality"]
            + self.w_semantic * loss_components["semantic"]
        )
        scalar_loss = min(1.0, max(0.0, scalar_loss))

        # Build informative textual critique prompt for backward TextGrad pass
        textual_critique = self._build_critique_text(
            pred_result=pred_result,
            question=question,
            schema_summary=schema_summary,
            loss_components=loss_components,
            error_category=error_category,
            gold_result=gold_result,
        )

        return ExecutionLossOutput(
            scalar_loss=scalar_loss,
            loss_breakdown=loss_components,
            textual_critique_prompt=textual_critique,
            error_category=error_category,
            execution_success=pred_result.success,
            row_count=pred_result.row_count,
            is_exact_match=is_exact_match,
        )

    def _build_critique_text(
        self,
        pred_result: ExecutionResult,
        question: str,
        schema_summary: str,
        loss_components: Dict[str, float],
        error_category: str,
        gold_result: Optional[ExecutionResult],
    ) -> str:
        """Constructs rich feedback text supplied to the backward critique LLM."""
        lines = [
            f"User Natural Language Goal: {question}",
            f"Candidate SQL Query:\n```sql\n{pred_result.query}\n```",
        ]

        if not pred_result.success:
            lines.append(f"EXECUTION FAILURE (SQLite Exception): {pred_result.error_message}")
            lines.append("Required Action: Diagnose the exact syntax error or missing table/column. Check schema foreign keys.")
        elif pred_result.row_count == 0:
            lines.append("EXECUTION WARNING: Query executed without error but returned 0 rows (Empty Result Set).")
            lines.append("Required Action: Check WHERE filters, string literals, and join conditions for excessive constraints.")
        else:
            lines.append(f"EXECUTION SUCCESS: Query produced {pred_result.row_count} rows with columns {pred_result.columns}.")
            if pred_result.row_count <= 3:
                lines.append(f"Sample Output Rows: {pred_result.data[:3]}")

        if gold_result and gold_result.success:
            if pred_result.success and not SQLParser.compare_execution_results(pred_result.data, gold_result.data):
                lines.append(f"DISCREPANCY DETECTED: Expected {gold_result.row_count} rows, but candidate query yielded {pred_result.row_count} rows.")
                lines.append(f"Expected Sample Rows: {gold_result.data[:2]}")

        lines.append(f"Loss Scalar: {sum(loss_components.values()):.2f} (Error Category: {error_category})")
        return "\n".join(lines)
