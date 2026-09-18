#!/usr/bin/env bash
psql -d shopdb -q \
 -c "DROP TABLE IF EXISTS orders, customers CASCADE;" \
 -c "CREATE TABLE customers (customer_id SERIAL PRIMARY KEY, name TEXT NOT NULL, city TEXT);" \
 -c "CREATE TABLE orders (order_id SERIAL PRIMARY KEY, customer_id INT NOT NULL REFERENCES customers(customer_id), amount NUMERIC(8,2));" \
 -c "INSERT INTO customers (name, city) VALUES ('Mohit','Ghaziabad'),('Priya','Delhi');" \
 -c "INSERT INTO orders (customer_id, amount) VALUES (1, 500.00), (2, 1250.50);"
