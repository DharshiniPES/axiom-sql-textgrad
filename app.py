"""
AxiomSQL Interactive Live Demo Application.
Streamlit-based visual studio for iterative prompt refinement using TextGrad and adaptive stopping.
"""

import os
import sys
import time
import pandas as pd
import streamlit as st

# Ensure axiomsql package is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from axiomsql.core.pipeline import AxiomSQLPipeline, PipelineConfig
from axiomsql.adaptive.stopping_policy import StoppingStrategy
from axiomsql.benchmark.datasets import (
    BENCHMARK_SUITE,
    create_benchmark_sandbox,
)
from axiomsql.benchmark.evaluator import BenchmarkEvaluator
from axiomsql.engine.llm_backend import (
    OfflineNeuralSimulator,
    GeminiLLM,
    OpenAILLM,
)
from axiomsql.utils.formatting import compute_text_diff, format_table_markdown


# Page Configuration
st.set_page_config(
    page_title="AxiomSQL: TextGrad SQL Planning with Adaptive Stopping",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1E88E5, #43A047);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #555;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 12px 16px;
        border-left: 4px solid #1E88E5;
        margin-bottom: 12px;
    }
    .stCodeBlock {
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)


# Sidebar Configuration
st.sidebar.title("⚡ AxiomSQL Engine")
st.sidebar.caption("Execution-Gated Textual Gradient Optimization")

# 1. Model Provider
provider = st.sidebar.selectbox(
    "LLM Provider Backend",
    options=["Offline Neural Simulator (Zero-API Friction)", "Google Gemini", "OpenAI"],
    index=0,
    help="Offline simulator provides instant, deterministic execution. Toggle to Gemini/OpenAI with your API key.",
)

api_key = ""
llm_instance = None
if provider == "Google Gemini":
    api_key = st.sidebar.text_input("Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))
    if api_key:
        try:
            llm_instance = GeminiLLM(api_key=api_key)
        except Exception as e:
            st.sidebar.error(f"Error initializing Gemini: {e}")
    else:
        st.sidebar.info("Enter Gemini API key or use Offline Simulator.")
elif provider == "OpenAI":
    api_key = st.sidebar.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    if api_key:
        try:
            llm_instance = OpenAILLM(api_key=api_key)
        except Exception as e:
            st.sidebar.error(f"Error initializing OpenAI: {e}")
    else:
        st.sidebar.info("Enter OpenAI API key or use Offline Simulator.")

if llm_instance is None:
    llm_instance = OfflineNeuralSimulator()

st.sidebar.divider()

# 2. Hyperparameters & Adaptive Stopping
st.sidebar.subheader("🎛️ Hyperparameters")

max_k = st.sidebar.slider(
    "Max Iterations Budget (K_max)",
    min_value=1,
    max_value=8,
    value=4,
    help="Upper bound on prompt refinement iterations.",
)

strategy_map = {
    "Execution-Gated Early Exit (EGEE)": StoppingStrategy.EXECUTION_GATED,
    "Gradient Energy Convergence (TGC)": StoppingStrategy.GRADIENT_CONVERGENCE,
    "Pareto Cost-Accuracy Utility (PUS)": StoppingStrategy.PARETO_UTILITY,
    "Fixed Budget (Exhaust K_max)": StoppingStrategy.FIXED_BUDGET,
}
selected_strategy_label = st.sidebar.selectbox(
    "Adaptive Stopping Policy",
    options=list(strategy_map.keys()),
    index=0,
    help="Dynamically decides whether to stop or continue after each iteration based on database feedback.",
)
selected_strategy = strategy_map[selected_strategy_label]

tau_conf = st.sidebar.slider(
    "Confidence Threshold (tau)",
    min_value=0.50,
    max_value=1.00,
    value=0.85,
    step=0.05,
    help="Minimum execution confidence required for early exit.",
)

learning_rate = st.sidebar.selectbox(
    "Optimizer Learning Rate",
    options=["conservative", "moderate", "aggressive"],
    index=1,
)

enable_momentum = st.sidebar.checkbox(
    "Enable Momentum & Anti-Oscillation Memory",
    value=True,
    help="Maintains past rejection history to prevent cyclical query regression.",
)

st.sidebar.divider()
selected_db_id = st.sidebar.selectbox(
    "Relational Database Domain",
    options=["financial", "ecommerce", "healthcare"],
    index=0,
)


# Main Content Area
st.markdown('<div class="main-header">AxiomSQL: Differentiable Text-to-SQL via TextGrad</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    'Iterative Prompt Refinement for Automated SQL Query Planning using Textual Gradients and Adaptive Stopping'
    '</div>',
    unsafe_allow_html=True,
)

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚀 Interactive Query Studio",
    "📈 Trajectory & Gradient Flow",
    "📊 Benchmark Arena",
    "🗄️ Database & Schema Explorer",
    "📜 Research Paper & Formulation",
])


# ==============================================================================
# TAB 1: INTERACTIVE QUERY STUDIO
# ==============================================================================
with tab1:
    col_input, col_ctrl = st.columns([3, 1])

    db_queries = [q for q in BENCHMARK_SUITE if q.db_id == selected_db_id]
    query_labels = [f"[{q.difficulty.upper()}] {q.question}" for q in db_queries]
    query_labels.append("Custom Question (Write your own)")

    with col_input:
        selected_q_idx = st.selectbox("Select Preset Benchmark Question or Custom:", options=range(len(query_labels)), format_func=lambda i: query_labels[i])
        if selected_q_idx < len(db_queries):
            active_q = db_queries[selected_q_idx]
            question_text = st.text_area("Question to synthesize into SQL:", value=active_q.question, height=70)
            gold_sql = active_q.gold_sql
        else:
            question_text = st.text_area("Question to synthesize into SQL:", value="Find the top 3 customers with the highest balance", height=70)
            gold_sql = None

    with col_ctrl:
        st.markdown("<br>", unsafe_allow_html=True)
        run_btn = st.button("🚀 Run AxiomSQL", type="primary", use_container_width=True)

    if run_btn:
        with st.spinner("Executing TextGrad computational graph and iterative backpropagation..."):
            sandbox = create_benchmark_sandbox(selected_db_id)
            gold_res = sandbox.execute_query(gold_sql) if gold_sql else None

            config = PipelineConfig(
                max_iterations=max_k,
                stopping_strategy=selected_strategy,
                tau_confidence=tau_conf,
                learning_rate=learning_rate,
                enable_momentum=enable_momentum,
            )

            pipeline = AxiomSQLPipeline(llm=llm_instance, config=config)
            result = pipeline.run(
                question=question_text,
                sandbox=sandbox,
                gold_result=gold_res,
            )

            # Store result in session state for cross-tab analysis
            st.session_state["latest_result"] = result
            st.session_state["latest_db_id"] = selected_db_id

    if "latest_result" in st.session_state:
        res = st.session_state["latest_result"]

        st.success(f"Optimization Finished in **{res.total_iterations}** iteration(s) | Exit Status: **{res.stopping_decision.details.get('status', 'DONE')}**")

        # Metric Tiles
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total Iterations", f"{res.total_iterations} / {max_k}")
        with m2:
            st.metric("Final Execution Status", "Success ✅" if res.execution_result.success else "Failed ❌")
        with m3:
            st.metric("Rows Returned", res.execution_result.row_count)
        with m4:
            st.metric("Total Pipeline Latency", f"{res.total_duration_seconds * 1000:.1f} ms")

        # Stopping decision rationale alert
        st.info(f"**Adaptive Stopping Controller Rationale:**\n{res.stopping_decision.reason}")

        # Final Synthesized Query and Execution Result
        col_res1, col_res2 = st.columns([1, 1])
        with col_res1:
            st.markdown("#### 📝 Final Synthesized SQL Query")
            st.code(res.final_sql, language="sql")

        with col_res2:
            st.markdown("#### ⚡ Execution Result Set")
            if res.execution_result.success:
                if res.execution_result.data:
                    df_out = pd.DataFrame(res.execution_result.data, columns=res.execution_result.columns)
                    st.dataframe(df_out.head(10), use_container_width=True)
                else:
                    st.warning("Query executed successfully but returned 0 rows.")
            else:
                st.error(f"Execution Error: {res.execution_result.error_message}")

        # Iteration-by-Iteration Breakdown
        st.markdown("---")
        st.markdown("### 🔄 Iterative Refinement Trajectory")

        for trace in res.history:
            with st.expander(f"Iteration {trace.iteration}: Loss = {trace.loss_output.scalar_loss:.2f} | Rows = {trace.execution_result.row_count} | Exit: {trace.exit_decision[:50]}..."):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Stage 1: Schema-Linking Query Plan (V_plan)**")
                    st.info(trace.plan_value)
                    st.markdown("**Stage 2: Candidate SQL Query (V_sql)**")
                    st.code(trace.sql_value, language="sql")
                with c2:
                    st.markdown("**Execution Feedback & Loss Breakdown**")
                    st.write(f"- Syntax Loss: `{trace.loss_output.loss_breakdown.get('syntax', 0.0)}`")
                    st.write(f"- Schema Loss: `{trace.loss_output.loss_breakdown.get('schema', 0.0)}`")
                    st.write(f"- Cardinality Loss: `{trace.loss_output.loss_breakdown.get('cardinality', 0.0)}`")
                    st.write(f"- Gradient Energy Norm: `{trace.gradient_norm:.3f}`")

                    st.markdown("**Textual Gradient (Backward Critique to SQL Synthesizer):**")
                    st.warning(trace.sql_gradient or "No gradient computed.")


# ==============================================================================
# TAB 2: TRAJECTORY & GRADIENT FLOW
# ==============================================================================
with tab2:
    st.markdown("### 📈 TextGrad Computational Graph & Flow")

    st.markdown("""
```mermaid
graph TD
    A["Natural Language Question (V_nl)"] --> C["Query Planner (V_plan)"]
    B["Relational Schema Context (V_schema)"] --> C
    C --> D["SQL Synthesizer (V_sql)"]
    B --> D
    D --> E["Database Engine Sandbox"]
    E --> F["Multi-Objective Loss (L_exec)"]
    F -.->|"nabla_{v_sql} L"| D
    D -.->|"nabla_{v_plan} L"| C
    F --> G["Adaptive Stopping Controller"]
    G -->|"Exit / Continue (K <= K_max)"| H["Terminal Solution"]
```
    """)

    if "latest_result" in st.session_state:
        res = st.session_state["latest_result"]
        if len(res.history) > 1:
            st.markdown("#### 🔍 SQL Evolution Diff (Iteration 1 vs Final)")
            diff = compute_text_diff(res.history[0].sql_value, res.final_sql)
            st.code(diff, language="diff")

        st.markdown("#### 📉 Loss and Gradient Energy Trajectory")
        chart_data = pd.DataFrame({
            "Iteration": [t.iteration for t in res.history],
            "Scalar Loss": [t.loss_output.scalar_loss for t in res.history],
            "Gradient Norm": [t.gradient_norm for t in res.history],
        })
        st.line_chart(chart_data.set_index("Iteration"))
    else:
        st.info("Run a query in the Interactive Studio to inspect gradient trajectories and loss curves.")


# ==============================================================================
# TAB 3: BENCHMARK ARENA
# ==============================================================================
with tab3:
    st.markdown("### 📊 Benchmark Arena & Empirical Comparison")
    st.markdown("Compare **AxiomSQL** against standard **Zero-Shot**, **Few-Shot**, and **Naive Reflexion** across the test suite.")

    if st.button("▶️ Run Full Benchmark Evaluation", type="secondary"):
        with st.spinner("Running comparative evaluation across all benchmark queries..."):
            evaluator = BenchmarkEvaluator(llm=llm_instance)
            df_eval = evaluator.evaluate_all(max_iterations=max_k, stopping_strategy=selected_strategy)
            summary_table = BenchmarkEvaluator.compute_summary_table(df_eval)

            st.session_state["bench_summary"] = summary_table
            st.session_state["bench_raw"] = df_eval

    if "bench_summary" in st.session_state:
        st.markdown("#### 🏆 Overall Benchmark Leaderboard")
        st.dataframe(st.session_state["bench_summary"], use_container_width=True)

        st.markdown("#### 📈 Execution Accuracy (EX) Comparison")
        st.bar_chart(st.session_state["bench_summary"].set_index("Method")["Exec Accuracy EX (%)"])

        st.markdown("#### ⏱️ Iteration Efficiency (Avg K)")
        st.bar_chart(st.session_state["bench_summary"].set_index("Method")["Avg Iterations (K)"])


# ==============================================================================
# TAB 4: DATABASE & SCHEMA EXPLORER
# ==============================================================================
with tab4:
    st.markdown(f"### 🗄️ Relational Database Schema Explorer: `{selected_db_id.upper()}`")
    sb_exp = create_benchmark_sandbox(selected_db_id)
    schema_dict = sb_exp.get_schema_dict()

    for table_name, t_info in schema_dict.items():
        with st.expander(f"📁 Table: `{table_name}` ({len(t_info['columns'])} columns)"):
            cols_df = pd.DataFrame([
                {"Column": c, "Type": d["type"], "Primary Key": d["pk"]}
                for c, d in t_info["columns"].items()
            ])
            st.dataframe(cols_df, use_container_width=True)
            if t_info["foreign_keys"]:
                st.write("**Foreign Keys:**")
                for fk in t_info["foreign_keys"]:
                    st.write(f"- `{fk['from']}` ➔ `{fk['to_table']}.{fk['to_col']}`")

    st.markdown("---")
    st.markdown("#### 🧪 Interactive SQL Scratchpad")
    raw_query = st.text_input("Run direct SQL query against active database:", value=f"SELECT * FROM {list(schema_dict.keys())[0]} LIMIT 5;")
    if st.button("Execute Scratchpad Query"):
        res_scratch = sb_exp.execute_query(raw_query)
        if res_scratch.success:
            st.dataframe(pd.DataFrame(res_scratch.data, columns=res_scratch.columns))
        else:
            st.error(res_scratch.error_message)


# ==============================================================================
# TAB 5: RESEARCH PAPER & FORMULATION
# ==============================================================================
with tab5:
    st.markdown("""
# Iterative Prompt Refinement for Automated SQL Query Planning using TextGrad
**Authors:** Dharshini et al.  
**Abstract:**  
Large Language Models (LLMs) have demonstrated strong capabilities in converting natural-language questions into SQL queries. However, their reliability degrades on complex schemas with multi-table joins and compound predicates. Conventional zero-shot and few-shot prompting lack systematic learning mechanisms from execution failures. We propose **AxiomSQL**, an execution-driven framework formulating Text-to-SQL synthesis as a differentiable computational graph optimized via **TextGrad** with an **Adaptive Iteration Controller**. Database runtime outputs (syntax errors, cardinality anomalies, schema grounding violations) are transformed into structured multi-objective loss vectors, backpropagated as textual gradients through a two-stage computational graph (Query Planning $\to$ SQL Synthesis). Crucially, the iteration count $K$ is governed dynamically by an adaptive stopping policy that balances confidence, gradient energy, and compute costs, eliminating redundant iterations and preventing cyclic regression.

### Mathematical Formulation
1. **Computational Graph:**
   $$\mathcal{G} = (V_{\text{nl}}, V_{\text{schema}}, V_{\text{plan}}, V_{\text{sql}})$$
2. **Multi-Objective Execution Loss:**
   $$\mathcal{L}_{\text{exec}} = w_1 \mathcal{L}_{\text{syntax}} + w_2 \mathcal{L}_{\text{schema}} + w_3 \mathcal{L}_{\text{cardinality}} + w_4 \mathcal{L}_{\text{semantic}}$$
3. **Upstream Textual Gradient Backpropagation:**
   $$\nabla_{V_{\text{sql}}} \mathcal{L}_{\text{exec}} = \text{CriticLLM}(V_{\text{sql}}, \mathcal{L}_{\text{exec}})$$
   $$\nabla_{V_{\text{plan}}} \mathcal{L}_{\text{exec}} = \text{CriticLLM}(V_{\text{plan}}, V_{\text{sql}}, \nabla_{V_{\text{sql}}} \mathcal{L}_{\text{exec}})$$
4. **Adaptive Stopping Rule:**
   $$\pi_{\text{exit}}(s_t) = \mathbb{I}\left( \text{Success}(Q_t) \land \|\nabla_{\text{text}}^{(t)}\| \le \epsilon \lor U(t) \ge \tau \right)$$
""")
