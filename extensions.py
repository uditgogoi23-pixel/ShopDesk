"""
Harry Retail - Flask Extensions
Centralized extension initialization to avoid circular imports
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db      = SQLAlchemy()
migrate = Migrate()
