-- =====================================================================
-- sales_analysis.sql
-- Task 2: SQL for Data Extraction
-- Database: sales_database.db (SQLite)
-- Tables: customers, products, orders, order_items
-- Run in SQLite:  sqlite3 sales_database.db < sales_analysis.sql
-- =====================================================================


-- =====================================================================
-- PART 1: SQL FUNDAMENTALS (Day 7-8)
-- =====================================================================

-- 1.1 SELECT: preview each table
SELECT * FROM customers   LIMIT 5;
SELECT * FROM products    LIMIT 5;
SELECT * FROM orders      LIMIT 5;
SELECT * FROM order_items LIMIT 5;

-- 1.2 WHERE: completed orders placed in 2026
SELECT order_id, customer_id, order_date, status
FROM orders
WHERE status = 'Completed'
  AND order_date >= '2026-01-01';

-- 1.3 ORDER BY + LIMIT: 5 most expensive products
SELECT name, category, price
FROM products
ORDER BY price DESC
LIMIT 5;

-- 1.4 GROUP BY: number of customers per city
SELECT city, COUNT(*) AS total_customers
FROM customers
GROUP BY city
ORDER BY total_customers DESC;

-- 1.5 HAVING: categories with more than 3 products
SELECT category, COUNT(*) AS product_count, ROUND(AVG(price), 2) AS avg_price
FROM products
GROUP BY category
HAVING COUNT(*) > 3;

-- 1.6 JOIN: order line details (INNER JOIN across 4 tables)
SELECT o.order_id,
       o.order_date,
       c.name  AS customer,
       p.name  AS product,
       oi.quantity,
       oi.unit_price,
       oi.quantity * oi.unit_price AS line_total
FROM orders o
JOIN customers   c  ON c.customer_id = o.customer_id
JOIN order_items oi ON oi.order_id   = o.order_id
JOIN products    p  ON p.product_id  = oi.product_id
WHERE o.status = 'Completed'
ORDER BY o.order_date DESC
LIMIT 10;

-- 1.7 LEFT JOIN: customers who have never placed an order
SELECT c.customer_id, c.name, c.city
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL;

-- 1.8 Aggregates: revenue by product category
SELECT p.category,
       SUM(oi.quantity)                        AS units_sold,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
JOIN orders   o ON o.order_id   = oi.order_id
WHERE o.status = 'Completed'
GROUP BY p.category
ORDER BY revenue DESC;


-- =====================================================================
-- PART 2: ADVANCED SQL (Day 9-10)
-- =====================================================================

-- 2.1 SUBQUERY: products priced above the overall average price
SELECT name, category, price
FROM products
WHERE price > (SELECT AVG(price) FROM products)
ORDER BY price DESC;

-- 2.2 SUBQUERY (IN): customers who bought from the 'Electronics' category
SELECT DISTINCT c.customer_id, c.name
FROM customers c
WHERE c.customer_id IN (
    SELECT o.customer_id
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    JOIN products p     ON p.product_id = oi.product_id
    WHERE p.category = 'Electronics'
);

-- 2.3 CTE: customer spend and comparison with average spend
WITH customer_spend AS (
    SELECT o.customer_id,
           SUM(oi.quantity * oi.unit_price) AS total_spent
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'Completed'
    GROUP BY o.customer_id
)
SELECT c.name,
       ROUND(cs.total_spent, 2) AS total_spent,
       ROUND((SELECT AVG(total_spent) FROM customer_spend), 2) AS avg_spend
FROM customer_spend cs
JOIN customers c ON c.customer_id = cs.customer_id
WHERE cs.total_spent > (SELECT AVG(total_spent) FROM customer_spend)
ORDER BY cs.total_spent DESC;

-- 2.4 Multiple CTEs: monthly revenue
WITH completed_items AS (
    SELECT o.order_date, oi.quantity * oi.unit_price AS line_total
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'Completed'
),
monthly AS (
    SELECT strftime('%Y-%m', order_date) AS month,
           ROUND(SUM(line_total), 2)     AS revenue
    FROM completed_items
    GROUP BY month
)
SELECT * FROM monthly ORDER BY month;

-- 2.5 WINDOW FUNCTION - ROW_NUMBER: each customer's orders in sequence
SELECT customer_id,
       order_id,
       order_date,
       ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) AS order_number
FROM orders
ORDER BY customer_id, order_number
LIMIT 15;

-- 2.6 WINDOW FUNCTION - RANK: rank products by revenue within each category
WITH product_revenue AS (
    SELECT p.category,
           p.name AS product,
           SUM(oi.quantity * oi.unit_price) AS revenue
    FROM order_items oi
    JOIN products p ON p.product_id = oi.product_id
    JOIN orders   o ON o.order_id   = oi.order_id
    WHERE o.status = 'Completed'
    GROUP BY p.category, p.name
)
SELECT category,
       product,
       ROUND(revenue, 2) AS revenue,
       RANK() OVER (PARTITION BY category ORDER BY revenue DESC) AS rank_in_category
FROM product_revenue
ORDER BY category, rank_in_category;

-- 2.7 WINDOW FUNCTION - LAG: month-over-month revenue growth
WITH monthly AS (
    SELECT strftime('%Y-%m', o.order_date) AS month,
           SUM(oi.quantity * oi.unit_price) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'Completed'
    GROUP BY month
)
SELECT month,
       ROUND(revenue, 2) AS revenue,
       ROUND(LAG(revenue) OVER (ORDER BY month), 2) AS prev_month_revenue,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
             / LAG(revenue) OVER (ORDER BY month), 1) AS growth_pct
FROM monthly
ORDER BY month;

-- 2.8 WINDOW FUNCTION - LEAD: days until each customer's next order
SELECT customer_id,
       order_id,
       order_date,
       LEAD(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS next_order_date,
       CAST(julianday(LEAD(order_date) OVER (PARTITION BY customer_id ORDER BY order_date))
            - julianday(order_date) AS INTEGER) AS days_to_next_order
FROM orders
ORDER BY customer_id, order_date
LIMIT 15;

-- 2.9 Running total (window aggregate): cumulative revenue by month
WITH monthly AS (
    SELECT strftime('%Y-%m', o.order_date) AS month,
           SUM(oi.quantity * oi.unit_price) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status = 'Completed'
    GROUP BY month
)
SELECT month,
       ROUND(revenue, 2) AS revenue,
       ROUND(SUM(revenue) OVER (ORDER BY month), 2) AS cumulative_revenue
FROM monthly;


-- =====================================================================
-- PART 3: VIEWS FOR REUSABLE QUERIES
-- =====================================================================

-- 3.1 Flat view of all completed sales lines
DROP VIEW IF EXISTS vw_sales_detail;
CREATE VIEW vw_sales_detail AS
SELECT o.order_id,
       o.order_date,
       strftime('%Y-%m', o.order_date)   AS order_month,
       c.customer_id,
       c.name                            AS customer_name,
       c.city,
       p.product_id,
       p.name                            AS product_name,
       p.category,
       oi.quantity,
       oi.unit_price,
       oi.quantity * oi.unit_price       AS line_total
FROM orders o
JOIN customers   c  ON c.customer_id = o.customer_id
JOIN order_items oi ON oi.order_id   = o.order_id
JOIN products    p  ON p.product_id  = oi.product_id
WHERE o.status = 'Completed';

-- 3.2 Monthly sales summary view
DROP VIEW IF EXISTS vw_monthly_sales;
CREATE VIEW vw_monthly_sales AS
SELECT order_month,
       COUNT(DISTINCT order_id) AS orders,
       SUM(quantity)            AS units_sold,
       ROUND(SUM(line_total), 2) AS revenue
FROM vw_sales_detail
GROUP BY order_month;

-- 3.3 Customer spend + segment view (Gold / Silver / Bronze)
DROP VIEW IF EXISTS vw_customer_segments;
CREATE VIEW vw_customer_segments AS
SELECT customer_id,
       customer_name,
       city,
       COUNT(DISTINCT order_id)   AS orders,
       ROUND(SUM(line_total), 2)  AS total_spent,
       CASE
           WHEN SUM(line_total) >= 80000 THEN 'Gold'
           WHEN SUM(line_total) >= 45000 THEN 'Silver'
           ELSE 'Bronze'
       END AS segment
FROM vw_sales_detail
GROUP BY customer_id, customer_name, city;

-- 3.4 Use the views
SELECT * FROM vw_monthly_sales ORDER BY order_month;
SELECT segment, COUNT(*) AS customers, ROUND(SUM(total_spent), 2) AS revenue
FROM vw_customer_segments
GROUP BY segment
ORDER BY revenue DESC;
