
import requests
from app import app
from models import FoodItem

with app.app_context():
    items = FoodItem.query.order_by(FoodItem.id).all()

    url_items = {}

    for item in items:
        url = (item.image_path or "").strip()

        if url.startswith("http"):
            url_items.setdefault(url, []).append(item.name)

    print("CHECKING FOOD IMAGE URLS")
    print("=" * 65)

    working = 0
    failed = 0

    for index, (url, food_names) in enumerate(url_items.items(), 1):
        try:
            response = requests.get(url, timeout=15, stream=True)

            content_type = response.headers.get("Content-Type", "")

            if response.status_code == 200 and "image/" in content_type:
                print(f"\n[OK] {index}/{len(url_items)}")
                working += 1
            else:
                print(f"\n[FAILED] {index}/{len(url_items)}")
                failed += 1

            print("USED BY:", ", ".join(food_names))
            print("STATUS:", response.status_code)
            print("URL:", url)

            response.close()

        except requests.RequestException as error:
            print(f"\n[ERROR] {index}/{len(url_items)}")
            print("USED BY:", ", ".join(food_names))
            print("DETAIL:", error)
            failed += 1

    print("\n" + "=" * 65)
    print("WORKING URLS:", working)
    print("FAILED URLS:", failed)
