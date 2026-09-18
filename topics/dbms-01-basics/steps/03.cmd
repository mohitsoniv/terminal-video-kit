psql -d shopdb -c "CREATE TABLE orders (order_id SERIAL PRIMARY KEY, customer_id INT NOT NULL REFERENCES customers(customer_id), amount NUMERIC(8,2));"
