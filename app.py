"""
Harry Retail - Retail Management & Analytics System
Main Flask Application Entry Point
"""

from flask import Flask
from datetime import datetime
from config import Config
from extensions import db, migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Inject `now` into every template
    @app.context_processor
    def inject_globals():
        return {'now': datetime.now()}

    # Register blueprints
    from routes.main import main_bp
    from routes.products import products_bp
    from routes.sales import sales_bp
    from routes.orders import orders_bp
    from routes.dashboard import dashboard_bp
    from routes.analytics import analytics_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(sales_bp, url_prefix='/sales')
    app.register_blueprint(orders_bp, url_prefix='/orders')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
