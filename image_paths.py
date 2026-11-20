"""Single source of truth for FoodConnect photograph file names.

No Flask import here, so the web app, seed_data.py and the tools/ scripts can
all use it.  Every seeded restaurant and food item has ONE predictable local
file under static/images/ (JPEG).  Nothing is fetched from the internet at
runtime.
"""
import re

FALLBACK_REL = 'images/fallback/photo-unavailable.jpg'


def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', (text or '').lower()).strip('-')


def restaurant_photo_rel(restaurant_name):
    return f'images/restaurants/{slugify(restaurant_name)}.jpg'


def food_photo_rel(restaurant_name, food_name):
    return f'images/food/{slugify(restaurant_name)}--{slugify(food_name)}.jpg'
