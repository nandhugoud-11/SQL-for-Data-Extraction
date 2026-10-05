"""
sql_python_integration.py
Answers 5 business questions by running SQL from Python (SQLAlchemy + pandas).

Run:
    python database_utils.py            # creates sales_database.db (first time only)
    python sql_python_integration.py    # prints answers and saves CSVs to ./outputs
"""

from database_utils import get_engine, run_query, save_to_csv

DB_PATH = "sales_database.db"

# ---------------------------------------------------------------------------
# The 5 business questions and the SQL that answers each one
# ---------------------------------------------------------------------------
QUESTIONS = {
    "1. Top 5 products by sales revenue": (
        "top_5_products.csv",
        """
        SELECT p.name AS product,
               p.category,
               SUM(oi.quantity)                           AS units_sold,
               ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
        FROM order_items oi
        JOIN products p ON p.product_id = oi.product_id
        JOIN orders   o ON o.order_id   = oi.order_id
        WHERE o.status = 'Completed'
        GROUP BY p.product_id, p.name, p.category
        ORDER BY revenue DESC
        LIMIT 5
        """,
    ),
    "2. Monthly sales trend (with month-over-month growth)": (
        "monthly_sales_trend.csv",
        """
        WITH monthly AS (
            SELECT strftime('%Y-%m', o.order_date)       AS month,
                   SUM(oi.quantity * oi.unit_price)      AS revenue
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.order_id
            WHERE o.status = 'Completed'
            GROUP BY month
        )
        SELECT month,
               ROUND(revenue, 2) AS revenue,
               ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
                     / LAG(revenue) OVER (ORDER BY month), 1) AS growth_pct
        FROM monthly
        ORDER BY month
        """,
    ),
    "3. Customer segmentation by spend": (
        "customer_segments.csv",
        """
        SELECT segment,
               COUNT(*)                   AS customers,
               ROUND(SUM(total_spent), 2) AS revenue,
               ROUND(AVG(total_spent), 2) AS avg_spend_per_customer
        FROM vw_customer_segments
        GROUP BY segment
        ORDER BY revenue DESC
        """,
    ),
    "4. Revenue and customer count by city": (
        "revenue_by_city.csv",
        """
        SELECT city,
               COUNT(DISTINCT customer_id)  AS customers,
               COUNT(DISTINCT order_id)     AS orders,
               ROUND(SUM(line_total), 2)    AS revenue
        FROM vw_sales_detail
        GROUP BY city
        ORDER BY revenue DESC
        """,
    ),
    "5. Order cancellation / return rate by category": (
        "cancel_return_rate.csv",
        """
        SELECT p.category,
               COUNT(DISTINCT o.order_id) AS total_orders,
               COUNT(DISTINCT CASE WHEN o.status IN ('Cancelled', 'Returned')
                                   THEN o.order_id END) AS lost_orders,
               ROUND(100.0 * COUNT(DISTINCT CASE WHEN o.status IN ('Cancelled', 'Returned')
                                                 THEN o.order_id END)
                     / COUNT(DISTINCT o.order_id), 1) AS lost_order_pct
        FROM orders o
        JOIN order_items oi ON oi.order_id   = o.order_id
        JOIN products    p  ON p.product_id  = oi.product_id
        GROUP BY p.category
        ORDER BY lost_order_pct DESC
        """,
    ),
}


def main() -> None:
    engine = get_engine(DB_PATH)

    for title, (csv_name, sql) in QUESTIONS.items():
        df = run_query(engine, sql)
        print(f"\n=== {title} ===")
        print(df.to_string(index=False))
        path = save_to_csv(df, csv_name)
        print(f"(saved to {path})")


if __name__ == "__main__":
    main()
