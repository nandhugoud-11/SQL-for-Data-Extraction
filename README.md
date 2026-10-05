# Task 2: SQL for Data Extraction

Master SQL for data extraction and analysis, then integrate it with Python (SQLAlchemy + pandas) to answer business questions automatically.

## Project Structure

| File | Description |
|------|-------------|
| `sales_analysis.sql` | SQL fundamentals (SELECT, WHERE, GROUP BY, HAVING, JOINs) and advanced SQL (subqueries, CTEs, window functions, views) |
| `sales_database.db` | Sample SQLite database (60 customers, 15 products, 400 orders) |
| `sql_data_extraction.ipynb` | Jupyter notebook: Python + SQLAlchemy, 10 business questions with `pandas.read_sql()` |
| `sql_python_integration.py` | Script answering 5 business questions with SQL and saving results as CSV |
| `database_utils.py` | Reusable database utility (engine, query runner, table inspection, sample DB builder) |
| `requirements.txt` | Required Python libraries |

## Database Schema

```
customers   (customer_id, name, city, signup_date)
products    (product_id, name, category, price)
orders      (order_id, customer_id, order_date, status)
order_items (item_id, order_id, product_id, quantity, unit_price)
```

Views created by the SQL file: `vw_sales_detail`, `vw_monthly_sales`, `vw_customer_segments`.

## Setup

1. Clone the repo and open the folder:
   ```bash
   git clone <your-repo-url>
   cd <your-repo-folder>
   ```
2. (Optional) Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. (Optional) Rebuild the sample database from scratch:
   ```bash
   python database_utils.py
   ```

## How to Run

**SQL queries**

```bash
sqlite3 sales_database.db < sales_analysis.sql
```

Or open `sales_database.db` in [DB Browser for SQLite](https://sqlitebrowser.org/) or [SQLite Online](https://sqliteonline.com/) and paste the queries from `sales_analysis.sql`.

**Python script (5 business questions)**

```bash
python sql_python_integration.py
```

Results print in the terminal and are saved as CSV files in an `outputs/` folder.

**Notebook (10 business questions)**

```bash
jupyter notebook sql_data_extraction.ipynb
```

## SQL Concepts Covered

- **Fundamentals:** SELECT, WHERE, ORDER BY, LIMIT, GROUP BY, HAVING, INNER JOIN, LEFT JOIN
- **Advanced:** subqueries, CTEs (`WITH`), window functions (`ROW_NUMBER`, `RANK`, `LAG`, `LEAD`, running totals), views
- **Python integration:** SQLAlchemy engine, `pandas.read_sql()`, reusable utility module

## Business Questions Answered

1. Top 5 products by sales
2. Monthly sales trend and month-over-month growth
3. Customer segmentation by spend (Gold / Silver / Bronze)
4. Revenue by city
5. Cancellation and return rate by category
6. Revenue by product category, top customers, average order value, repeat customers, best seller per category (notebook)

## Notes

- Revenue figures only include orders with status `Completed`.
- The data is randomly generated (fixed seed `42`), so it is reproducible but not real.
- Window functions need SQLite 3.25 or later (included with any recent Python).

## Tools

Python · SQLite · SQLAlchemy · pandas · Jupyter
