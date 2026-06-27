"""
Harry Retail - Retail Management & Analytics System
Main Flask Application Entry Point
"""
from routes.stocks import stock_bp
from flask import Flask
from datetime import datetime
from config import Config
from extensions import db, migrate
from routes.customers import customers_bp
from routes.imports import imports_bp
from routes.export import export_bp
import os
from routes.import_suppliers import supplier_import_bp
from routes.import_purchases import purchase_import_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["UPLOAD_FOLDER"] = os.path.join(
    app.root_path,
    "static",
    "product_images"
)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
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
    from routes.suppliers import suppliers_bp
    from routes.sales import sales_bp
    from routes.orders import orders_bp
    from routes.dashboard import dashboard_bp
    from routes.analytics import analytics_bp
    from routes.settings import settings_bp

    app.register_blueprint(stock_bp, url_prefix='/stock')
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(suppliers_bp, url_prefix='/suppliers')
    app.register_blueprint(imports_bp, url_prefix="/imports")
    app.register_blueprint(export_bp, url_prefix="/export")
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(supplier_import_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(sales_bp, url_prefix='/sales')
    app.register_blueprint(orders_bp, url_prefix='/orders')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(purchase_import_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
