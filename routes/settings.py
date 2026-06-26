from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import BusinessSettings

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/', methods=['GET', 'POST'])
def index():
    settings = BusinessSettings.query.first()

    # Create default settings if none exist
    if not settings:
        settings = BusinessSettings()
        db.session.add(settings)
        db.session.commit()

    if request.method == 'POST':
        settings.shop_name            = request.form.get('shop_name', '').strip()
        settings.owner_name           = request.form.get('owner_name', '').strip()
        settings.phone                = request.form.get('phone', '').strip()
        settings.email                = request.form.get('email', '').strip()
        settings.address              = request.form.get('address', '').strip()
        settings.business_type        = request.form.get('business_type', 'Retail')
        settings.currency             = request.form.get('currency', 'INR')
        settings.gst_enabled          = request.form.get('gst_enabled') == 'on'
        settings.gst_number           = request.form.get('gst_number', '').strip()
        settings.default_gst_rate     = float(request.form.get('default_gst_rate', 18))
        settings.gst_mode             = request.form.get('gst_mode', 'Inclusive')
        settings.gst_registration_type = request.form.get('gst_registration_type', 'Regular')

        db.session.commit()
        flash('✓ Settings saved successfully.', 'success')
        return redirect(url_for('settings.index'))

    return render_template('settings/index.html', settings=settings)