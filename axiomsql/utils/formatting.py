"""
Display utilities, SQL diff computation, and Markdown/HTML formatting.
"""

import difflib
from typing import Any, List, Tuple


def compute_text_diff(text_a: str, text_b: str) -> str:
    """Computes unified diff between two text strings."""
    lines_a = text_a.strip().splitlines()
    lines_b = text_b.strip().splitlines()
    diff = difflib.unified_diff(
        lines_a, lines_b,
        fromfile="Previous", tofile="Refined",
        lineterm=""
    )
    return "\n".join(diff)


def format_table_markdown(columns: List[str], data: List[Tuple[Any, ...]], max_rows: int = 5) -> str:
    """Formats SQL rows as a clean Markdown table."""
    if not columns or not data:
        return "*Empty Result Set (0 rows)*"

    header = "| " + " | ".join(str(c) for c in columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"

    rows = []
    for r in data[:max_rows]:
        row_str = "| " + " | ".join(str(val) for val in r) + " |"
        rows.append(row_str)

    if len(data) > max_rows:
        rows.append(f"| ... ({len(data) - max_rows} more rows) ... |")

    return "\n".join([header, separator] + rows)
