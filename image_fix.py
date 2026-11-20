
import os
from app import app
from models import db, Restaurant, FoodItem

BASE = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE, "static", "images", "verified")

def find_image(prefix, item_id):
    for ext in (".jpg", ".png", ".webp"):
        path = os.path.join(IMAGE_DIR, f"{prefix}_{item_id}{ext}")
        if os.path.isfile(path):
            return f"images/verified/{prefix}_{item_id}{ext}"
    return None

with app.app_context():
    food_updated = 0
    food_missing = []
    restaurant_updated = 0
    restaurant_missing = []

    for item in FoodItem.query.order_by(FoodItem.id).all():
        image_path = find_image("food", item.id)
        if image_path:
            item.image_path = image_path
            food_updated += 1
        else:
            food_missing.append(item.name)

    for place in Restaurant.query.order_by(Restaurant.id).all():
        image_path = find_image("restaurant", place.id)
        if image_path:
            place.cover_image = image_path
            restaurant_updated += 1
        else:
            restaurant_missing.append(place.name)

    db.session.commit()

    print("=" * 50)
    print("FOODCONNECT IMAGE DATABASE UPDATE")
    print("=" * 50)
    print("Food images connected:", food_updated)
    print("Restaurant images connected:", restaurant_updated)
    print("\nFood images still missing:", len(food_missing))
    for name in food_missing:
        print(" -", name)

    print("\nRestaurant images still missing:", len(restaurant_missing))
    for name in restaurant_missing:
        print(" -", name)

    print("\nDatabase update completed.")
