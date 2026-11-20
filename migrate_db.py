"""Run non-destructive FoodConnect schema upgrades for an existing database."""
from app import app, db, upgrade_local_schema

with app.app_context():
    db.create_all()
    upgrade_local_schema()

print('FoodConnect database schema is up to date.')
