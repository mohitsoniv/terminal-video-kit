psql -d shopdb -c "SELECT c.name, c.city, o.order_id, o.amount FROM customers c JOIN orders o ON o.customer_id = c.customer_id ORDER BY o.order_id;"
