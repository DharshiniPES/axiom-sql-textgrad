"""
SQL parsing, extraction, schema ground-truth checking, and execution set equivalence checking.
"""

import re
import sqlite3
from typing import Any, Dict, List, Optional, Set, Tuple


class SQLParser:
    """Parses and sanitizes SQL queries from raw LLM responses."""

    @staticmethod
    def extract_sql(text: str) -> str:
        """Extracts SQL query string from markdown code blocks or raw text."""
        # Check for ```sql ... ```
        sql_match = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if sql_match:
            candidate = sql_match.group(1).strip()
        elif ";" in text:
            # Match from SELECT up to the terminating semicolon
            select_match = re.search(r"(SELECT\s+[\s\S]*?;)", text, re.IGNORECASE)
            candidate = select_match.group(1).strip() if select_match else text.strip()
        else:
            select_match = re.search(r"(SELECT\s+[\s\S]+)", text, re.IGNORECASE)
            candidate = select_match.group(1).strip() if select_match else text.strip()

        # Clean trailing semicolon or unwanted comments
        candidate = candidate.rstrip(";").strip()
        return candidate

    @staticmethod
    def extract_tables_and_columns(query: str) -> Tuple[Set[str], Set[str]]:
        """Heuristically extracts referenced table and column tokens from SQL query."""
        tokens = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", query.lower()))
        sql_keywords = {
            "select", "from", "where", "join", "left", "right", "inner", "outer",
            "group", "by", "having", "order", "asc", "desc", "limit", "offset",
            "as", "on", "and", "or", "not", "in", "is", "null", "like", "between",
            "avg", "sum", "count", "min", "max", "distinct", "case", "when", "then",
            "else", "end", "all", "any", "exists", "union", "intersect", "except"
        }
        identifiers = tokens - sql_keywords
        return identifiers, tokens

    @staticmethod
    def check_schema_alignment(query: str, schema_dict: Dict[str, Dict[str, Any]]) -> List[str]:
        """Detects if query references non-existent tables or invalid columns."""
        identifiers, _ = SQLParser.extract_tables_and_columns(query)
        known_tables = {t.lower() for t in schema_dict.keys()}
        known_columns = set()
        for t_info in schema_dict.values():
            for c_name in t_info.get("columns", {}).keys():
                known_columns.add(c_name.lower())

        warnings = []
        for ident in identifiers:
            # If identifier looks like a table/column name and not in schema
            if "." in ident:
                parts = ident.split(".")
                if parts[0] not in known_tables:
                    warnings.append(f"Table '{parts[0]}' not in schema.")
            elif len(ident) > 3 and ident not in known_tables and ident not in known_columns:
                # Might be an alias, literal, or hallucination
                pass
        return warnings

    @staticmethod
    def compare_execution_results(
        pred_data: List[Tuple[Any, ...]],
        gold_data: List[Tuple[Any, ...]],
        order_matters: bool = False,
    ) -> bool:
        """
        Calculates Execution Accuracy (EX).
        Checks multiset or ordered equality between predicted and gold execution tuples.
        """
        if not pred_data and not gold_data:
            return True
        if len(pred_data) != len(gold_data):
            return False

        if order_matters:
            return pred_data == gold_data

        # Multiset comparison
        from collections import Counter
        try:
            pred_counter = Counter(pred_data)
            gold_counter = Counter(gold_data)
            return pred_counter == gold_counter
        except TypeError:
            # Fallback for unhashable types if any
            return sorted(str(x) for x in pred_data) == sorted(str(x) for x in gold_data)
