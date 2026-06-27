"""
Harry Retail - Configuration
MySQL database connection and Flask settings
"""

import os
from datetime import timedelta


class Config:
    # ─────────────────────────────────────────────
    # SECURITY
    # ─────────────────────────────────────────────
    # Set SECRET_KEY in your .env file — never leave this as a default in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        import secrets
        SECRET_KEY = secrets.token_hex(32)   # Random key each restart (dev only)

    # ─────────────────────────────────────────────
    # DATABASE — set these in your .env file
    # ─────────────────────────────────────────────
    MYSQL_HOST     = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER     = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
  
    MYSQL_DB = os.environ.get('MYSQL_DB', 'ShopDesk')   # Fixed: matches setup_database.sql
    MYSQL_PORT     = int(os.environ.get('MYSQL_PORT', 3306))

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }

    # ─────────────────────────────────────────────
    # SESSION / COOKIE
    # ─────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY  = True
    SESSION_COOKIE_SAMESITE  = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # ─────────────────────────────────────────────
    # BUSINESS SETTINGS
    # ─────────────────────────────────────────────
    CURRENCY_SYMBOL    = '₹'     # Change to $ or £ as needed
    LOW_STOCK_THRESHOLD = 10     # Global fallback alert threshold
    BUSINESS_NAME      = 'Harry Retail'
    TAX_RATE           = 0.0    # Set GST/VAT rate e.g. 0.18 for 18%