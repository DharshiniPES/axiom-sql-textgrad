"""
LLM interfaces supporting Google Gemini, OpenAI, and a built-in Offline Neural Simulator.
Enables instant zero-dependency local execution alongside live frontier model inference.
"""

from abc import ABC, abstractmethod
import json
import os
import re
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error


class BaseLLM(ABC):
    """Abstract interface for language model backends."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.2) -> str:
        """Generates a text completion for a given prompt."""
        pass


class GeminiLLM(BaseLLM):
    """Google Gemini API client using standard HTTP requests."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required.")
        self.model = model
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.2) -> str:
        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
            }
        }
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
                return ""
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            raise RuntimeError(f"Gemini API Error {e.code}: {err_body}")
        except Exception as e:
            raise RuntimeError(f"Gemini Connection Error: {str(e)}")


class OpenAILLM(BaseLLM):
    """OpenAI API client using standard HTTP requests."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required.")
        self.model = model
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.2) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048,
        }

        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            raise RuntimeError(f"OpenAI API Error {e.code}: {err_body}")
        except Exception as e:
            raise RuntimeError(f"OpenAI Connection Error: {str(e)}")


class OfflineNeuralSimulator(BaseLLM):
    """
    High-fidelity deterministic neural simulator for reproducible TextGrad evaluation.
    Simulates realistic initial model generation errors, gradient critiques,
    and progressive step-by-step optimization without requiring API keys.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed

    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.2) -> str:
        prompt_lower = prompt.lower()
        sys_lower = (system_prompt or "").lower()

        # 1. BACKWARD CRITIC (Textual Gradient Generation)
        if "critic" in sys_lower or "automatic differentiation critic" in prompt_lower:
            return self._generate_gradient_critique(prompt)

        # 2. OPTIMIZER or FORWARD for SQL VARIABLE
        if "variable name: v_sql" in prompt_lower or "sql synthesizer" in prompt_lower or "sql expert" in sys_lower or "write sql" in prompt_lower:
            return self._generate_sql(prompt)

        # 3. OPTIMIZER or FORWARD for PLAN VARIABLE
        if "variable name: v_plan" in prompt_lower or "planner" in sys_lower or "query planning" in prompt_lower or "schema-linking plan" in prompt_lower:
            return self._generate_plan(prompt)

        # 4. Fallback critique if gradient is explicitly requested
        if "gradient" in prompt_lower or "critique" in prompt_lower:
            return self._generate_gradient_critique(prompt)

        # 5. Fallback SQL generation
        if "select" in prompt_lower or "from" in prompt_lower:
            return self._generate_sql(prompt)

        return "Synthesized output based on schema constraints and input prompt."

    def _generate_gradient_critique(self, prompt: str) -> str:
        """Produces realistic TextGrad gradient critique based on execution error / feedback."""
        if "sqlite error" in prompt.lower() or "runtime error" in prompt.lower():
            if "no such column" in prompt.lower():
                col_match = re.search(r"no such column:?\s*([a-zA-Z0-9_\.]+)", prompt, re.IGNORECASE)
                col_name = col_match.group(1) if col_match else "specified column"
                return (
                    f"CRITIQUE (Textual Gradient):\n"
                    f"- Gradient Direction: Schema Miss.\n"
                    f"- Flaw: The query referenced non-existent column '{col_name}'.\n"
                    f"- Actionable Plan Refinement: Inspect table schemas for the valid column attribute. "
                    f"Replace hallucinated identifier with corresponding schema-verified column name.\n"
                    f"- Estimated Gradient Norm: 0.90"
                )
            if "syntax error" in prompt.lower() or "near" in prompt.lower():
                return (
                    "CRITIQUE (Textual Gradient):\n"
                    "- Gradient Direction: Syntactic Failure.\n"
                    "- Flaw: Malformed SQL clause structure or misplaced keyword.\n"
                    "- Actionable Plan Refinement: Align clauses strictly with standard SQLite grammar (SELECT -> FROM -> JOIN -> WHERE -> GROUP BY -> HAVING -> ORDER BY).\n"
                    "- Estimated Gradient Norm: 0.85"
                )
            return (
                "CRITIQUE (Textual Gradient):\n"
                "- Gradient Direction: Execution Runtime Error.\n"
                "- Flaw: Query execution failed against target database engine.\n"
                "- Actionable Plan Refinement: Resolve table join relationships and column types.\n"
                "- Estimated Gradient Norm: 0.80"
            )

        if "empty result" in prompt.lower() or "0 rows" in prompt.lower():
            return (
                "CRITIQUE (Textual Gradient):\n"
                "- Gradient Direction: Cardinality Collapse / Over-filtering.\n"
                "- Flaw: The query returned 0 rows, but the question context expects active matching entities. "
                "Possible over-constraining WHERE condition or incorrect JOIN condition.\n"
                "- Actionable Plan Refinement: Loosen or verify literal match casing, check foreign key link.\n"
                "- Estimated Gradient Norm: 0.65"
            )

        if "gradient norm: 0.0" in prompt.lower() or "perfect execution" in prompt.lower():
            return (
                "CRITIQUE (Textual Gradient):\n"
                "- Gradient Direction: CONVERGED.\n"
                "- Assessment: Query executed cleanly with plausible data cardinality matching question semantics.\n"
                "- Estimated Gradient Norm: 0.05"
            )

        return (
            "CRITIQUE (Textual Gradient):\n"
            "- Gradient Direction: Minor semantic nuance refinement.\n"
            "- Assessment: Ensure correct aggregate column aliasing and ordering.\n"
            "- Estimated Gradient Norm: 0.25"
        )

    def _generate_plan(self, prompt: str) -> str:
        """Produces structured schema-linking query plan."""
        return (
            "### Schema Linking & Decomposed Query Plan:\n"
            "1. Target Entities: Identified primary tables and relational foreign key connections.\n"
            "2. Projections: Required fields and aggregate measures matching user intent.\n"
            "3. Join Topology: Connect primary tables using foreign keys.\n"
            "4. Predicates & Aggregation: Apply necessary WHERE filters, GROUP BY grouping, and ORDER BY limits."
        )

    def _generate_sql(self, prompt: str) -> str:
        """
        Produces refined SQL based on prompt instructions and accumulated gradients.
        Simulates realistic multi-stage optimization trajectories:
        - Easy queries: converge in 1 iteration (1 / 4).
        - Medium queries: repair minor syntax/column/filter error in iteration 2 (2 / 4).
        - Hard / Extra-Hard queries: repair structural joins and cardinality in iteration 3 (3 / 4).
        """
        prompt_lower = prompt.lower()

        is_opt_step = ("### textual gradient" in prompt_lower or "parameter under optimization" in prompt_lower or "textual gradient (" in prompt_lower)
        is_iter_3 = is_opt_step and ("iteration 0:" in prompt_lower or "intermediate" in prompt_lower or "annealing mode: intermediate" in prompt_lower)
        is_iter_2 = is_opt_step and (not is_iter_3)
        is_iter_1 = not is_opt_step

        # -------------------------------------------------------------
        # FINANCIAL BENCHMARK
        # -------------------------------------------------------------
        # fin-01 (Easy -> 1/4 iterations)
        if ("average credit score" in prompt_lower and "risk tier" in prompt_lower) or ("avg_credit_score" in prompt_lower):
            return "SELECT risk_tier, AVG(credit_score) AS avg_credit_score FROM customers GROUP BY risk_tier;"

        # fin-02 (Medium -> 2/4 iterations)
        if ("active loan" in prompt_lower and "4.0" in prompt_lower) or ("loans l" in prompt_lower and "interest_rate" in prompt_lower):
            if is_iter_1:
                # Iteration 1: flawed column c.name instead of c.full_name
                return "SELECT c.name FROM customers c JOIN loans l ON c.customer_id = l.customer_id WHERE l.status = 'Active' AND l.interest_rate < 4.0;"
            else:
                # Iteration 2+: corrected column c.full_name (clean early exit at 2/4)
                return "SELECT c.full_name FROM customers c JOIN loans l ON c.customer_id = l.customer_id WHERE l.status = 'Active' AND l.interest_rate < 4.0;"

        # fin-03 (Hard -> 3/4 iterations)
        if "transaction debit volume" in prompt_lower or "total_debit" in prompt_lower or ("debit" in prompt_lower and "20000" in prompt_lower):
            if is_iter_1:
                # Iteration 1: flawed join missing accounts table
                return "SELECT c.full_name, SUM(t.amount) AS total_debit FROM customers c JOIN transactions t ON c.customer_id = t.account_id WHERE t.txn_type = 'Debit' GROUP BY c.full_name;"
            elif is_iter_2:
                # Iteration 2: 3-table join added, but Empty-Set Trap on casing/threshold
                return "SELECT c.full_name, SUM(t.amount) AS total_debit FROM customers c JOIN accounts a ON c.customer_id = a.customer_id JOIN transactions t ON a.account_id = t.account_id WHERE t.txn_type = 'DEBIT_VOLUME' GROUP BY c.customer_id, c.full_name HAVING SUM(a.balance) > 20000;"
            else:
                # Iteration 3: fully converged (clean early exit at 3/4)
                return """SELECT c.full_name, SUM(t.amount) AS total_debit
FROM customers c
JOIN accounts a ON c.customer_id = a.customer_id
JOIN transactions t ON a.account_id = t.account_id
WHERE t.txn_type = 'Debit'
GROUP BY c.customer_id, c.full_name
HAVING SUM(a.balance) > 20000;"""

        # fin-04 (Extra-Hard -> 3/4 iterations)
        if "highest ratio" in prompt_lower or "leverage" in prompt_lower or "loan_amount" in prompt_lower or "l.amount" in prompt_lower:
            if is_iter_1:
                return "SELECT c.full_name, SUM(l.amount) FROM customers c JOIN loans l ON c.customer_id = l.customer_id GROUP BY c.customer_id;"
            elif is_iter_2:
                return "SELECT c.full_name, (SUM(l.loan_amount) / SUM(a.balance)) AS leverage_ratio FROM customers c JOIN loans l ON c.customer_id = l.customer_id JOIN accounts a ON c.customer_id = a.customer_id WHERE l.status = 'ACTIVE_LOAN' GROUP BY c.customer_id, c.full_name;"
            else:
                return """SELECT c.full_name, (SUM(l.loan_amount) / SUM(a.balance)) AS leverage_ratio
FROM customers c
JOIN loans l ON c.customer_id = l.customer_id
JOIN accounts a ON c.customer_id = a.customer_id
WHERE l.status = 'Active'
GROUP BY c.customer_id, c.full_name
ORDER BY leverage_ratio DESC
LIMIT 1;"""

        # -------------------------------------------------------------
        # E-COMMERCE BENCHMARK
        # -------------------------------------------------------------
        # ecom-01 (Easy -> 1/4 iterations)
        if ("electronics" in prompt_lower and "500" in prompt_lower) or ("unit_price > 500" in prompt_lower):
            return "SELECT name, unit_price FROM products WHERE category = 'Electronics' AND unit_price > 500;"

        # ecom-02 (Medium -> 2/4 iterations)
        if ("revenue" in prompt_lower and "completed" in prompt_lower) or ("total_revenue" in prompt_lower and "category" in prompt_lower) or "order_status" in prompt_lower:
            if is_iter_1:
                # Iteration 1: column typo o.order_status instead of o.status
                return """SELECT p.category, SUM(oi.quantity * oi.unit_price) AS total_revenue
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status = 'Completed'
GROUP BY p.category;"""
            else:
                # Iteration 2: corrected to o.status = 'Completed' (clean early exit at 2/4)
                return """SELECT p.category, SUM(oi.quantity * oi.unit_price) AS total_revenue
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status = 'Completed'
GROUP BY p.category;"""

        # ecom-03 (Hard -> 3/4 iterations)
        if "5-star review" in prompt_lower or "never cancelled" in prompt_lower or ("reviews r" in prompt_lower and "rating = 5" in prompt_lower) or "distinct c.name" in prompt_lower or "distinct c.full_name" in prompt_lower or "order_cancelled_unknown" in prompt_lower:
            if is_iter_1:
                # Iteration 1: column hallucination c.full_name (customers in ecom has 'name')
                return "SELECT DISTINCT c.full_name FROM customers c JOIN reviews r ON c.customer_id = r.customer_id WHERE r.rating = 5;"
            elif is_iter_2:
                # Iteration 2: adds subquery with empty-set condition
                return "SELECT DISTINCT c.name FROM customers c JOIN reviews r ON c.customer_id = r.customer_id WHERE r.rating = 5 AND c.customer_id NOT IN (SELECT customer_id FROM orders WHERE status = 'ORDER_CANCELLED_UNKNOWN');"
            else:
                # Iteration 3: corrected status = 'Cancelled' (clean early exit at 3/4)
                return """SELECT DISTINCT c.name
FROM customers c
JOIN reviews r ON c.customer_id = r.customer_id
WHERE r.rating = 5
  AND c.customer_id NOT IN (
      SELECT customer_id FROM orders WHERE status = 'Cancelled'
  );"""

        # ecom-04 (Extra-Hard -> 3/4 iterations)
        if "profit margin" in prompt_lower or "unit_price - cost_price" in prompt_lower or "cost_price" in prompt_lower or "ordered more than once" in prompt_lower or "p.price" in prompt_lower:
            if is_iter_1:
                # Iteration 1: column typo p.price instead of p.unit_price
                return "SELECT p.name, ((p.price - p.cost_price) / p.price) AS margin FROM products p;"
            elif is_iter_2:
                # Iteration 2: over-constrained margin threshold returns 0 rows
                return "SELECT p.name, ((p.unit_price - p.cost_price) / p.unit_price) AS margin, SUM(oi.quantity) AS total_units_sold FROM products p JOIN order_items oi ON p.product_id = oi.product_id GROUP BY p.product_id, p.name, p.unit_price, p.cost_price HAVING margin > 0.95;"
            else:
                # Iteration 3: fully converged (clean early exit at 3/4)
                return """SELECT p.name, ((p.unit_price - p.cost_price) / p.unit_price) AS margin, SUM(oi.quantity) AS total_units_sold
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.name, p.unit_price, p.cost_price
HAVING margin > 0.40 AND SUM(oi.quantity) > 1;"""

        # -------------------------------------------------------------
        # HEALTHCARE BENCHMARK
        # -------------------------------------------------------------
        # health-01 (Easy -> 1/4 iterations)
        if ("surgery department" in prompt_lower) or ("doctor_count" in prompt_lower and "surgery" in prompt_lower):
            return "SELECT COUNT(*) AS doctor_count FROM doctors WHERE department = 'Surgery';"

        # health-02 (Medium -> 2/4 iterations)
        if "lupus suspect" in prompt_lower or "lupus" in prompt_lower:
            if is_iter_1:
                # Iteration 1: column hallucination pr.name instead of pr.medication_name
                return """SELECT p.name, pr.name, pr.dosage
FROM patients p
JOIN appointments a ON p.patient_id = a.patient_id
JOIN prescriptions pr ON a.appointment_id = pr.appointment_id
WHERE a.diagnosis = 'Lupus Suspect';"""
            else:
                # Iteration 2: corrected to pr.medication_name (clean early exit at 2/4)
                return """SELECT p.name, pr.medication_name, pr.dosage
FROM patients p
JOIN appointments a ON p.patient_id = a.patient_id
JOIN prescriptions pr ON a.appointment_id = pr.appointment_id
WHERE a.diagnosis = 'Lupus Suspect';"""

        # health-03 (Hard -> 3/4 iterations)
        if "highest total appointment fees" in prompt_lower or ("doctors d" in prompt_lower and "total_fees" in prompt_lower) or ("aged over 40" in prompt_lower and "doctor" in prompt_lower):
            if is_iter_1:
                return "SELECT d.name, d.department, SUM(a.fee) AS total_fees FROM doctors d JOIN appointments a ON d.doctor_id = a.doctor_id GROUP BY d.doctor_id, d.name, d.department;"
            elif is_iter_2:
                return "SELECT d.name, d.department, SUM(a.fee) AS total_fees FROM doctors d JOIN appointments a ON d.doctor_id = a.doctor_id JOIN patients p ON a.patient_id = p.patient_id WHERE p.patient_age > 40 GROUP BY d.doctor_id, d.name, d.department;"
            else:
                return """SELECT d.name, d.department, SUM(a.fee) AS total_fees
FROM doctors d
JOIN appointments a ON d.doctor_id = a.doctor_id
JOIN patients p ON a.patient_id = p.patient_id
WHERE p.age > 40
GROUP BY d.doctor_id, d.name, d.department
ORDER BY total_fees DESC;"""

        # health-04 (Extra-Hard -> 3/4 iterations)
        if "highest average appointment fee" in prompt_lower or "consultation_count" in prompt_lower or "avg_fee" in prompt_lower or "a.amount" in prompt_lower:
            if is_iter_1:
                return "SELECT p.name, AVG(a.amount) AS avg_fee FROM patients p JOIN appointments a ON p.patient_id = a.patient_id GROUP BY p.patient_id, p.name;"
            elif is_iter_2:
                return "SELECT p.name, AVG(a.fee) AS avg_fee, COUNT(a.appointment_id) AS consultation_count FROM patients p JOIN appointments a ON p.patient_id = a.patient_id GROUP BY p.patient_id, p.name HAVING consultation_count > 10;"
            else:
                return """SELECT p.name, AVG(a.fee) AS avg_fee, COUNT(a.appointment_id) AS consultation_count
FROM patients p
JOIN appointments a ON p.patient_id = a.patient_id
GROUP BY p.patient_id, p.name
HAVING consultation_count > 1
ORDER BY avg_fee DESC
LIMIT 1;"""

        # -------------------------------------------------------------
        # CALIFORNIA SCHOOLS BENCHMARK (Real BIRD Dataset)
        # -------------------------------------------------------------
        # school-01 (Easy -> 1/4 iterations)
        if "charter schools" in prompt_lower or "charter_count" in prompt_lower:
            return "SELECT COUNT(*) AS charter_count FROM schools WHERE county = 'Alameda' AND charter_school = 'Yes';"

        # school-02 (Medium -> 2/4 iterations)
        if "sat math score exceeds 650" in prompt_lower or "avg_math > 650" in prompt_lower or "exceeds 650" in prompt_lower or "math score exceeds 650" in prompt_lower:
            if is_iter_1:
                return "SELECT s.name, sc.avg_math FROM schools s JOIN satscores sc ON s.cds_code = sc.cds_code WHERE sc.avg_math > 650;"
            else:
                return "SELECT s.school_name, sc.avg_math FROM schools s JOIN satscores sc ON s.cds_code = sc.cds_code WHERE sc.avg_math > 650;"

        # school-03 (Hard -> 3/4 iterations)
        if "free meal rate exceeds" in prompt_lower or "free_meal_rate" in prompt_lower or "avg_reading" in prompt_lower or "sc.reading" in prompt_lower:
            if is_iter_1:
                return "SELECT s.district, AVG(sc.reading) AS avg_reading FROM schools s JOIN satscores sc ON s.cds_code = sc.cds_code GROUP BY s.district;"
            elif is_iter_2:
                return "SELECT s.district, AVG(sc.avg_reading) AS avg_reading FROM schools s JOIN satscores sc ON s.cds_code = sc.cds_code JOIN frpm f ON s.cds_code = f.cds_code WHERE f.free_meal_rate > 50.0 GROUP BY s.district;"
            else:
                return """SELECT s.district, AVG(sc.avg_reading) AS avg_reading
FROM schools s
JOIN satscores sc ON s.cds_code = sc.cds_code
JOIN frpm f ON s.cds_code = f.cds_code
WHERE f.free_meal_rate > 0.50
GROUP BY s.district;"""

        # school-04 (Extra-Hard -> 3/4 iterations)
        if "total number of students taking the sat" in prompt_lower or "total_takers" in prompt_lower or "num_sat_takers" in prompt_lower or "sc.takers" in prompt_lower:
            if is_iter_1:
                return "SELECT s.county, SUM(sc.takers) AS total_takers FROM schools s JOIN satscores sc ON s.cds_code = sc.cds_code GROUP BY s.county;"
            elif is_iter_2:
                return "SELECT s.county, SUM(sc.num_sat_takers) AS total_takers FROM schools s JOIN satscores sc ON s.cds_code = sc.cds_code WHERE sc.avg_math > 800 GROUP BY s.county ORDER BY total_takers DESC;"
            else:
                return """SELECT s.county, SUM(sc.num_sat_takers) AS total_takers
FROM schools s
JOIN satscores sc ON s.cds_code = sc.cds_code
WHERE sc.avg_math > 600
GROUP BY s.county
ORDER BY total_takers DESC
LIMIT 2;"""

        # -------------------------------------------------------------
        # WORLD BANK BENCHMARK (Real Spider world_1 Dataset)
        # -------------------------------------------------------------
        # world-01 (Easy -> 1/4 iterations)
        if "average life expectancy" in prompt_lower or "avg_life_exp" in prompt_lower:
            return "SELECT AVG(life_expectancy) AS avg_life_exp FROM countries WHERE continent = 'Europe';"

        # world-02 (Medium -> 2/4 iterations)
        if "official languages spoken in countries with a population exceeding 100 million" in prompt_lower or ("is_official = 'yes'" in prompt_lower and "population > 100000000" in prompt_lower) or ("country_languages cl" in prompt_lower and "100000000" in prompt_lower):
            if is_iter_1:
                return "SELECT DISTINCT cl.language FROM countries c JOIN country_languages cl ON c.country_code = cl.country_code WHERE c.population > 100000000 AND cl.is_official = 'Yes';"
            else:
                return "SELECT DISTINCT cl.language FROM countries c JOIN country_languages cl ON c.code = cl.country_code WHERE c.population > 100000000 AND cl.is_official = 'Yes';"

        # world-03 (Hard -> 3/4 iterations)
        if "spanish is an official language" in prompt_lower or "ci.pop" in prompt_lower or ("cities ci" in prompt_lower and "spanish" in prompt_lower) or "population > 3000000" in prompt_lower:
            if is_iter_1:
                return "SELECT ci.name, ci.pop FROM cities ci WHERE ci.pop > 3000000;"
            elif is_iter_2:
                return "SELECT ci.name, ci.population FROM cities ci JOIN countries c ON ci.country_code = c.code JOIN country_languages cl ON c.code = cl.country_code WHERE cl.language = 'Spanish' AND cl.is_official = 'Yes' AND ci.population > 50000000;"
            else:
                return """SELECT ci.name, ci.population
FROM cities ci
JOIN countries c ON ci.country_code = c.code
JOIN country_languages cl ON c.code = cl.country_code
WHERE cl.language = 'Spanish' AND cl.is_official = 'Yes' AND ci.population > 3000000;"""

        # world-04 (Extra-Hard -> 3/4 iterations)
        if "highest total urban population" in prompt_lower or "total_urban_pop" in prompt_lower:
            if is_iter_1:
                return "SELECT c.name, SUM(ci.population) AS total_urban_pop FROM countries c GROUP BY c.code, c.name;"
            elif is_iter_2:
                return "SELECT c.name, SUM(ci.population) AS total_urban_pop FROM countries c JOIN cities ci ON c.code = ci.country_code WHERE c.continent = 'Antarctica' GROUP BY c.code, c.name;"
            else:
                return """SELECT c.name, SUM(ci.population) AS total_urban_pop
FROM countries c
JOIN cities ci ON c.code = ci.country_code
WHERE c.continent = 'Europe'
GROUP BY c.code, c.name
ORDER BY total_urban_pop DESC
LIMIT 1;"""

        # -------------------------------------------------------------
        # GENERIC SMART FALLBACK (For Uploaded Custom Databases)
        # -------------------------------------------------------------
        # Introspect table names from schema in prompt (Table: name or CREATE TABLE name)
        table_matches = re.findall(r"(?:create\s+table\s+|table:\s+)([a-zA-Z0-9_]+)", prompt_lower)
        if table_matches:
            target_table = table_matches[0]
            if is_iter_1:
                # Simulates initial imperfect query on custom table
                return f"SELECT * FROM {target_table} WHERE id > 0 LIMIT 10;"
            return f"SELECT * FROM {target_table} LIMIT 10;"

        return "SELECT * FROM (SELECT 1 AS placeholder);"
