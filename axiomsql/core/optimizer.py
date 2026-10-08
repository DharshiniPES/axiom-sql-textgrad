"""
Textual Gradient Optimizer (TGD with Momentum and Anti-Oscillation Memory).
Applies textual gradient updates to prompt and plan variables in the computational graph.
"""

from typing import Dict, List, Optional
from axiomsql.core.variable import TextVariable
from axiomsql.engine.llm_backend import BaseLLM


class TextualGradientOptimizer:
    """
    Optimizes TextVariables using textual gradients:
    v_{t+1} = Step(v_t, \\nabla_{v_t} L, Memory_t)
    """

    def __init__(
        self,
        llm: BaseLLM,
        learning_rate: str = "moderate",  # "conservative", "moderate", "aggressive"
        enable_momentum: bool = True,
        max_memory_history: int = 5,
    ):
        self.llm = llm
        self.learning_rate = learning_rate
        self.enable_momentum = enable_momentum
        self.max_memory_history = max_memory_history
        self.optimization_steps: int = 0
        self.memory_buffer: Dict[str, List[Dict[str, str]]] = {}

    def step(self, variable: TextVariable, schema_context: str = "") -> str:
        """Applies textual gradient update to the given variable."""
        if not variable.trainable:
            return variable.value

        gradients = variable.gradients
        if not gradients:
            return variable.value

        latest_gradient = gradients[-1]
        var_name = variable.name

        if var_name not in self.memory_buffer:
            self.memory_buffer[var_name] = []

        # Record into memory buffer
        self.memory_buffer[var_name].append({
            "previous_value": variable.value,
            "gradient": latest_gradient,
        })
        if len(self.memory_buffer[var_name]) > self.max_memory_history:
            self.memory_buffer[var_name].pop(0)

        # Build optimizer prompt
        system_prompt = (
            "You are a Mathematical Textual Gradient Optimizer (TGD) for Relational Database Systems. "
            "Your objective is to update a textual parameter variable based on execution gradients and critiques. "
            "Address all flaws identified in the textual gradient directly. "
            "Do NOT repeat past failed patterns recorded in the memory buffer."
        )

        memory_context = ""
        if self.enable_momentum and len(self.memory_buffer[var_name]) > 1:
            history_snippets = []
            for idx, item in enumerate(self.memory_buffer[var_name][:-1]):
                history_snippets.append(
                    f"Iteration {idx}: Attempt had gradient '{item['gradient'][:120]}...'"
                )
            memory_context = (
                "\n### Momentum & Rejection History (DO NOT RE-EXPLORE THESE FAILED PATHS):\n"
                + "\n".join(history_snippets)
            )

        optimizer_prompt = f"""
### Parameter Under Optimization:
Variable Name: {variable.name}
Role: {variable.role_description}

### Current Variable Value:
{variable.value}

### Textual Gradient (Feedback & Execution Critique):
{latest_gradient}

### Schema Context:
{schema_context}
{memory_context}

### Optimization Instructions:
Update the variable to resolve all critiques in the textual gradient.
Provide ONLY the updated, improved content for '{variable.name}'. Do not wrap in conversational preamble.
"""

        from axiomsql.engine.parser import SQLParser

        updated_text = self.llm.generate(
            prompt=optimizer_prompt,
            system_prompt=system_prompt,
            temperature=0.2 if self.learning_rate == "conservative" else 0.4,
        )

        if variable.name == "v_sql":
            updated_text = SQLParser.extract_sql(updated_text)

        variable.update_value(updated_text)
        self.optimization_steps += 1
        return updated_text
