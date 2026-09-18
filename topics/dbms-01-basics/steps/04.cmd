psql -d shopdb -c "INSERT INTO customers (name, city) VALUES ('Mohit','Ghaziabad'),('Priya','Delhi') RETURNING customer_id, name;"
