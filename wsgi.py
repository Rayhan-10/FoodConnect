"""Production WSGI entry point for Gunicorn and Render."""
import os
from app import app, db, upgrade_local_schema

if os.getenv('FLASK_ENV') == 'production' and not os.getenv('SECRET_KEY'):
    raise RuntimeError('SECRET_KEY must be configured in the production environment.')

with app.app_context():
    db.create_all()
    upgrade_local_schema()

if os.getenv('COOKIE_SECURE', '0') == '1':
    app.config['SESSION_COOKIE_SECURE'] = True
