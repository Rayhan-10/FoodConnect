
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO

API_URL = "https://commons.wikimedia.org/w/api.php"

HEADERS = {
    "User-Agent": "FoodConnectEducationalProject/1.0 (image research)"
}

preview_dir = Path("static/images/preview")
preview_dir.mkdir(parents=True, exist_ok=True)

foods = [
    "Chicken biryani",
    "Gulab jamun",
    "Vegetable gyoza",
    "Lemonade"
]

for food in foods:
    print("\nSearching:", food)

    try:
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": food + " filetype:bitmap",
            "gsrnamespace": 6,
            "gsrlimit": 5,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "iiurlwidth": 640
        }

        response = requests.get(
            API_URL,
            params=params,
            headers=HEADERS,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()
        pages = data.get("query", {}).get("pages", {})

        if not pages:
            print("NO RESULTS FOUND")
            continue

        page = next(iter(pages.values()))
        info = page["imageinfo"][0]

        image_url = info.get("thumburl") or info.get("url")
        metadata = info.get("extmetadata", {})

        image_response = requests.get(
            image_url,
            headers=HEADERS,
            timeout=30
        )
        image_response.raise_for_status()

        image = Image.open(
            BytesIO(image_response.content)
        ).convert("RGB")

        filename = food.lower().replace(" ", "_") + ".jpg"
        output = preview_dir / filename
        image.save(output, "JPEG", quality=90)

        print("TITLE:", page["title"])
        print("LICENSE:", metadata.get("LicenseShortName", {}).get("value", "Unknown"))
        print("SAVED:", output)
        print("SIZE:", image.size)

    except Exception as error:
        print("FAILED:", error)

print("\nPreview process finished.")
