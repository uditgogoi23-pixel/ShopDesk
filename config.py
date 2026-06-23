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
    SECRET_KEY = os.environ.get('SECRET_KEY', 'harry-retail-secret-key-2024')

    # ─────────────────────────────────────────────
    # DATABASE — edit these to match your MySQL setup
    # ─────────────────────────────────────────────
    MYSQL_HOST     = os.environ.get('MYSQL_HOST',     'localhost')
    MYSQL_USER     = os.environ.get('MYSQL_USER',     'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '785663')
    MYSQL_DB       = os.environ.get('MYSQL_DB',       'harry_retail')
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
    # APP SETTINGS
    # ─────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # ─────────────────────────────────────────────
    # BUSINESS SETTINGS
    # ─────────────────────────────────────────────
    CURRENCY_SYMBOL   = '₹'    # Change to $ or £ as needed
    LOW_STOCK_THRESHOLD = 10   # Alert when stock falls below this
    BUSINESS_NAME     = 'Harry Retail'
    TAX_RATE          = 0.0    # Set GST / VAT rate e.g. 0.18 for 18%
