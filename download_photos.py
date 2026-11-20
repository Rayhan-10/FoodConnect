"""
Download locally hosted, distinct Pexels photographs for FoodConnect demo content.

Requires a Pexels API key (PEXELS_API_KEY). The key is read only from the
environment and is never written to the project. Run manually, not at app startup:
    set PEXELS_API_KEY=your_key
    python download_photos.py

Pexels photo pages/photographers are recorded in static/images/photo_credits.json.
"""
import json
import os
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from io import BytesIO

from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static" / "images"
API_KEY = os.getenv("PEXELS_API_KEY")
API = "https://api.pexels.com/v1/search"
HEADERS = {"User-Agent": "FoodConnect-local-photo-import/1.0"}
USED_IDS = set()
CREDITS = []

def slugify(value):
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value[:80] or "photo"

def request_json(url, headers=None):
    req = Request(url, headers=headers or HEADERS)
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))

def search_photo(query, orientation):
    params = urlencode({"query": query, "per_page": 30, "orientation": orientation})
    data = request_json(API + "?" + params, {"Authorization": API_KEY, **HEADERS})
    for photo in data.get("photos", []):
        if photo["id"] not in USED_IDS:
            return photo
    return None

def save_photo(photo, destination):
    url = photo["src"].get("large2x") or photo["src"].get("large")
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=45) as response:
        raw = response.read()
    try:
        image = Image.open(BytesIO(raw))
        image.verify()
        image = Image.open(BytesIO(raw)).convert("RGB")
        if image.width < 600 or image.height < 400:
            raise ValueError("Image resolution is too small")
        image.save(destination, "JPEG", quality=88, optimize=True)
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(f"Invalid downloaded image: {exc}") from exc

def main():
    if not API_KEY:
        raise SystemExit("PEXELS_API_KEY is required. Set it in the shell; do not put it in source code.")
    # Read only literal demo data from seed_data.py; do not import it because
    # importing seed_data would execute database initialization/seeding.
    import ast
    seed_tree = ast.parse((ROOT / "seed_data.py").read_text(encoding="utf-8"))
    seed_values = {}
    wanted = {"sample_restaurants", "sample_foods_by_restaurant", "extra_foods_by_restaurant"}
    for node in seed_tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in wanted:
                    seed_values[target.id] = ast.literal_eval(node.value)
    sample_restaurants = seed_values["sample_restaurants"]
    sample_foods_by_restaurant = seed_values["sample_foods_by_restaurant"]
    extra_foods_by_restaurant = seed_values["extra_foods_by_restaurant"]

    (STATIC / "restaurants").mkdir(parents=True, exist_ok=True)
    (STATIC / "food").mkdir(parents=True, exist_ok=True)

    for restaurant in sample_restaurants:
        name = restaurant["name"]
        target = STATIC / "restaurants" / (slugify(name) + ".jpg")
        query = f'{restaurant["cuisine_type"]} restaurant interior dining room real photograph'
        photo = search_photo(query, "landscape")
        if not photo:
            print("MISSING RESTAURANT:", name)
            continue
        save_photo(photo, target)
        USED_IDS.add(photo["id"])
        CREDITS.append({"file": str(target.relative_to(ROOT / "static")).replace("\\\\", "/"),
                        "pexels_photo_id": photo["id"], "photographer": photo["photographer"],
                        "photographer_url": photo["photographer_url"], "photo_page": photo["url"],
                        "source": "Pexels", "search_query": query})
        time.sleep(0.15)

    for restaurant_name, base in sample_foods_by_restaurant.items():
        dishes = list(base) + list(extra_foods_by_restaurant.get(restaurant_name, []))
        for dish in dishes[:10]:
            name = dish[0]
            target = STATIC / "food" / (slugify(restaurant_name) + "--" + slugify(name) + ".jpg")
            query = f"{name} plated food dish professional food photography"
            photo = search_photo(query, "landscape")
            if not photo:
                print("MISSING FOOD:", restaurant_name, "—", name)
                continue
            save_photo(photo, target)
            USED_IDS.add(photo["id"])
            CREDITS.append({"file": str(target.relative_to(ROOT / "static")).replace("\\\\", "/"),
                            "pexels_photo_id": photo["id"], "photographer": photo["photographer"],
                            "photographer_url": photo["photographer_url"], "photo_page": photo["url"],
                            "source": "Pexels", "search_query": query})
            time.sleep(0.15)

    (STATIC / "photo_credits.json").write_text(json.dumps(CREDITS, indent=2), encoding="utf-8")
    print(f"Downloaded {sum(x['file'].startswith('images/restaurants/') for x in CREDITS)} restaurant photos "
          f"and {sum(x['file'].startswith('images/food/') for x in CREDITS)} food photos.")
    print("Review photo_credits.json and audit_images.py before committing.")
if __name__ == "__main__":
    main()
