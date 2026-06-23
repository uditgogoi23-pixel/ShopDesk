"""
Harry Retail - Main Routes
Home redirect and general pages
"""

from flask import Blueprint, redirect, url_for

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return redirect(url_for('dashboard.index'))
