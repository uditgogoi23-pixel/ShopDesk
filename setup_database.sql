-- ════════════════════════════════════════════════════════════════════════════
-- Harry Retail — Database Setup
-- Run: mysql -u root -p < setup_database.sql
-- ════════════════════════════════════════════════════════════════════════════

CREATE DATABASE IF NOT EXISTS harry_retail CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE harry_retail;

-- ── TABLES ──────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS customers (
    customer_id  INT PRIMARY KEY AUTO_INCREMENT,
    name         VARCHAR(100) NOT NULL,
    email        VARCHAR(150) UNIQUE,
    city         VARCHAR(50),
    signup_date  DATE DEFAULT (CURDATE())
);

CREATE TABLE IF NOT EXISTS products (
    product_id   INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(100) NOT NULL,
    category     VARCHAR(50),
    price        DECIMAL(10,2) NOT NULL,
    stock        INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS orders (
    order_id     INT PRIMARY KEY AUTO_INCREMENT,
    customer_id  INT,
    order_date   DATE DEFAULT (CURDATE()),
    order_status VARCHAR(30) DEFAULT 'Completed',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id      INT NOT NULL,
    product_id    INT NOT NULL,
    quantity      INT NOT NULL DEFAULT 1,
    FOREIGN KEY (order_id)   REFERENCES orders(order_id)   ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id   INT PRIMARY KEY AUTO_INCREMENT,
    order_id     INT NOT NULL,
    payment_mode VARCHAR(30) DEFAULT 'Cash',
    amount       DECIMAL(10,2) NOT NULL,
    payment_date DATE DEFAULT (CURDATE()),
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);

-- ── SAMPLE DATA ──────────────────────────────────────────────────────────────

INSERT INTO products (product_name, category, price, stock) VALUES
('Amul Butter 500g',       'Dairy & Eggs',           58.00,  45),
('Britannia Good Day',     'Snacks & Confectionery', 35.00,  80),
('Tata Salt 1kg',          'Groceries',              24.00,  60),
('Parle-G 800g',           'Snacks & Confectionery', 55.00,  70),
('Surf Excel 1kg',         'Household',              145.00, 25),
('Dettol Soap 3-pack',     'Personal Care',          87.00,  30),
('Maggi Noodles 4-pack',   'Groceries',              68.00,  55),
('Red Bull 250ml',         'Beverages',              115.00,  8),
('Coca-Cola 2L',           'Beverages',              75.00,  20),
('Bourn vita 500g',        'Beverages',              240.00, 12),
('Haldirams Mixture',      'Snacks & Confectionery', 60.00,  40),
('Dettol Handwash 200ml',  'Personal Care',          85.00,   5),
('Vim Bar 200g',           'Household',              25.00,  50),
('Amul Milk 1L',           'Dairy & Eggs',           60.00,  30),
('Kurkure Masala 80g',     'Snacks & Confectionery', 20.00, 100),
('Head & Shoulders 180ml', 'Personal Care',          199.00,  9),
('Fortune Sunflower Oil 1L','Groceries',             140.00, 20),
('Clinic Plus Shampoo',    'Personal Care',          175.00, 15),
('Lifebuoy Soap',          'Personal Care',          45.00,  35),
('Aashirvaad Atta 5kg',    'Groceries',              245.00,  2);

INSERT INTO customers (name, email, city) VALUES
('Ramesh Sharma',  'ramesh@example.com', 'Mumbai'),
('Priya Patel',    'priya@example.com',  'Pune'),
('Amit Verma',     'amit@example.com',   'Delhi');

-- Sample orders (today)
INSERT INTO orders (customer_id, order_date, order_status) VALUES (1, CURDATE(), 'Completed');
INSERT INTO order_items (order_id, product_id, quantity) VALUES (1, 1, 2), (1, 4, 1);
INSERT INTO payments (order_id, payment_mode, amount, payment_date) VALUES (1, 'UPI', 171.00, CURDATE());

INSERT INTO orders (customer_id, order_date, order_status) VALUES (2, CURDATE(), 'Completed');
INSERT INTO order_items (order_id, product_id, quantity) VALUES (2, 9, 1), (2, 8, 2);
INSERT INTO payments (order_id, payment_mode, amount, payment_date) VALUES (2, 'Cash', 305.00, CURDATE());

INSERT INTO orders (customer_id, order_date, order_status) VALUES (NULL, CURDATE(), 'Completed');
INSERT INTO order_items (order_id, product_id, quantity) VALUES (3, 3, 3), (3, 13, 2);
INSERT INTO payments (order_id, payment_mode, amount, payment_date) VALUES (3, 'Cash', 122.00, CURDATE());

SELECT 'Harry Retail database setup complete!' AS status;
