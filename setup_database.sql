-- ════════════════════════════════════════════════════════════════════════════
-- Harry Retail — Database Setup
-- Run: mysql -u root -p < setup_database.sql
--
-- Fixed:
--   - DB name matches config.py (harry_retail)
--   - All columns match models.py exactly
--   - stock and quantity changed from INT to DECIMAL(10,3)
--   - Added missing tables: stock_entries, business_settings, suppliers
-- ════════════════════════════════════════════════════════════════════════════



USE ShopDesk;

-- ── TABLES ──────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS customers (
    customer_id INT          PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL,
    phone       VARCHAR(20)  UNIQUE,
    email       VARCHAR(150) UNIQUE,
    city        VARCHAR(50),
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id   INT          PRIMARY KEY AUTO_INCREMENT,
    supplier_name VARCHAR(120) NOT NULL,
    phone         VARCHAR(20),
    email         VARCHAR(120),
    gst_number    VARCHAR(30),
    address       TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    product_id     INT           PRIMARY KEY AUTO_INCREMENT,
    product_name   VARCHAR(100)  NOT NULL,
    category       VARCHAR(50),
    price          DECIMAL(10,2) NOT NULL,
    stock          DECIMAL(10,3) DEFAULT 0,        -- Fixed: was INT, now supports weight
    unit_type      VARCHAR(20)   NOT NULL DEFAULT 'Units',
    cost_price     DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    discount_type  VARCHAR(10)   DEFAULT 'none',
    discount_value DECIMAL(10,2) DEFAULT 0,
    reorder_level  INT           NOT NULL DEFAULT 10,
    image          VARCHAR(255)  DEFAULT 'default_product.png'
);

CREATE TABLE IF NOT EXISTS orders (
    order_id     INT           PRIMARY KEY AUTO_INCREMENT,
    invoice_no   VARCHAR(20)   UNIQUE,
    customer_id  INT,
    order_date   DATE          DEFAULT (CURDATE()),
    total_amount DECIMAL(10,2),
    discount     DECIMAL(10,2) DEFAULT 0,
    gst_amount   DECIMAL(10,2) DEFAULT 0,
    grand_total  DECIMAL(10,2) DEFAULT 0,
    payment_mode VARCHAR(30),
    order_status VARCHAR(30)   DEFAULT 'Completed',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INT           PRIMARY KEY AUTO_INCREMENT,
    order_id      INT           NOT NULL,
    product_id    INT           NOT NULL,
    quantity      DECIMAL(10,3) NOT NULL DEFAULT 1.000,  -- Fixed: was INT
    unit_type     VARCHAR(20)   NOT NULL DEFAULT 'Units',
    selling_price DECIMAL(10,2) NOT NULL DEFAULT 0,
    cost_price    DECIMAL(10,2) NOT NULL DEFAULT 0,
    unit_price    DECIMAL(10,2) NOT NULL DEFAULT 0,      -- Fixed: non-nullable
    subtotal      DECIMAL(10,2),
    FOREIGN KEY (order_id)   REFERENCES orders(order_id)   ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id   INT           PRIMARY KEY AUTO_INCREMENT,
    order_id     INT           NOT NULL,
    payment_mode VARCHAR(30)   DEFAULT 'Cash',
    amount       DECIMAL(10,2) NOT NULL,
    payment_date DATE          DEFAULT (CURDATE()),
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS stock_entries (
    entry_id       INT           PRIMARY KEY AUTO_INCREMENT,
    product_id     INT           NOT NULL,
    quantity_added DECIMAL(10,3) NOT NULL,
    previous_stock DECIMAL(10,3) NOT NULL,
    new_stock      DECIMAL(10,3) NOT NULL,
    remarks        VARCHAR(255),
    supplier_name  VARCHAR(100),
    invoice_no     VARCHAR(50),
    purchase_price DECIMAL(10,2) NOT NULL DEFAULT 0,
    gst_percent    DECIMAL(5,2)  NOT NULL DEFAULT 0,
    gst_amount     DECIMAL(10,2) NOT NULL DEFAULT 0,
    invoice_total  DECIMAL(10,2) NOT NULL DEFAULT 0,
    gst_claimed    TINYINT(1)    NOT NULL DEFAULT 0,
    entry_date     DATETIME      DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS business_settings (
    id                    INT           PRIMARY KEY AUTO_INCREMENT,
    shop_name             VARCHAR(120)  NOT NULL DEFAULT 'ShopDesk',
    owner_name            VARCHAR(120),
    phone                 VARCHAR(20),
    email                 VARCHAR(120),
    address               TEXT,
    business_type         VARCHAR(20)   NOT NULL DEFAULT 'Retail',
    gst_enabled           TINYINT(1)    NOT NULL DEFAULT 0,
    gst_mode              VARCHAR(20)   NOT NULL DEFAULT 'Inclusive',
    gst_number            VARCHAR(30),
    default_gst_rate      DECIMAL(5,2)  NOT NULL DEFAULT 18.00,
    gst_registration_type VARCHAR(20)   NOT NULL DEFAULT 'Regular',
    currency              VARCHAR(10)   NOT NULL DEFAULT 'INR',
    created_at            DATETIME      DEFAULT CURRENT_TIMESTAMP,
    updated_at            DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ── DEFAULT BUSINESS SETTINGS ROW ────────────────────────────────────────────
INSERT INTO business_settings (shop_name, business_type, currency)
VALUES ('Harry Retail', 'Retail', 'INR');

-- ── SAMPLE DATA ──────────────────────────────────────────────────────────────

INSERT INTO products
    (product_name, category, price, stock, unit_type, cost_price, reorder_level)
VALUES
    ('Amul Butter 500g',       'Dairy & Eggs',            58.00,  45,  'Units', 48.00,  10),
    ('Britannia Good Day',     'Snacks & Confectionery',  35.00,  80,  'Units', 28.00,  15),
    ('Tata Salt 1kg',          'Groceries',               24.00,  60,  'Units', 18.00,  20),
    ('Parle-G 800g',           'Snacks & Confectionery',  55.00,  70,  'Units', 44.00,  15),
    ('Surf Excel 1kg',         'Household',              145.00,  25,  'Units', 120.00, 10),
    ('Dettol Soap 3-pack',     'Personal Care',           87.00,  30,  'Units', 70.00,  10),
    ('Maggi Noodles 4-pack',   'Groceries',               68.00,  55,  'Units', 55.00,  15),
    ('Red Bull 250ml',         'Beverages',              115.00,   8,  'Units', 95.00,  10),
    ('Coca-Cola 2L',           'Beverages',               75.00,  20,  'Units', 60.00,  10),
    ('Bournvita 500g',         'Beverages',              240.00,  12,  'Units', 200.00, 5),
    ('Haldirams Mixture',      'Snacks & Confectionery',  60.00,  40,  'Units', 48.00,  10),
    ('Dettol Handwash 200ml',  'Personal Care',           85.00,   5,  'Units', 68.00,  10),
    ('Vim Bar 200g',           'Household',               25.00,  50,  'Units', 18.00,  15),
    ('Amul Milk 1L',           'Dairy & Eggs',            60.00,  30,  'Units', 50.00,  10),
    ('Kurkure Masala 80g',     'Snacks & Confectionery',  20.00, 100,  'Units', 14.00,  20),
    ('Head & Shoulders 180ml', 'Personal Care',          199.00,   9,  'Units', 160.00, 5),
    ('Fortune Sunflower Oil 1L','Groceries',             140.00,  20,  'kg',    115.00, 5),
    ('Clinic Plus Shampoo',    'Personal Care',          175.00,  15,  'Units', 140.00, 5),
    ('Lifebuoy Soap',          'Personal Care',           45.00,  35,  'Units', 35.00,  10),
    ('Aashirvaad Atta 5kg',    'Groceries',              245.00,   2,  'kg',    210.00, 5);

INSERT INTO customers (name, phone, email, city) VALUES
    ('Ramesh Sharma', '9876543210', 'ramesh@example.com', 'Mumbai'),
    ('Priya Patel',   '9812345678', 'priya@example.com',  'Pune'),
    ('Amit Verma',    '9898989898', 'amit@example.com',   'Delhi');

-- ── Sample Order 1 ─────────────────────────────────────────────────────────
-- 2x Amul Butter (₹58) + 1x Parle-G (₹55) = ₹171
INSERT INTO orders
    (invoice_no, customer_id, order_date, total_amount, grand_total, payment_mode, order_status)
VALUES
    ('INV-0001', 1, CURDATE(), 171.00, 171.00, 'UPI', 'Completed');

INSERT INTO order_items
    (order_id, product_id, quantity, unit_type, selling_price, cost_price, unit_price, subtotal)
VALUES
    (1, 1, 2.000, 'Units', 58.00, 48.00, 58.00, 116.00),
    (1, 4, 1.000, 'Units', 55.00, 44.00, 55.00,  55.00);

INSERT INTO payments (order_id, payment_mode, amount, payment_date)
VALUES (1, 'UPI', 171.00, CURDATE());

-- ── Sample Order 2 ─────────────────────────────────────────────────────────
-- 1x Coca-Cola (₹75) + 2x Red Bull (₹115) = ₹305
INSERT INTO orders
    (invoice_no, customer_id, order_date, total_amount, grand_total, payment_mode, order_status)
VALUES
    ('INV-0002', 2, CURDATE(), 305.00, 305.00, 'Cash', 'Completed');

INSERT INTO order_items
    (order_id, product_id, quantity, unit_type, selling_price, cost_price, unit_price, subtotal)
VALUES
    (2, 9, 1.000, 'Units',  75.00, 60.00,  75.00,  75.00),
    (2, 8, 2.000, 'Units', 115.00, 95.00, 115.00, 230.00);

INSERT INTO payments (order_id, payment_mode, amount, payment_date)
VALUES (2, 'Cash', 305.00, CURDATE());

-- ── Sample Order 3 (walk-in, no customer) ──────────────────────────────────
-- 3x Tata Salt (₹24) + 2x Vim Bar (₹25) = ₹122
INSERT INTO orders
    (invoice_no, customer_id, order_date, total_amount, grand_total, payment_mode, order_status)
VALUES
    ('INV-0003', NULL, CURDATE(), 122.00, 122.00, 'Cash', 'Completed');

INSERT INTO order_items
    (order_id, product_id, quantity, unit_type, selling_price, cost_price, unit_price, subtotal)
VALUES
    (3, 3,  3.000, 'Units', 24.00, 18.00, 24.00, 72.00),
    (3, 13, 2.000, 'Units', 25.00, 18.00, 25.00, 50.00);

INSERT INTO payments (order_id, payment_mode, amount, payment_date)
VALUES (3, 'Cash', 122.00, CURDATE());

SELECT 'Harry Retail database setup complete!' AS status;