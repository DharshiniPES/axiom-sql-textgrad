"""
Curated benchmark testbeds, schemas, and queries matching Spider and BIRD standards.
Includes real-world relational databases across Finance, E-Commerce, and Healthcare.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from axiomsql.engine.database import DatabaseSandbox


@dataclass
class BenchmarkQuery:
    id: str
    db_id: str
    difficulty: str  # easy, medium, hard, extra-hard
    question: str
    gold_sql: str
    complexity_factors: List[str]  # e.g. ["multi-join", "group-by", "subquery"]


# Database creation scripts with rich data
FINANCIAL_DDL = """
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    credit_score INTEGER NOT NULL,
    risk_tier TEXT NOT NULL,
    country TEXT NOT NULL
);

CREATE TABLE accounts (
    account_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    account_type TEXT NOT NULL,
    balance REAL NOT NULL,
    open_date TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE transactions (
    txn_id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    txn_type TEXT NOT NULL,
    amount REAL NOT NULL,
    txn_date TEXT NOT NULL,
    merchant_category TEXT NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

CREATE TABLE loans (
    loan_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    loan_amount REAL NOT NULL,
    interest_rate REAL NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Seed Data
INSERT INTO customers VALUES (1, 'Alice Morgan', 780, 'Low', 'USA');
INSERT INTO customers VALUES (2, 'Bob Chen', 620, 'Medium', 'USA');
INSERT INTO customers VALUES (3, 'Clara Rossi', 810, 'Low', 'Italy');
INSERT INTO customers VALUES (4, 'David Patel', 590, 'High', 'UK');
INSERT INTO customers VALUES (5, 'Elena Rostova', 730, 'Low', 'Germany');
INSERT INTO customers VALUES (6, 'Fariq Al-Mansoor', 680, 'Medium', 'UAE');

INSERT INTO accounts VALUES (101, 1, 'Checking', 12500.50, '2021-01-15');
INSERT INTO accounts VALUES (102, 1, 'Savings', 54000.00, '2021-03-20');
INSERT INTO accounts VALUES (103, 2, 'Checking', 2100.20, '2022-06-10');
INSERT INTO accounts VALUES (104, 3, 'Investment', 180000.00, '2020-11-05');
INSERT INTO accounts VALUES (105, 4, 'Checking', 850.00, '2023-02-14');
INSERT INTO accounts VALUES (106, 5, 'Savings', 42000.75, '2021-09-01');
INSERT INTO accounts VALUES (107, 6, 'Checking', 9300.00, '2022-12-18');

INSERT INTO transactions VALUES (1001, 101, 'Debit', 120.50, '2023-10-01', 'Groceries');
INSERT INTO transactions VALUES (1002, 101, 'Debit', 450.00, '2023-10-05', 'Electronics');
INSERT INTO transactions VALUES (1003, 102, 'Credit', 3000.00, '2023-10-02', 'Salary');
INSERT INTO transactions VALUES (1004, 103, 'Debit', 85.00, '2023-10-03', 'Dining');
INSERT INTO transactions VALUES (1005, 104, 'Debit', 12000.00, '2023-10-07', 'Luxury');
INSERT INTO transactions VALUES (1006, 105, 'Debit', 600.00, '2023-10-08', 'Electronics');
INSERT INTO transactions VALUES (1007, 106, 'Credit', 1500.00, '2023-10-09', 'Dividend');
INSERT INTO transactions VALUES (1008, 101, 'Debit', 95.00, '2023-10-12', 'Dining');

INSERT INTO loans VALUES (501, 1, 250000.0, 3.8, 'Active');
INSERT INTO loans VALUES (502, 2, 45000.0, 7.2, 'Defaulted');
INSERT INTO loans VALUES (503, 3, 500000.0, 3.2, 'Active');
INSERT INTO loans VALUES (504, 4, 15000.0, 9.5, 'Active');
INSERT INTO loans VALUES (505, 5, 80000.0, 4.5, 'Closed');
"""

ECOMMERCE_DDL = """
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    loyalty_tier TEXT NOT NULL,
    signup_date TEXT NOT NULL
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price REAL NOT NULL,
    cost_price REAL NOT NULL,
    stock_quantity INTEGER NOT NULL
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    status TEXT NOT NULL,
    total_amount REAL NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE reviews (
    review_id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Seed Data
INSERT INTO customers VALUES (1, 'Sarah Connor', 'sarah@skynet.com', 'Platinum', '2021-04-12');
INSERT INTO customers VALUES (2, 'John Wick', 'john@continental.org', 'Gold', '2022-01-20');
INSERT INTO customers VALUES (3, 'Bruce Wayne', 'bruce@wayne.com', 'Diamond', '2020-08-15');
INSERT INTO customers VALUES (4, 'Peter Parker', 'peter@dailybugle.com', 'Standard', '2023-05-10');
INSERT INTO customers VALUES (5, 'Diana Prince', 'diana@themyscira.gov', 'Gold', '2021-11-30');

INSERT INTO products VALUES (10, 'Quantum Laptop', 'Electronics', 1499.99, 950.00, 25);
INSERT INTO products VALUES (11, 'Ergonomic Desk Chair', 'Furniture', 349.50, 180.00, 60);
INSERT INTO products VALUES (12, 'Wireless Noise-Canceling Headphones', 'Audio', 249.99, 110.00, 120);
INSERT INTO products VALUES (13, 'Mechanical Gaming Keyboard', 'Accessories', 129.00, 55.00, 85);
INSERT INTO products VALUES (14, 'Ultra-Wide 4K Monitor', 'Electronics', 699.00, 420.00, 30);

INSERT INTO orders VALUES (101, 1, '2023-09-01', 'Completed', 1749.98);
INSERT INTO orders VALUES (102, 2, '2023-09-05', 'Completed', 249.99);
INSERT INTO orders VALUES (103, 3, '2023-09-10', 'Completed', 2198.99);
INSERT INTO orders VALUES (104, 4, '2023-09-12', 'Cancelled', 129.00);
INSERT INTO orders VALUES (105, 5, '2023-09-15', 'Completed', 1048.50);
INSERT INTO orders VALUES (106, 1, '2023-09-20', 'Processing', 349.50);

INSERT INTO order_items VALUES (1, 101, 10, 1, 1499.99);
INSERT INTO order_items VALUES (2, 101, 12, 1, 249.99);
INSERT INTO order_items VALUES (3, 102, 12, 1, 249.99);
INSERT INTO order_items VALUES (4, 103, 10, 1, 1499.99);
INSERT INTO order_items VALUES (5, 103, 14, 1, 699.00);
INSERT INTO order_items VALUES (6, 104, 13, 1, 129.00);
INSERT INTO order_items VALUES (7, 105, 11, 3, 349.50);
INSERT INTO order_items VALUES (8, 106, 11, 1, 349.50);

INSERT INTO reviews VALUES (1, 10, 1, 5, 'Superb computational power.');
INSERT INTO reviews VALUES (2, 12, 2, 4, 'Blocks out high decibel combat noise.');
INSERT INTO reviews VALUES (3, 14, 3, 5, 'Perfect resolution for night surveillance.');
INSERT INTO reviews VALUES (4, 11, 5, 5, 'Comfortable for extended strategic planning.');
"""

HEALTHCARE_DDL = """
CREATE TABLE patients (
    patient_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    blood_group TEXT NOT NULL,
    admission_date TEXT NOT NULL
);

CREATE TABLE doctors (
    doctor_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    specialization TEXT NOT NULL,
    experience_years INTEGER NOT NULL
);

CREATE TABLE appointments (
    appointment_id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    appointment_date TEXT NOT NULL,
    diagnosis TEXT NOT NULL,
    fee REAL NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
);

CREATE TABLE prescriptions (
    prescription_id INTEGER PRIMARY KEY,
    appointment_id INTEGER NOT NULL,
    medication_name TEXT NOT NULL,
    dosage TEXT NOT NULL,
    days INTEGER NOT NULL,
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id)
);

-- Seed Data
INSERT INTO patients VALUES (1, 'Arthur Dent', 42, 'M', 'O+', '2023-08-01');
INSERT INTO patients VALUES (2, 'Ford Prefect', 38, 'M', 'AB-', '2023-08-05');
INSERT INTO patients VALUES (3, 'Trillian Astra', 29, 'F', 'A+', '2023-08-10');
INSERT INTO patients VALUES (4, 'Zaphod Beeblebrox', 50, 'M', 'B+', '2023-08-12');
INSERT INTO patients VALUES (5, 'Marvin Paranoid', 75, 'M', 'O-', '2023-08-15');

INSERT INTO doctors VALUES (1, 'Dr. Gregory House', 'Diagnostics', 'Infectious Disease', 22);
INSERT INTO doctors VALUES (2, 'Dr. Leonard McCoy', 'Surgery', 'General Trauma', 18);
INSERT INTO doctors VALUES (3, 'Dr. Beverly Crusher', 'Cardiology', 'Internal Medicine', 15);
INSERT INTO doctors VALUES (4, 'Dr. Meredith Grey', 'Surgery', 'General Surgery', 12);

INSERT INTO appointments VALUES (101, 1, 1, '2023-08-02', 'Lupus Suspect', 350.00);
INSERT INTO appointments VALUES (102, 2, 2, '2023-08-06', 'Concussion', 220.00);
INSERT INTO appointments VALUES (103, 3, 3, '2023-08-11', 'Arrhythmia', 300.00);
INSERT INTO appointments VALUES (104, 4, 1, '2023-08-13', 'Multiple Head Trauma', 450.00);
INSERT INTO appointments VALUES (105, 5, 4, '2023-08-16', 'Chronic Fatigue', 180.00);
INSERT INTO appointments VALUES (106, 1, 3, '2023-08-20', 'Cardiovascular Checkup', 280.00);

INSERT INTO prescriptions VALUES (1, 101, 'Prednisone', '20mg daily', 14);
INSERT INTO prescriptions VALUES (2, 102, 'Ibuprofen', '400mg twice daily', 7);
INSERT INTO prescriptions VALUES (3, 103, 'Atenolol', '50mg daily', 30);
INSERT INTO prescriptions VALUES (4, 104, 'Sertraline', '100mg daily', 30);
INSERT INTO prescriptions VALUES (5, 106, 'Atorvastatin', '10mg daily', 60);
"""


BENCHMARK_SUITE: List[BenchmarkQuery] = [
    # FINANCIAL BENCHMARK
    BenchmarkQuery(
        id="fin-01",
        db_id="financial",
        difficulty="easy",
        question="What is the average credit score of customers by risk tier?",
        gold_sql="SELECT risk_tier, AVG(credit_score) AS avg_credit_score FROM customers GROUP BY risk_tier;",
        complexity_factors=["group-by", "aggregation"],
    ),
    BenchmarkQuery(
        id="fin-02",
        db_id="financial",
        difficulty="medium",
        question="List the names of customers who have an active loan with an interest rate below 4.0%.",
        gold_sql="SELECT c.full_name FROM customers c JOIN loans l ON c.customer_id = l.customer_id WHERE l.status = 'Active' AND l.interest_rate < 4.0;",
        complexity_factors=["join", "filtering"],
    ),
    BenchmarkQuery(
        id="fin-03",
        db_id="financial",
        difficulty="hard",
        question="Find the total transaction debit volume for each customer whose total account balance across all accounts exceeds 20000.",
        gold_sql="""SELECT c.full_name, SUM(t.amount) AS total_debit
FROM customers c
JOIN accounts a ON c.customer_id = a.customer_id
JOIN transactions t ON a.account_id = t.account_id
WHERE t.txn_type = 'Debit'
GROUP BY c.customer_id, c.full_name
HAVING SUM(a.balance) > 20000;""",
        complexity_factors=["multi-join", "group-by", "having", "aggregation"],
    ),
    BenchmarkQuery(
        id="fin-04",
        db_id="financial",
        difficulty="extra-hard",
        question="Which customer has the highest ratio of total active loan amount to their total combined account balances?",
        gold_sql="""SELECT c.full_name, (SUM(l.loan_amount) / SUM(a.balance)) AS leverage_ratio
FROM customers c
JOIN loans l ON c.customer_id = l.customer_id
JOIN accounts a ON c.customer_id = a.customer_id
WHERE l.status = 'Active'
GROUP BY c.customer_id, c.full_name
ORDER BY leverage_ratio DESC
LIMIT 1;""",
        complexity_factors=["multi-join", "arithmetic-ratio", "order-by", "limit"],
    ),

    # E-COMMERCE BENCHMARK
    BenchmarkQuery(
        id="ecom-01",
        db_id="ecommerce",
        difficulty="easy",
        question="Find all products in the Electronics category priced above 500 dollars.",
        gold_sql="SELECT name, unit_price FROM products WHERE category = 'Electronics' AND unit_price > 500;",
        complexity_factors=["filtering"],
    ),
    BenchmarkQuery(
        id="ecom-02",
        db_id="ecommerce",
        difficulty="medium",
        question="Find the total revenue generated from each product category for completed orders.",
        gold_sql="""SELECT p.category, SUM(oi.quantity * oi.unit_price) AS total_revenue
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status = 'Completed'
GROUP BY p.category;""",
        complexity_factors=["multi-join", "aggregation", "group-by"],
    ),
    BenchmarkQuery(
        id="ecom-03",
        db_id="ecommerce",
        difficulty="hard",
        question="List the names of customers who have given a 5-star review but have never cancelled any order.",
        gold_sql="""SELECT DISTINCT c.name
FROM customers c
JOIN reviews r ON c.customer_id = r.customer_id
WHERE r.rating = 5
  AND c.customer_id NOT IN (
      SELECT customer_id FROM orders WHERE status = 'Cancelled'
  );""",
        complexity_factors=["subquery", "anti-join", "distinct"],
    ),
    BenchmarkQuery(
        id="ecom-04",
        db_id="ecommerce",
        difficulty="extra-hard",
        question="Identify products whose profit margin ((unit_price - cost_price) / unit_price) is above 40% and that have been ordered more than once.",
        gold_sql="""SELECT p.name, ((p.unit_price - p.cost_price) / p.unit_price) AS margin, SUM(oi.quantity) AS total_units_sold
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.name, p.unit_price, p.cost_price
HAVING margin > 0.40 AND SUM(oi.quantity) > 1;""",
        complexity_factors=["computed-margin", "aggregation", "having", "join"],
    ),

    # HEALTHCARE BENCHMARK
    BenchmarkQuery(
        id="health-01",
        db_id="healthcare",
        difficulty="easy",
        question="Count how many doctors belong to the Surgery department.",
        gold_sql="SELECT COUNT(*) AS doctor_count FROM doctors WHERE department = 'Surgery';",
        complexity_factors=["aggregation", "filtering"],
    ),
    BenchmarkQuery(
        id="health-02",
        db_id="healthcare",
        difficulty="medium",
        question="Find the names of patients who were diagnosed with Lupus Suspect along with their prescribed medication.",
        gold_sql="""SELECT p.name, pr.medication_name, pr.dosage
FROM patients p
JOIN appointments a ON p.patient_id = a.patient_id
JOIN prescriptions pr ON a.appointment_id = pr.appointment_id
WHERE a.diagnosis = 'Lupus Suspect';""",
        complexity_factors=["multi-join", "filtering"],
    ),
    BenchmarkQuery(
        id="health-03",
        db_id="healthcare",
        difficulty="hard",
        question="Find the doctors who have earned the highest total appointment fees from patients aged over 40.",
        gold_sql="""SELECT d.name, d.department, SUM(a.fee) AS total_fees
FROM doctors d
JOIN appointments a ON d.doctor_id = a.doctor_id
JOIN patients p ON a.patient_id = p.patient_id
WHERE p.age > 40
GROUP BY d.doctor_id, d.name, d.department
ORDER BY total_fees DESC;""",
        complexity_factors=["multi-join", "group-by", "order-by", "aggregation"],
    ),
]


def create_benchmark_sandbox(db_id: str) -> DatabaseSandbox:
    """Factory creating in-memory populated database sandbox for requested domain."""
    sandbox = DatabaseSandbox(":memory:")
    cursor = sandbox._conn.cursor()

    if db_id == "financial":
        cursor.executescript(FINANCIAL_DDL)
    elif db_id == "ecommerce":
        cursor.executescript(ECOMMERCE_DDL)
    elif db_id == "healthcare":
        cursor.executescript(HEALTHCARE_DDL)
    else:
        raise ValueError(f"Unknown database identifier: {db_id}")

    sandbox._conn.commit()
    return sandbox
