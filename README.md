# Harry Retail — Retail Management & Analytics System

A full-stack Flask + MySQL retail POS and analytics platform for small grocery stores, pharmacies, and local retail businesses.

---

## Features

| Module | What it does |
|--------|-------------|
| **Dashboard** | Today's revenue, monthly trend chart, top sellers, low-stock alerts, recent orders |
| **POS / New Sale** | Product grid by category, cart with qty controls, payment mode selection, atomic order completion |
| **Products** | Full CRUD — add, edit, delete, search, filter by category, sort by price/stock |
| **Order History** | Paginated order list with date/status filters, detailed order view |
| **Analytics** | Top 10 sellers, dead stock, revenue by category (doughnut chart), monthly growth %, inventory turnover, reorder alerts |

---

## Tech Stack

- **Backend**: Python 3.10+ · Flask 3 · SQLAlchemy ORM · Flask-Migrate
- **Database**: MySQL 8+ (PyMySQL driver)
- **Frontend**: Vanilla HTML/CSS/JS · Chart.js 4 (CDN) · Inter + JetBrains Mono fonts

---

## Folder Structure

```
harry_retail/
├── app.py                  # Flask app factory & blueprint registration
├── config.py               # MySQL + Flask settings
├── extensions.py           # SQLAlchemy + Migrate instances
├── models.py               # ORM models (Customer, Product, Order, OrderItem, Payment)
├── requirements.txt
├── setup_database.sql      # Schema + sample data
├── .env.example            # Environment variable template
│
├── routes/
│   ├── main.py             # Root redirect
│   ├── products.py         # CRUD + stock API
│   ├── sales.py            # POS + complete_sale endpoint
│   ├── orders.py           # Order history + detail
│   ├── dashboard.py        # KPI queries
│   └── analytics.py        # BI queries (top sellers, dead stock, etc.)
│
├── templates/
│   ├── base.html           # Sidebar layout + flash messages
│   ├── dashboard/index.html
│   ├── products/{index,add,edit}.html
│   ├── sales/{index,receipt}.html
│   ├── orders/{index,detail}.html
│   └── analytics/index.html
│
└── static/
    ├── css/main.css        # Design system (tokens, layout, components)
    └── js/main.js          # Sidebar toggle + utilities
```

---

## Setup Instructions

### 1. Create & activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure MySQL

Edit `config.py` OR copy `.env.example` → `.env` and set:

```
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=harry_retail
```

### 4. Create database & load schema

```bash
mysql -u root -p < setup_database.sql
```

### 5. Run the application

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

## Key Design Decisions

### Order Processing (atomic transaction)
When **Complete Sale** is clicked the backend:
1. Validates stock for every cart item
2. Creates an `orders` record
3. Creates `order_items` records
4. Deducts stock from `products`
5. Records payment in `payments`
All in a single `db.session` — rolled back entirely on any error.

### Analytics queries
All analytics use raw SQLAlchemy with `func.sum`, `func.date_format`, and subqueries — no pandas required. The `days` parameter lets you switch between 7/30/60/90-day windows.

### POS (no page reload)
Cart lives in JavaScript. `Complete Sale` POSTs JSON to `/sales/complete`. On success, stock badges on cards update in-place via DOM — no refresh needed.

---

## Currency & Localisation

Change `CURRENCY_SYMBOL` and `TAX_RATE` in `config.py`. The template uses `₹` by default (suitable for India). For GST, set `TAX_RATE = 0.18` and update the cart total calculation in `sales/index.html`.

---

## Next Steps (Future Analytics)

- Customer segmentation (RFM analysis)
- Demand forecasting (moving average)
- Supplier management module
- Export to CSV/Excel
- User authentication & role-based access
- WhatsApp/SMS low-stock alerts

---

## Database Schema

```sql
customers   → customer_id, name, email, city, signup_date
products    → product_id, product_name, category, price, stock
orders      → order_id, customer_id, order_date, order_status
order_items → order_item_id, order_id, product_id, quantity
payments    → payment_id, order_id, payment_mode, amount, payment_date
```
