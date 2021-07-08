
--Analyze the Northwind Dataset Exercise



Throughout the week write SQL queries to answer the questions below



1. Get the names and the quantities in stock for each product.

select productname, unitsinstock from products;

2. Get a list of current products (Product ID and name).

select productid, productname from products where discontinued = false;

3. Get a list of the most and least expensive products (name and unit price).

select productname, unitprice from products order by unitprice desc;

4. Get products that cost less than $20.

select productname, unitprice from products where unitprice < 20;

5. Get products that cost between $15 and $25.

select productname, unitprice from products where unitprice < 25 and unitprice > 15;

6. Get products above average price.

select productname, unitprice from products where unitprice > (select AVG(unitprice) from products);

7. Find the ten most expensive products.

select productname, unitprice from products order by unitprice desc limit 10;

8. Get a list of discontinued products (Product ID and name).

select productid, productname from products where discontinued = true;

9. Count current and discontinued products.

select count(*) from products where discontinued = true 
select count(*) from products where discontinued = false;


SELECT SCount(productname) FROM products GROUP BY discontinued;

10. Find products with less units in stock than the quantity on order.

select productname, unitsinstock, unitsonorder from products where unitsinstock < unitsonorder;


SELECT ProductName,  UnitsOnOrder , UnitsInStock
FROM Products
WHERE (((Discontinued)=False) AND ((UnitsInStock)<UnitsOnOrder));

11. Find the customer who had the highest order amount

select c.companyname, count(*) from orders o join (select customerid, companyname from customers) c on o.customerid = c.customerid group by o.customerid, c.companyname order by count desc limit 1;

SELECT customerid, COUNT(DISTINCT orderid), MAX(order) FROM order GROUP BY customerid ORDER BY 2 DESC;

SELECT customerid,orderdate,MAX(quantity) 
FROM orders 
GROUP BY customerid,orderdate 
HAVING MAX(quantity)>2000.00;

select c.companyname, (od.unitprice * od.quantity) as total from orders o right join order_details od on o.orderid = od.orderid left join customers c on c.customerid = o.customerid order by total desc;


12. Get orders for a given employee and the according customer

select e.lastname, o.orderid from employees e right join (select orderid, employeeid from orders) o on e.employeeid = o.employeeid;

13. Find the hiring age of each employee

select lastname, firstname, titleofcourtesy,( DATE_PART('year', hiredate) - DATE_PART('year', birthdate)) as hiringage from employees;

14. Create views and/or named queries for some of these queries

create view discontinuedproducts as select productname from products where discontinued = true;
create view currentproducts as select productname from products where discontinued = false;
