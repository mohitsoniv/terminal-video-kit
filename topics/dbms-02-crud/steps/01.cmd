psql -d shopdb -c "INSERT INTO customers (name, city) VALUES ('Neha','Gurugram') RETURNING customer_id, name, city;"
