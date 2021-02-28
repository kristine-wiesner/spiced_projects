

\copy products FROM 'C:\Users\Kristine\spicednotes\northwind_data_clean-master\data\products.csv' DELIMITER ',' CSV HEADER;



CREATE TABLE products (productID,productName,supplierID,categoryID,quantityPerUnit,unitPrice,unitsInStock,unitsOnOrder,reorderLevel,discontinued);

\COPY products (productID,productName,supplierID,categoryID,quantityPerUnit,unitPrice,unitsInStock,unitsOnOrder,reorderLevel,discontinued
) FROM 'C:\Users\Kristine\spicednotes\northwind_data_clean-master\data\products.csv' CSV HEADER DELIMITER ',';

CREATE TABLE products(
    productID INT PRIMARY KEY,
    productName VARCHAR(100),
    supplierID INT,
    categoryID INT,
    quantityPerUnit VARCHAR(100),
    unitPrice REAL,
    unitsInStock INT,
    unitsOnOrder INT,
    reorderLevel INT,
    discontinued BOOLEAN
)

CREATE TABLE suppliers(
    supplierID INT PRIMARY KEY,
    companyName VARCHAR(100),
    contactName VARCHAR(100),
    contactTitle VARCHAR(100),
    address VARCHAR(100),
    city VARCHAR(100),
    region VARCHAR(100),
    postalCode VARCHAR(100),
    country VARCHAR(100),
    phone VARCHAR(100),
    fax VARCHAR(100),
    homePage VARCHAR(100)
);

\copy suppliers FROM 'C:\Users\Kristine\spicednotes\northwind_data_clean-master\data\suppliers.csv' DELIMITER ',' CSV HEADER;

ALTER TABLE products ADD CONSTRAINT suppliers_fk FOREIGN KEY (supplierid) REFERENCES suppliers (supplierid) on delete cascade on update cascade;


\d+ products

CREATE TABLE categories(
    categoryID INT PRIMARY KEY,
    categoryName VARCHAR(100),
    description VARCHAR(100),
    picture BYTEA
);

\copy categories FROM 'C:\Users\Kristine\spicednotes\northwind_data_clean-master\data\categories.csv' DELIMITER ',' CSV HEADER;

ALTER TABLE products ADD CONSTRAINT categories_fk FOREIGN KEY (categoryid) REFERENCES categories (categoryid);

CREATE TABLE customers(
    customerID VARCHAR(5) PRIMARY KEY,
    companyName VARCHAR(100),
    contactName VARCHAR(100),
    contactTitle VARCHAR(100),
    address VARCHAR(100),
    city VARCHAR(100),
    region VARCHAR(100),
    postalCode VARCHAR(100),
    country VARCHAR(100),
    phone VARCHAR(100),
    fax VARCHAR(100)
);

\copy customers FROM 'C:\Users\Kristine\spicednotes\northwind_data_clean-master\data\customers.csv' DELIMITER ',' CSV HEADER;

CREATE TABLE territories(
    territoryID VARCHAR(5) PRIMARY KEY,
    territoryDescription VARCHAR(100),
    regionID INT,
    CONSTRAINT regions_fk FOREIGN KEY (regionid) REFERENCES regions (regionid)
);

\copy territories FROM 'C:\Users\Kristine\spicednotes\northwind_data_clean-master\data\territories.csv' DELIMITER ',' CSV HEADER;

CREATE TABLE regions(
    regionid INT PRIMARY KEY,
    regionDescription VARCHAR(100)
);

\copy regions FROM 'C:\Users\Kristine\spicednotes\northwind_data_clean-master\data\regions.csv' DELIMITER ',' CSV HEADER;

CREATE TABLE employees (
    employeeID INT PRIMARY KEY,
    lastName VARCHAR(100),
    firstName VARCHAR(100),
    title VARCHAR(100),
    titleOfCourtesy VARCHAR(100),
    birthDate DATE,
    hireDate DATE,
    address VARCHAR(100),
    city VARCHAR(100),
    region VARCHAR(100),
    postalCode VARCHAR(100),
    country VARCHAR(100),
    homePhone VARCHAR(100),
    extension VARCHAR(100),
    photo BYTEA,
    notes TEXT,
    reportsTo INT,
    photoPath VARCHAR(100)
)

\copy employees FROM 'C:\Users\Kristine\spicednotes\northwind_data_clean-master\data\employees.csv' DELIMITER ',' CSV HEADER  NULL AS 'NULL';

ALTER TABLE employees ADD CONSTRAINT employees_fk FOREIGN KEY (reportsto) REFERENCES employees (employeeid);

CREATE TABLE employee_territories(
    employeeID INT,
    territoryID VARCHAR(5),
    CONSTRAINT employee_fk FOREIGN KEY (employeeid) REFERENCES employees (employeeid),
    CONSTRAINT territory_fk FOREIGN KEY (territoryid) REFERENCES territories (territoryid)
);

\copy employee_territories FROM 'C:\Users\Kristine\spicednotes\northwind_data_clean-master\data\employee_territories.csv' DELIMITER ',' CSV HEADER;

CREATE TABLE shippers (
    shipperID INT PRIMARY KeY,
    companyName VARCHAR(100),
    phone VARCHAR (100)
);

\copy shippers FROM 'C:\Users\Kristine\spicednotes\northwind_data_clean-master\data\shippers.csv' DELIMITER ',' CSV HEADER;




CREATE TABLE orders (
    orderID INT PRIMARY KEY,
    customerID VARCHAR(5),
    employeeID INT,
    orderDate DATE,
    requiredDate DATE,
    shippedDate DATE,
    shipVia INT,
    freight REAL,
    shipName VARCHAR(100),
    shipAddress VARCHAR(100),
    shipCity VARCHAR(100),
    shipRegion VARCHAR(100) NULL,
    shipPostalCode VARCHAR(100),
    shipCountry VARCHAR(100),
    CONSTRAINT customer_fk FOREIGN KEY (customerid) REFERENCES customers (customerid),
    CONSTRAINT employee_fk FOREIGN KEY (employeeid) REFERENCES employees (employeeid),
    CONSTRAINT shippers_fk FOREIGN KEY (shipvia) REFERENCES shippers (shipperid)
);

\copy orders FROM 'C:\Users\Kristine\spicednotes\northwind_data_clean-master\data\orders.csv' DELIMITER ',' CSV HEADER NULL AS 'NULL';

CREATE TABLE order_details (
    orderID INT,
    productID INT,
    unitPrice REAL,
    quantity INT,
    discount REAL,
    CONSTRAINT order_fk FOREIGN KEY (orderid) REFERENCES orders (orderid),
    CONSTRAINT product_fk FOREIGN KEY (productid) REFERENCES products (productid)
);

\copy order_details FROM 'C:\Users\Kristine\spicednotes\northwind_data_clean-master\data\order_details.csv' DELIMITER ',' CSV HEADER;



SELECT category_id AS cat, max(unit_price), round(avg(unit_price), 2), count(name)
  FROM products
  WHERE unit_price > 10
  GROUP BY cat
  HAVING count(name) >= 8
  ORDER BY max(unit_price) DESC
  OFFSET 1
  LIMIT 3;



psql -d northwind -f products.sql
