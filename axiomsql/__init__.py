"""
AxiomSQL: Adaptive Textual Gradient Optimization with Dynamic Execution Feedback for Multi-Stage SQL Planning.
"""

from axiomsql.core.variable import TextVariable, TextGradReport
from axiomsql.core.computational_graph import SQLComputationalGraph, IterationTrace
from axiomsql.core.loss import ExecutionLoss, ExecutionLossOutput
from axiomsql.core.optimizer import TextualGradientOptimizer
from axiomsql.core.pipeline import AxiomSQLPipeline, PipelineConfig, PipelineResult
from axiomsql.adaptive.stopping_policy import (
    AdaptiveStoppingController,
    StoppingDecision,
    StoppingStrategy,
)
from axiomsql.engine.database import DatabaseSandbox, ExecutionResult
from axiomsql.engine.llm_backend import (
    BaseLLM,
    GeminiLLM,
    OpenAILLM,
    OfflineNeuralSimulator,
)

__version__ = "0.1.0"
__all__ = [
    "AxiomSQLPipeline",
    "PipelineConfig",
    "PipelineResult",
    "TextVariable",
    "TextGradReport",
    "SQLComputationalGraph",
    "IterationTrace",
    "ExecutionLoss",
    "ExecutionLossOutput",
    "TextualGradientOptimizer",
    "AdaptiveStoppingController",
    "StoppingDecision",
    "StoppingStrategy",
    "DatabaseSandbox",
    "ExecutionResult",
    "BaseLLM",
    "GeminiLLM",
    "OpenAILLM",
    "OfflineNeuralSimulator",
]
