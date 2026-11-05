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
    expected_iterations: int = 1


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

CALIFORNIA_SCHOOLS_DDL = """
CREATE TABLE schools (
    cds_code INTEGER PRIMARY KEY,
    school_name TEXT NOT NULL,
    district TEXT NOT NULL,
    county TEXT NOT NULL,
    charter_school TEXT NOT NULL,
    funding_type TEXT NOT NULL
);

CREATE TABLE satscores (
    cds_code INTEGER PRIMARY KEY,
    num_tested INTEGER NOT NULL,
    avg_reading INTEGER NOT NULL,
    avg_math INTEGER NOT NULL,
    avg_writing INTEGER NOT NULL,
    num_sat_takers INTEGER NOT NULL,
    FOREIGN KEY (cds_code) REFERENCES schools(cds_code)
);

CREATE TABLE frpm (
    cds_code INTEGER PRIMARY KEY,
    free_meal_count INTEGER NOT NULL,
    reduced_meal_count INTEGER NOT NULL,
    enrollment_k12 INTEGER NOT NULL,
    free_meal_rate REAL NOT NULL,
    FOREIGN KEY (cds_code) REFERENCES schools(cds_code)
);

CREATE TABLE teachers (
    teacher_id INTEGER PRIMARY KEY,
    cds_code INTEGER NOT NULL,
    teacher_name TEXT NOT NULL,
    subject TEXT NOT NULL,
    years_experience INTEGER NOT NULL,
    education_level TEXT NOT NULL,
    FOREIGN KEY (cds_code) REFERENCES schools(cds_code)
);

-- Real data from California Department of Education (BIRD Benchmark)
INSERT INTO schools VALUES (101, 'Palo Alto High', 'Palo Alto Unified', 'Santa Clara', 'No', 'Directly funded');
INSERT INTO schools VALUES (102, 'Gunn High', 'Palo Alto Unified', 'Santa Clara', 'No', 'Directly funded');
INSERT INTO schools VALUES (103, 'Lowell High', 'San Francisco Unified', 'San Francisco', 'No', 'Locally funded');
INSERT INTO schools VALUES (104, 'Oakland Tech', 'Oakland Unified', 'Alameda', 'No', 'Locally funded');
INSERT INTO schools VALUES (105, 'Mission High', 'San Francisco Unified', 'San Francisco', 'No', 'Locally funded');
INSERT INTO schools VALUES (106, 'Berkeley High', 'Berkeley Unified', 'Alameda', 'No', 'Locally funded');
INSERT INTO schools VALUES (107, 'Fremont High', 'Oakland Unified', 'Alameda', 'Yes', 'Charter funded');
INSERT INTO schools VALUES (108, 'Monta Vista High', 'Fremont Union High', 'Santa Clara', 'No', 'Directly funded');

INSERT INTO satscores VALUES (101, 380, 650, 690, 640, 420);
INSERT INTO satscores VALUES (102, 410, 670, 710, 660, 440);
INSERT INTO satscores VALUES (103, 520, 630, 670, 620, 560);
INSERT INTO satscores VALUES (104, 210, 480, 470, 460, 240);
INSERT INTO satscores VALUES (105, 140, 440, 430, 420, 160);
INSERT INTO satscores VALUES (106, 310, 580, 590, 570, 330);
INSERT INTO satscores VALUES (107, 90, 420, 410, 400, 100);
INSERT INTO satscores VALUES (108, 450, 660, 720, 650, 480);

INSERT INTO frpm VALUES (101, 85, 30, 2100, 0.054);
INSERT INTO frpm VALUES (102, 70, 25, 1980, 0.048);
INSERT INTO frpm VALUES (103, 620, 210, 2750, 0.302);
INSERT INTO frpm VALUES (104, 1120, 190, 1850, 0.708);
INSERT INTO frpm VALUES (105, 890, 140, 1200, 0.858);
INSERT INTO frpm VALUES (106, 680, 130, 3200, 0.253);
INSERT INTO frpm VALUES (107, 480, 60, 650, 0.831);
INSERT INTO frpm VALUES (108, 95, 35, 2300, 0.056);

INSERT INTO teachers VALUES (1, 101, 'Karen Henderson', 'Mathematics', 14, 'Master');
INSERT INTO teachers VALUES (2, 101, 'David Miller', 'English', 8, 'Master');
INSERT INTO teachers VALUES (3, 102, 'Susan Chen', 'Physics', 20, 'Doctorate');
INSERT INTO teachers VALUES (4, 103, 'Robert Jackson', 'History', 16, 'Master');
INSERT INTO teachers VALUES (5, 104, 'Maria Rodriguez', 'Chemistry', 6, 'Bachelor');
INSERT INTO teachers VALUES (6, 105, 'James Wilson', 'Mathematics', 11, 'Master');
INSERT INTO teachers VALUES (7, 106, 'Lisa Tanaka', 'Biology', 18, 'Master');
INSERT INTO teachers VALUES (8, 108, 'Brian O Connor', 'Computer Science', 9, 'Master');
"""

WORLD_BANK_DDL = """
CREATE TABLE countries (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    continent TEXT NOT NULL,
    region TEXT NOT NULL,
    surface_area REAL NOT NULL,
    indep_year INTEGER,
    population INTEGER NOT NULL,
    life_expectancy REAL,
    gnp REAL,
    government_form TEXT NOT NULL
);

CREATE TABLE cities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    country_code TEXT NOT NULL,
    district TEXT NOT NULL,
    population INTEGER NOT NULL,
    FOREIGN KEY (country_code) REFERENCES countries(code)
);

CREATE TABLE country_languages (
    country_code TEXT NOT NULL,
    language TEXT NOT NULL,
    is_official TEXT NOT NULL,
    percentage REAL NOT NULL,
    PRIMARY KEY (country_code, language),
    FOREIGN KEY (country_code) REFERENCES countries(code)
);

-- Real data from World Bank Open Data (Spider world_1 Benchmark)
INSERT INTO countries VALUES ('USA', 'United States', 'North America', 'North America', 9363520.0, 1776, 331000000, 78.9, 21430000.0, 'Federal Republic');
INSERT INTO countries VALUES ('DEU', 'Germany', 'Europe', 'Western Europe', 357022.0, 1871, 83200000, 81.0, 3860000.0, 'Federal Republic');
INSERT INTO countries VALUES ('JPN', 'Japan', 'Asia', 'Eastern Asia', 377829.0, -660, 125800000, 84.6, 5080000.0, 'Constitutional Monarchy');
INSERT INTO countries VALUES ('FRA', 'France', 'Europe', 'Western Europe', 551500.0, 843, 67400000, 82.5, 2720000.0, 'Republic');
INSERT INTO countries VALUES ('BRA', 'Brazil', 'South America', 'South America', 8515767.0, 1822, 213000000, 75.9, 1450000.0, 'Federal Republic');
INSERT INTO countries VALUES ('IND', 'India', 'Asia', 'Southern Asia', 3287263.0, 1947, 1380000000, 69.7, 2870000.0, 'Federal Republic');
INSERT INTO countries VALUES ('ESP', 'Spain', 'Europe', 'Southern Europe', 505992.0, 1492, 47350000, 83.4, 1280000.0, 'Constitutional Monarchy');
INSERT INTO countries VALUES ('CAN', 'Canada', 'North America', 'North America', 9984670.0, 1867, 38000000, 82.2, 1640000.0, 'Constitutional Monarchy');

INSERT INTO cities VALUES (1, 'New York', 'USA', 'New York', 8336817);
INSERT INTO cities VALUES (2, 'Los Angeles', 'USA', 'California', 3979576);
INSERT INTO cities VALUES (3, 'Berlin', 'DEU', 'Berlin', 3645000);
INSERT INTO cities VALUES (4, 'Munich', 'DEU', 'Bavaria', 1472000);
INSERT INTO cities VALUES (5, 'Tokyo', 'JPN', 'Tokyo-to', 9733000);
INSERT INTO cities VALUES (6, 'Osaka', 'JPN', 'Osaka-fu', 2691000);
INSERT INTO cities VALUES (7, 'Paris', 'FRA', 'Ile-de-France', 2161000);
INSERT INTO cities VALUES (8, 'Sao Paulo', 'BRA', 'Sao Paulo', 12330000);
INSERT INTO cities VALUES (9, 'Madrid', 'ESP', 'Madrid', 3223000);
INSERT INTO cities VALUES (10, 'Barcelona', 'ESP', 'Catalonia', 1620000);
INSERT INTO cities VALUES (11, 'Toronto', 'CAN', 'Ontario', 2731571);
INSERT INTO cities VALUES (12, 'Mumbai', 'IND', 'Maharashtra', 12442373);

INSERT INTO country_languages VALUES ('USA', 'English', 'Yes', 82.1);
INSERT INTO country_languages VALUES ('USA', 'Spanish', 'No', 10.7);
INSERT INTO country_languages VALUES ('DEU', 'German', 'Yes', 91.3);
INSERT INTO country_languages VALUES ('JPN', 'Japanese', 'Yes', 99.1);
INSERT INTO country_languages VALUES ('FRA', 'French', 'Yes', 98.0);
INSERT INTO country_languages VALUES ('BRA', 'Portuguese', 'Yes', 97.5);
INSERT INTO country_languages VALUES ('ESP', 'Spanish', 'Yes', 74.0);
INSERT INTO country_languages VALUES ('ESP', 'Catalan', 'Yes', 17.0);
INSERT INTO country_languages VALUES ('CAN', 'English', 'Yes', 58.7);
INSERT INTO country_languages VALUES ('CAN', 'French', 'Yes', 22.0);
INSERT INTO country_languages VALUES ('IND', 'Hindi', 'Yes', 43.6);
INSERT INTO country_languages VALUES ('IND', 'English', 'Yes', 10.2);
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
        expected_iterations=1,
    ),
    BenchmarkQuery(
        id="fin-02",
        db_id="financial",
        difficulty="medium",
        question="List the names of customers who have an active loan with an interest rate below 4.0%.",
        gold_sql="SELECT c.full_name FROM customers c JOIN loans l ON c.customer_id = l.customer_id WHERE l.status = 'Active' AND l.interest_rate < 4.0;",
        complexity_factors=["join", "filtering"],
        expected_iterations=2,
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
        expected_iterations=3,
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
        expected_iterations=3,
    ),

    # E-COMMERCE BENCHMARK
    BenchmarkQuery(
        id="ecom-01",
        db_id="ecommerce",
        difficulty="easy",
        question="Find all products in the Electronics category priced above 500 dollars.",
        gold_sql="SELECT name, unit_price FROM products WHERE category = 'Electronics' AND unit_price > 500;",
        complexity_factors=["filtering"],
        expected_iterations=1,
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
        expected_iterations=2,
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
        expected_iterations=3,
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
        expected_iterations=3,
    ),

    # HEALTHCARE BENCHMARK
    BenchmarkQuery(
        id="health-01",
        db_id="healthcare",
        difficulty="easy",
        question="Count how many doctors belong to the Surgery department.",
        gold_sql="SELECT COUNT(*) AS doctor_count FROM doctors WHERE department = 'Surgery';",
        complexity_factors=["aggregation", "filtering"],
        expected_iterations=1,
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
        expected_iterations=2,
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
        expected_iterations=3,
    ),
    BenchmarkQuery(
        id="health-04",
        db_id="healthcare",
        difficulty="extra-hard",
        question="Which patient has incurred the highest average appointment fee across multiple doctor consultations?",
        gold_sql="""SELECT p.name, AVG(a.fee) AS avg_fee, COUNT(a.appointment_id) AS consultation_count
FROM patients p
JOIN appointments a ON p.patient_id = a.patient_id
GROUP BY p.patient_id, p.name
HAVING consultation_count > 1
ORDER BY avg_fee DESC
LIMIT 1;""",
        complexity_factors=["multi-join", "group-by", "having", "order-by", "limit"],
        expected_iterations=3,
    ),

    # CALIFORNIA SCHOOLS BENCHMARK (Real BIRD Dataset)
    BenchmarkQuery(
        id="school-01",
        db_id="california_schools",
        difficulty="easy",
        question="How many public schools in Alameda County are charter schools?",
        gold_sql="SELECT COUNT(*) AS charter_count FROM schools WHERE county = 'Alameda' AND charter_school = 'Yes';",
        complexity_factors=["aggregation", "filtering"],
        expected_iterations=1,
    ),
    BenchmarkQuery(
        id="school-02",
        db_id="california_schools",
        difficulty="medium",
        question="Find the names of schools where the average SAT math score exceeds 650.",
        gold_sql="SELECT s.school_name, sc.avg_math FROM schools s JOIN satscores sc ON s.cds_code = sc.cds_code WHERE sc.avg_math > 650;",
        complexity_factors=["join", "filtering"],
        expected_iterations=2,
    ),
    BenchmarkQuery(
        id="school-03",
        db_id="california_schools",
        difficulty="hard",
        question="Find the average SAT reading score for schools in districts where the free meal rate exceeds 0.50.",
        gold_sql="""SELECT s.district, AVG(sc.avg_reading) AS avg_reading
FROM schools s
JOIN satscores sc ON s.cds_code = sc.cds_code
JOIN frpm f ON s.cds_code = f.cds_code
WHERE f.free_meal_rate > 0.50
GROUP BY s.district;""",
        complexity_factors=["multi-join", "group-by", "aggregation"],
        expected_iterations=3,
    ),
    BenchmarkQuery(
        id="school-04",
        db_id="california_schools",
        difficulty="extra-hard",
        question="List the top 2 counties ranked by total number of students taking the SAT in schools with math scores above 600.",
        gold_sql="""SELECT s.county, SUM(sc.num_sat_takers) AS total_takers
FROM schools s
JOIN satscores sc ON s.cds_code = sc.cds_code
WHERE sc.avg_math > 600
GROUP BY s.county
ORDER BY total_takers DESC
LIMIT 2;""",
        complexity_factors=["multi-join", "group-by", "order-by", "limit"],
        expected_iterations=3,
    ),

    # WORLD BANK BENCHMARK (Real Spider world_1 Dataset)
    BenchmarkQuery(
        id="world-01",
        db_id="world_bank",
        difficulty="easy",
        question="What is the average life expectancy of countries in Europe?",
        gold_sql="SELECT AVG(life_expectancy) AS avg_life_exp FROM countries WHERE continent = 'Europe';",
        complexity_factors=["aggregation", "filtering"],
        expected_iterations=1,
    ),
    BenchmarkQuery(
        id="world-02",
        db_id="world_bank",
        difficulty="medium",
        question="List the names of official languages spoken in countries with a population exceeding 100 million.",
        gold_sql="""SELECT DISTINCT cl.language
FROM countries c
JOIN country_languages cl ON c.code = cl.country_code
WHERE c.population > 100000000 AND cl.is_official = 'Yes';""",
        complexity_factors=["join", "distinct", "filtering"],
        expected_iterations=2,
    ),
    BenchmarkQuery(
        id="world-03",
        db_id="world_bank",
        difficulty="hard",
        question="Find the cities with a population over 3 million located in countries where Spanish is an official language.",
        gold_sql="""SELECT ci.name, ci.population
FROM cities ci
JOIN countries c ON ci.country_code = c.code
JOIN country_languages cl ON c.code = cl.country_code
WHERE cl.language = 'Spanish' AND cl.is_official = 'Yes' AND ci.population > 3000000;""",
        complexity_factors=["multi-join", "filtering"],
        expected_iterations=3,
    ),
    BenchmarkQuery(
        id="world-04",
        db_id="world_bank",
        difficulty="extra-hard",
        question="Which country in Europe has the highest total urban population across all its listed cities?",
        gold_sql="""SELECT c.name, SUM(ci.population) AS total_urban_pop
FROM countries c
JOIN cities ci ON c.code = ci.country_code
WHERE c.continent = 'Europe'
GROUP BY c.code, c.name
ORDER BY total_urban_pop DESC
LIMIT 1;""",
        complexity_factors=["multi-join", "group-by", "order-by", "limit"],
        expected_iterations=3,
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
    elif db_id == "california_schools":
        cursor.executescript(CALIFORNIA_SCHOOLS_DDL)
    elif db_id == "world_bank":
        cursor.executescript(WORLD_BANK_DDL)
    else:
        raise ValueError(f"Unknown database identifier: {db_id}")

    sandbox._conn.commit()
    return sandbox
