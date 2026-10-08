"""
Differentiable TextVariable representing nodes in the TextGrad computational graph.
Maintains text values, semantic roles, gradient accumulators, and computational ancestry.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TextGradReport:
    """Detailed record of a single gradient computation."""
    step: int
    target_variable: str
    gradient_text: str
    loss_summary: str
    gradient_norm: float  # Estimated semantic critique energy in [0, 1]


class TextVariable:
    """
    A differentiable text variable within the computational graph.
    Analogous to torch.Tensor with requires_grad=True.
    """

    def __init__(
        self,
        value: str,
        role_description: str,
        name: str,
        trainable: bool = True,
        predecessors: Optional[List['TextVariable']] = None,
    ):
        self.value: str = value
        self.role_description: str = role_description
        self.name: str = name
        self.trainable: bool = trainable
        self.predecessors: List['TextVariable'] = predecessors or []
        self.gradients: List[str] = []
        self.gradient_norms: List[float] = []
        self.history: List[str] = [value]
        self.gradient_reports: List[TextGradReport] = []

    def zero_grad(self) -> None:
        """Clears accumulated gradients."""
        self.gradients.clear()
        self.gradient_norms.clear()

    def accumulate_gradient(self, grad_text: str, norm: float = 1.0, report: Optional[TextGradReport] = None) -> None:
        """Appends a textual gradient feedback signal."""
        self.gradients.append(grad_text)
        self.gradient_norms.append(norm)
        if report:
            self.gradient_reports.append(report)

    def update_value(self, new_value: str) -> None:
        """Updates the variable's text value and appends to version history."""
        self.value = new_value
        self.history.append(new_value)

    @property
    def current_gradient(self) -> Optional[str]:
        """Returns the most recent textual gradient or combined gradient text."""
        if not self.gradients:
            return None
        return "\n---\n".join(self.gradients)

    @property
    def average_gradient_norm(self) -> float:
        """Calculates current semantic critique energy magnitude."""
        if not self.gradient_norms:
            return 0.0
        return sum(self.gradient_norms) / len(self.gradient_norms)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "role": self.role_description,
            "trainable": self.trainable,
            "gradients_count": len(self.gradients),
            "latest_gradient": self.gradients[-1] if self.gradients else None,
            "history_length": len(self.history),
        }

    def __repr__(self) -> str:
        return f"<TextVariable(name={self.name}, trainable={self.trainable}, value_len={len(self.value)})>"
