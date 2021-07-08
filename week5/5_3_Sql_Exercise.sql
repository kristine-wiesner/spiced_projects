----EXERCISES 5.3 Characterize products and customers---

--1. Count total number of products. Count the number of products in the products table.

select count(*) from products;

--2. Separate currently available and discontinued products. Count separate numbers for currently available and discontinued products.

select * from products where discontinued = true;
select * from products where discontinued = false;

select count(*) from products where discontinued = true;
select count(*) from products where discontinued = false;

create view discontinuedproducts as select productname from products where discontinued = true;
create view currentproducts as select productname from products where discontinued = false;

select * from discontinuedproducts;

--3.Frequently ordered products. Count which product got ordered how many times.

select products.productname, count(order_details.productid) from order_details right join products on order_details.productid = products.productid group by products.productname order by count desc;

--4. Relative amount. Calculate the percentage of a product on the total number of orders.Verify that the sum of percentages is 100%.
   
select products.productname, round((count(order_details.productid) * 100.0 / (select count(*) from order_details)), 2) as percentage from order_details right join products on order_details.productid = products.productid group by products.productname order by percentage desc;

select sum(p.percentage) from (select (count(order_details.productid) * 100.0 / (select count(*) from order_details)) as percentage from order_details right join products on order_details.productid = products.productid) as p;

--5. Search your country (or a country of choice), From the Customers table, retrieve all rows containing your country.

SELECT * from customers where country  = 'Germany';