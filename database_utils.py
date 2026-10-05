"""
database_utils.py
Reusable database utilities for SQL data extraction with Python.

Usage:
    from database_utils import get_engine, run_query, run_sql_file

    engine = get_engine("sales_database.db")
    df = run_query(engine, "SELECT * FROM customers LIMIT 5")
"""

import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect, text

DEFAULT_DB = "sales_database.db"


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------
def get_engine(db_path: str = DEFAULT_DB):
    """Create a SQLAlchemy engine for a SQLite database file."""
    return create_engine(f"sqlite:///{db_path}")


def run_query(engine, query: str, params: dict | None = None) -> pd.DataFrame:
    """Run a SELECT query and return the result as a DataFrame."""
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn, params=params)


def run_sql_file(engine, sql_path: str) -> None:
    """Execute every statement in a .sql file (useful for schema/setup scripts)."""
    script = Path(sql_path).read_text(encoding="utf-8")
    raw = engine.raw_connection()
    try:
        raw.executescript(script)
        raw.commit()
    finally:
        raw.close()


def list_tables(engine) -> list[str]:
    """Return all table names in the database."""
    return inspect(engine).get_table_names()


def describe_table(engine, table: str) -> pd.DataFrame:
    """Return column names and types for a table."""
    cols = inspect(engine).get_columns(table)
    return pd.DataFrame([{"column": c["name"], "type": str(c["type"])} for c in cols])


def save_to_csv(df: pd.DataFrame, filename: str, folder: str = "outputs") -> Path:
    """Save a DataFrame to CSV inside `folder` and return the path."""
    Path(folder).mkdir(exist_ok=True)
    path = Path(folder) / filename
    df.to_csv(path, index=False)
    return path


# ---------------------------------------------------------------------------
# Sample database builder
# ---------------------------------------------------------------------------
SCHEMA = """
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    city        TEXT NOT NULL,
    signup_date TEXT NOT NULL
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    category   TEXT NOT NULL,
    price      REAL NOT NULL
);

CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date  TEXT NOT NULL,
    status      TEXT NOT NULL
);

CREATE TABLE order_items (
    item_id    INTEGER PRIMARY KEY,
    order_id   INTEGER NOT NULL REFERENCES orders(order_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity   INTEGER NOT NULL,
    unit_price REAL NOT NULL
);
"""

VIEWS = """
DROP VIEW IF EXISTS vw_sales_detail;
CREATE VIEW vw_sales_detail AS
SELECT o.order_id, o.order_date, strftime('%Y-%m', o.order_date) AS order_month,
       c.customer_id, c.name AS customer_name, c.city,
       p.product_id, p.name AS product_name, p.category,
       oi.quantity, oi.unit_price, oi.quantity * oi.unit_price AS line_total
FROM orders o
JOIN customers   c  ON c.customer_id = o.customer_id
JOIN order_items oi ON oi.order_id   = o.order_id
JOIN products    p  ON p.product_id  = oi.product_id
WHERE o.status = 'Completed';

DROP VIEW IF EXISTS vw_monthly_sales;
CREATE VIEW vw_monthly_sales AS
SELECT order_month, COUNT(DISTINCT order_id) AS orders, SUM(quantity) AS units_sold,
       ROUND(SUM(line_total), 2) AS revenue
FROM vw_sales_detail
GROUP BY order_month;

DROP VIEW IF EXISTS vw_customer_segments;
CREATE VIEW vw_customer_segments AS
SELECT customer_id, customer_name, city, COUNT(DISTINCT order_id) AS orders,
       ROUND(SUM(line_total), 2) AS total_spent,
       CASE WHEN SUM(line_total) >= 80000 THEN 'Gold'
            WHEN SUM(line_total) >= 45000 THEN 'Silver'
            ELSE 'Bronze' END AS segment
FROM vw_sales_detail
GROUP BY customer_id, customer_name, city;
"""

_FIRST = ["Aarav", "Diya", "Vivaan", "Ananya", "Aditya", "Isha", "Rohan", "Meera",
          "Kabir", "Saanvi", "Arjun", "Priya", "Karan", "Neha", "Rahul", "Sneha",
          "Vikram", "Pooja", "Amit", "Kavya"]
_LAST = ["Sharma", "Reddy", "Patel", "Iyer", "Gupta", "Nair", "Singh", "Rao",
         "Mehta", "Das"]
_CITIES = ["Hyderabad", "Mumbai", "Delhi", "Bengaluru", "Chennai", "Pune", "Kolkata"]

_PRODUCTS = [
    ("Wireless Mouse", "Electronics", 799), ("Mechanical Keyboard", "Electronics", 3499),
    ("Bluetooth Speaker", "Electronics", 2199), ("USB-C Hub", "Electronics", 1499),
    ("Noise-Cancelling Headphones", "Electronics", 5999),
    ("Running Shoes", "Fashion", 2999), ("Denim Jacket", "Fashion", 2499),
    ("Cotton T-Shirt", "Fashion", 599), ("Backpack", "Fashion", 1299),
    ("Coffee Maker", "Home", 3299), ("Desk Lamp", "Home", 899),
    ("Air Fryer", "Home", 4999), ("Yoga Mat", "Sports", 699),
    ("Dumbbell Set", "Sports", 2799), ("Water Bottle", "Sports", 399),
]

_STATUSES = ["Completed"] * 8 + ["Cancelled", "Returned"]


def create_sample_database(db_path: str = DEFAULT_DB, n_customers: int = 60,
                           n_orders: int = 400, seed: int = 42) -> str:
    """Build a sample sales database (SQLite) with realistic random data."""
    rng = random.Random(seed)
    Path(db_path).unlink(missing_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)

    start = date(2025, 1, 1)
    customers = []
    for cid in range(1, n_customers + 1):
        name = f"{rng.choice(_FIRST)} {rng.choice(_LAST)}"
        signup = start + timedelta(days=rng.randint(0, 200))
        customers.append((cid, name, rng.choice(_CITIES), signup.isoformat()))
    conn.executemany("INSERT INTO customers VALUES (?,?,?,?)", customers)

    products = [(i, n, c, p) for i, (n, c, p) in enumerate(_PRODUCTS, start=1)]
    conn.executemany("INSERT INTO products VALUES (?,?,?,?)", products)
    price_of = {p[0]: p[3] for p in products}

    item_id = 1
    for oid in range(1, n_orders + 1):
        cid = rng.randint(1, n_customers)
        signup = date.fromisoformat(customers[cid - 1][3])
        order_date = signup + timedelta(days=rng.randint(1, 400))
        order_date = min(order_date, date(2026, 8, 31))
        conn.execute("INSERT INTO orders VALUES (?,?,?,?)",
                     (oid, cid, order_date.isoformat(), rng.choice(_STATUSES)))
        for pid in rng.sample(range(1, len(products) + 1), rng.randint(1, 3)):
            conn.execute("INSERT INTO order_items VALUES (?,?,?,?,?)",
                         (item_id, oid, pid, rng.randint(1, 4), price_of[pid]))
            item_id += 1

    conn.executescript(VIEWS)  # reusable views used by the analysis queries
    conn.commit()
    conn.close()
    return db_path


if __name__ == "__main__":
    path = create_sample_database()
    print(f"Sample database created: {path}")
