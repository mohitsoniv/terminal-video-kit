psql -d shopdb -c "UPDATE customers SET city = 'Noida' WHERE name = 'Mohit' RETURNING customer_id, name, city;"
