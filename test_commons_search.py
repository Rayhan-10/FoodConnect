
import requests

API_URL = "https://commons.wikimedia.org/w/api.php"

FOODS = [
    "Chicken biryani",
    "Gulab jamun",
    "Vegetable gyoza",
    "Lemon soda"
]

session = requests.Session()
session.headers.update({
    "User-Agent": "FoodConnectImageResearch/1.0 (educational project)"
})

for food in FOODS:
    print("\n" + "=" * 65)
    print("SEARCHING:", food)
    print("=" * 65)

    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": food,
        "gsrnamespace": 6,
        "gsrlimit": 5,
        "prop": "imageinfo",
        "iiprop": "url|mime|extmetadata",
        "iiurlwidth": 900
    }

    try:
        response = session.get(
            API_URL,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        pages = data.get("query", {}).get("pages", {})

        if not pages:
            print("NO RESULTS FOUND")
            continue

        for page in pages.values():
            info = page.get("imageinfo", [{}])[0]
            metadata = info.get("extmetadata", {})

            license_name = metadata.get(
                "LicenseShortName", {}
            ).get("value", "Not specified")

            mime = info.get("mime", "Unknown")
            image_url = info.get("thumburl", info.get("url", ""))

            print("\nTITLE:", page.get("title"))
            print("TYPE:", mime)
            print("LICENSE:", license_name)
            print("IMAGE URL:", image_url)

    except Exception as error:
        print("SEARCH ERROR:", error)

print("\nSEARCH TEST COMPLETED")
