psql -d shopdb -c "SELECT name, amount FROM customers c JOIN orders o ON o.customer_id=c.customer_id WHERE o.amount > 600 ORDER BY o.amount DESC;"
