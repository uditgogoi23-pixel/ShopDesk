"""
Harry Retail - Retail Management & Analytics System
Main Flask Application Entry Point
"""
from dotenv import load_dotenv
load_dotenv()
import os
from flask import Flask
from datetime import datetime
from config import Config
from extensions import db, migrate


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.config["UPLOAD_FOLDER"] = os.path.join(
        app.root_path,
        "static",
        "product_images"
    )
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ── Initialize extensions ─────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)

    # ── Inject `now` into every template ──────────────────────────────────
    @app.context_processor
    def inject_globals():
        return {'now': datetime.utcnow()}
    @app.context_processor
    def global_sidebar_data():
        from models import Product

        low_stock_count = Product.query.filter(
            Product.stock <= Product.reorder_level
        ).count()

        return {
            "low_stock_count": low_stock_count
        }

    # ── Register blueprints ───────────────────────────────────────────────
    from routes.main       import main_bp
    from routes.products   import products_bp
    from routes.sales      import sales_bp
    from routes.orders     import orders_bp
    from routes.dashboard  import dashboard_bp
    from routes.analytics  import analytics_bp
    from routes.customers  import customers_bp
    from routes.suppliers  import suppliers_bp
    from routes.export     import export_bp
    from routes.stocks     import stock_bp
    from routes.import_purchases import purchase_import_bp
    from routes.import_suppliers import supplier_import_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp,      url_prefix='/products')
    app.register_blueprint(sales_bp,         url_prefix='/sales')
    app.register_blueprint(orders_bp,        url_prefix='/orders')
    app.register_blueprint(dashboard_bp,     url_prefix='/dashboard')
    app.register_blueprint(analytics_bp,     url_prefix='/analytics')
    app.register_blueprint(customers_bp,     url_prefix='/customers')
    app.register_blueprint(suppliers_bp,     url_prefix='/suppliers')
    app.register_blueprint(export_bp,        url_prefix='/export')
    app.register_blueprint(stock_bp,         url_prefix='/stock')
    app.register_blueprint(purchase_import_bp)
    app.register_blueprint(supplier_import_bp, url_prefix='/supplier-import')
    from models import Product

    @app.context_processor
    def inject_sidebar_data():
        low_stock_count = Product.query.filter(
            Product.stock <= Product.reorder_level
        ).count()

        return dict(low_stock_count=low_stock_count)
    # ── Optional blueprints (register only if the route file exists) ──────
    _optional = [
        ('routes.settings', 'settings_bp', '/settings'),
        ('routes.imports',  'imports_bp',  '/imports'),
    ]
    for module_path, bp_name, url_prefix in _optional:
        try:
            module = __import__(module_path, fromlist=[bp_name])
            bp = getattr(module, bp_name)
            app.register_blueprint(bp, url_prefix=url_prefix)
        except ImportError:
            app.logger.warning(
                f"Optional blueprint '{bp_name}' not found ({module_path}) — skipping."
            )

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
