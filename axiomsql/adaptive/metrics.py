"""
Convergence metrics, gradient energy trackers, and trajectory telemetry.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ConvergenceMetrics:
    """Holds running statistics across optimization iterations."""
    iteration_count: int
    loss_history: List[float]
    gradient_norm_history: List[float]
    error_reduction_rate: float
    is_converged: bool
    final_exit_reason: str


class GradientEnergyTracker:
    """Tracks semantic gradient norms and detects stagnation or convergence."""

    def __init__(self, window_size: int = 3, convergence_threshold: float = 0.15):
        self.window_size = window_size
        self.convergence_threshold = convergence_threshold
        self.history: List[float] = []

    def record(self, gradient_norm: float) -> None:
        self.history.append(gradient_norm)

    def is_converged(self) -> bool:
        """Returns True if recent gradient norms are consistently below threshold."""
        if not self.history:
            return False
        recent = self.history[-self.window_size:]
        return max(recent) <= self.convergence_threshold

    def is_stagnated(self, tolerance: float = 0.02) -> bool:
        """Detects if gradient norm hasn't improved over recent steps."""
        if len(self.history) < self.window_size:
            return False
        recent = self.history[-self.window_size:]
        return (max(recent) - min(recent)) < tolerance
