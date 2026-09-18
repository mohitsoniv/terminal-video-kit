psql -d shopdb -c "DELETE FROM customers WHERE customer_id = 3 RETURNING customer_id, name;"
