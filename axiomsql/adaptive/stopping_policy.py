"""
Adaptive Stopping Policy and Dynamic Reiteration Controller for AxiomSQL.
Dynamically decides whether to stop or continue prompt refinement after each iteration
based on execution feedback, textual gradient norms, and Pareto cost-accuracy tradeoffs.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
from axiomsql.core.loss import ExecutionLossOutput
from axiomsql.engine.database import ExecutionResult


class StoppingStrategy(str, Enum):
    EXECUTION_GATED = "execution_gated"       # Exit upon valid, non-empty, schema-grounded execution
    GRADIENT_CONVERGENCE = "gradient_convergence" # Exit when textual gradient energy drops below threshold
    PARETO_UTILITY = "pareto_utility"         # Balance execution quality against cumulative iteration compute cost
    FIXED_BUDGET = "fixed_budget"             # Always exhaust max_iterations budget


@dataclass
class StoppingDecision:
    """The decision output from the Adaptive Controller after an iteration."""
    should_stop: bool
    reason: str
    iteration: int
    confidence_score: float
    current_utility: float
    strategy_used: str
    details: Dict[str, str]


class AdaptiveStoppingController:
    """
    Evaluates whether the optimization loop should terminate or proceed to iteration t + 1.
    Formulation:
      Decision_t = pi_exit(Result_t, Loss_t, GradNorm_t, t; Theta_hyperparams)
    """

    def __init__(
        self,
        strategy: StoppingStrategy = StoppingStrategy.EXECUTION_GATED,
        max_iterations: int = 4,
        tau_confidence: float = 0.85,
        grad_energy_threshold: float = 0.15,
        cost_penalty_lambda: float = 0.08,
    ):
        self.strategy = strategy
        self.max_iterations = max_iterations
        self.tau_confidence = tau_confidence
        self.grad_energy_threshold = grad_energy_threshold
        self.cost_penalty_lambda = cost_penalty_lambda

    def evaluate(
        self,
        iteration: int,
        exec_result: ExecutionResult,
        loss_output: ExecutionLossOutput,
        gradient_norm: float,
        gradient_history: List[float],
    ) -> StoppingDecision:
        """
        Evaluates dynamic exit conditions at iteration step t (1-indexed).
        Returns StoppingDecision indicating whether to exit and the formal reason.
        """
        # Hard Upper Bound: Max iterations hyperparameter exhausted
        if iteration >= self.max_iterations:
            return StoppingDecision(
                should_stop=True,
                reason=f"Hyperparameter budget reached: exhausted maximum iterations ({self.max_iterations}).",
                iteration=iteration,
                confidence_score=1.0 - loss_output.scalar_loss,
                current_utility=(1.0 - loss_output.scalar_loss) - (self.cost_penalty_lambda * iteration),
                strategy_used=self.strategy.value,
                details={"status": "BUDGET_EXHAUSTED"},
            )

        confidence_score = 1.0 - loss_output.scalar_loss
        current_utility = confidence_score - (self.cost_penalty_lambda * iteration)

        # Strategy 1: Execution-Gated Early Exit (EGEE)
        if self.strategy == StoppingStrategy.EXECUTION_GATED:
            # Clean execution: no SQL error, non-empty result set, no schema failure
            if exec_result.success and exec_result.row_count > 0 and loss_output.loss_breakdown.get("schema", 0) == 0:
                if loss_output.scalar_loss <= (1.0 - self.tau_confidence):
                    return StoppingDecision(
                        should_stop=True,
                        reason=(
                            f"Execution-Gated Early Exit: clean query execution succeeded with "
                            f"{exec_result.row_count} rows, zero schema violations, and confidence "
                            f"{confidence_score:.2f} >= threshold {self.tau_confidence:.2f}."
                        ),
                        iteration=iteration,
                        confidence_score=confidence_score,
                        current_utility=current_utility,
                        strategy_used=self.strategy.value,
                        details={"status": "CLEAN_EXECUTION_EARLY_EXIT"},
                    )

        # Strategy 2: Textual Gradient Energy Convergence (TGC)
        elif self.strategy == StoppingStrategy.GRADIENT_CONVERGENCE:
            if exec_result.success and gradient_norm <= self.grad_energy_threshold:
                return StoppingDecision(
                    should_stop=True,
                    reason=(
                        f"Gradient Convergence: Textual critique gradient energy ({gradient_norm:.3f}) "
                        f"dropped below convergence threshold ({self.grad_energy_threshold:.3f}). "
                        f"Query plan has stabilized."
                    ),
                    iteration=iteration,
                    confidence_score=confidence_score,
                    current_utility=current_utility,
                    strategy_used=self.strategy.value,
                    details={"status": "GRADIENT_CONVERGED"},
                )

        # Strategy 3: Pareto Utility Stopping (PUS)
        elif self.strategy == StoppingStrategy.PARETO_UTILITY:
            # If current confidence is high enough that an additional iteration's cost outweighs expected gains
            if exec_result.success and confidence_score >= self.tau_confidence:
                expected_gain = 0.05  # diminishing returns
                if expected_gain < self.cost_penalty_lambda:
                    return StoppingDecision(
                        should_stop=True,
                        reason=(
                            f"Pareto Optimal Exit: Marginal utility gain ({expected_gain:.3f}) is less than "
                            f"iteration compute penalty lambda ({self.cost_penalty_lambda:.3f}). "
                            f"Current Pareto Utility: {current_utility:.3f}."
                        ),
                        iteration=iteration,
                        confidence_score=confidence_score,
                        current_utility=current_utility,
                        strategy_used=self.strategy.value,
                        details={"status": "PARETO_OPTIMAL"},
                    )

        # Strategy 4: Fixed Budget
        elif self.strategy == StoppingStrategy.FIXED_BUDGET:
            # Continue until max_iterations
            pass

        # If none of the early exit conditions triggered, proceed with refinement
        return StoppingDecision(
            should_stop=False,
            reason=(
                f"Continue Refinement: Candidate query at iteration {iteration} has residual loss "
                f"L={loss_output.scalar_loss:.2f} (Error: {loss_output.error_category}). "
                f"Gradient energy: {gradient_norm:.2f}."
            ),
            iteration=iteration,
            confidence_score=confidence_score,
            current_utility=current_utility,
            strategy_used=self.strategy.value,
            details={"status": "CONTINUE_REFINEMENT"},
        )
