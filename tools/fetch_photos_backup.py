"""Collects real photographs for FoodConnect into static/images/ (run on YOUR computer).

Usage:   python tools/fetch_photos.py            (fill everything that is still missing)
         python tools/fetch_photos.py --force    (re-download everything, except manual photos)

For every expected photo (see tools/catalog.py) it tries, in order:
  1. manual_photos/<file-name-without-extension>.(jpg|jpeg|png|webp)   <- your own downloads always win
  2. a direct image URL you put in tools/photo_sources.csv (column "url"), e.g. an Unsplash/Pexels image
     link you downloaded-from-site yourself (respect each site's licence)
  3. Wikimedia Commons (official keyless API; only CC0 / public-domain / CC BY / CC BY-SA photos)

Everything is converted to a genuine JPEG (max 1400 px wide) and saved as static/images/<rel path>.
Author + licence + source URL are written to IMAGE_SOURCES.csv.  Nothing is AI-generated, nothing is
fetched at runtime by the website.  Items that cannot be found are listed at the end - never replaced
by an unrelated picture.
"""
import csv
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from catalog import ROOT, load_catalog, abs_path  # noqa: E402
from PIL import Image  # noqa: E402

UA = 'FoodConnectUniversityProject/1.0 (student project; contact via GitHub Rayhan-10/FoodConnect)'
MANUAL_DIR = os.path.join(ROOT, 'manual_photos')
SOURCES_CSV = os.path.join(ROOT, 'tools', 'photo_sources.csv')
MANIFEST = os.path.join(ROOT, 'IMAGE_SOURCES.csv')
OK_LICENSES = ('cc0', 'public domain', 'pd', 'cc by', 'cc-by', 'attribution')
BAD_WORDS = ('map', 'logo', 'flag', 'diagram', 'icon', 'poster', 'menu', 'recipe', 'drawing', 'painting',
             'illustration', 'vector', 'svg', 'cover', 'stamp', 'sign', 'package', 'packet', 'label')

RESTAURANT_QUERIES = {
    'Indian': ['Indian restaurant interior', 'restaurant interior dining room'],
    'Japanese': ['Japanese restaurant interior', 'sushi restaurant interior'],
    'Fast Food': ['fast food restaurant interior', 'burger restaurant interior'],
    'Italian': ['Italian restaurant interior', 'trattoria interior'],
    'Bangladeshi': ['Bangladeshi restaurant interior', 'restaurant Dhaka interior', 'restaurant interior dining room'],
    'Cafe': ['cafe interior', 'coffee shop interior'],
    'Chinese': ['Chinese restaurant interior', 'restaurant interior dining room'],
    'Mexican': ['Mexican restaurant interior', 'restaurant interior dining room'],
    'Korean': ['Korean restaurant interior', 'restaurant interior dining room'],
    'Seafood': ['seafood restaurant interior', 'restaurant terrace sea'],
}
FOOD_QUERY_FIX = {  # clearer search words for dishes whose menu names are vague
    'Salmon Sushi Roll': 'salmon maki sushi', 'Chicken Teriyaki Bowl': 'chicken teriyaki rice',
    'Classic Beef Burger': 'hamburger beef', 'Crispy Chicken Burger': 'fried chicken sandwich',
    'Creamy Alfredo Pasta': 'fettuccine alfredo', 'Mezban Beef with Rice': 'beef curry with rice',
    'Kala Bhuna': 'kala bhuna beef', 'Chattogram Beef Bhuna': 'beef bhuna', 'Beef Mezban': 'Chittagong mezban beef',
    'Dal Bhorta': 'dal bhorta', 'Aloo Bhorta': 'aloo bharta', 'Beef Chap': 'chaap beef',
    'Borhani': 'borhani drink', 'Lassi': 'lassi drink', 'Lemon Soda': 'lemon soda drink',
    'Mango Smoothie': 'mango smoothie', 'Mexican Rice Bowl': 'mexican rice bowl', 'Egg Korma': 'egg curry',
    'Jali Kebab': 'seekh kebab', 'Firni': 'phirni dessert', 'Morog Polao': 'chicken pulao',
    'Beef Khichuri': 'khichuri', 'Chicken Roast': 'bengali roast chicken', 'Chicken Roast ': 'roast chicken',
    'Kimchi Pancake': 'kimchijeon', 'Korean Corn Dogs': 'Korean corn dog', 'Hotteok': 'hotteok',
    'Caramel Macchiato': 'caramel macchiato', 'Waffles with Honey': 'waffles honey',
    'Club Sandwich': 'club sandwich', 'Chicken Panini': 'panini', 'Vanilla Frappe': 'iced coffee frappe',
    'Seafood Chowder': 'seafood chowder', 'Grilled Fish': 'grilled fish', 'Prawn Masala': 'prawn masala curry',
    'Steamed Dumplings': 'steamed dumplings jiaozi', 'Hot and Sour Soup': 'hot and sour soup',
    'Chilli Garlic Noodles': 'garlic noodles', 'Sweet and Sour Chicken': 'sweet and sour chicken',
    'Beef with Broccoli': 'beef and broccoli', 'Mango Pudding': 'mango pudding',
}


def http_get(url, timeout=40):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def save_jpeg(raw, dest):
    with Image.open(io.BytesIO(raw)) as im:
        im = im.convert('RGB')
        if im.width > 1400:
            im = im.resize((1400, round(im.height * 1400 / im.width)), Image.LANCZOS)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        im.save(dest, 'JPEG', quality=85, optimize=True)
        return im.size


def strip_html(text):
    return re.sub(r'<[^>]+>', '', text or '').strip()


def pick_commons(api_json, used_urls):
    """Choose the best usable photo from a Commons API response (pure function, unit-testable)."""
    pages = (api_json.get('query') or {}).get('pages') or {}
    ranked = sorted(pages.values(), key=lambda p: p.get('index', 999))
    for page in ranked:
        info = (page.get('imageinfo') or [None])[0]
        if not info:
            continue
        title = (page.get('title') or '').lower()
        if info.get('mime') != 'image/jpeg' or any(w in title for w in BAD_WORDS):
            continue
        if info.get('width', 0) < 900 or info.get('height', 0) < 600:
            continue
        meta = info.get('extmetadata') or {}
        lic = strip_html((meta.get('LicenseShortName') or {}).get('value', '')).lower()
        if not any(ok in lic for ok in OK_LICENSES) or re.search(r'(^|[ -])(nc|nd)([ -]|$)', lic):
            continue
        url = info.get('thumburl') or info.get('url')
        if url in used_urls:
            continue
        return {'url': url, 'page': info.get('descriptionurl', ''), 'license': lic.upper(),
                'author': strip_html((meta.get('Artist') or {}).get('value', ''))[:120], 'title': page.get('title', '')}
    return None


def commons_search(query, used_urls):
    params = {'action': 'query', 'format': 'json', 'generator': 'search', 'gsrnamespace': '6',
              'gsrsearch': f'{query} filetype:bitmap', 'gsrlimit': '25', 'prop': 'imageinfo',
              'iiprop': 'url|size|mime|extmetadata', 'iiurlwidth': '1400'}
    data = json.loads(http_get('https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(params)))
    return pick_commons(data, used_urls)


def queries_for(item):
    if item['kind'] == 'restaurant':
        return RESTAURANT_QUERIES.get(item['cuisine'], ['restaurant interior dining room'])
    base = FOOD_QUERY_FIX.get(item['name'], item['name'])
    return [base + ' dish', base]


def load_sources_csv():
    out = {}
    if os.path.isfile(SOURCES_CSV):
        with open(SOURCES_CSV, newline='', encoding='utf-8') as fh:
            for row in csv.DictReader(fh):
                if (row.get('url') or '').strip():
                    out[row['file']] = row
    return out


def find_manual(rel):
    stem = os.path.splitext(os.path.basename(rel))[0]
    for ext in ('jpg', 'jpeg', 'png', 'webp', 'JPG', 'JPEG', 'PNG', 'WEBP'):
        path = os.path.join(MANUAL_DIR, f'{stem}.{ext}')
        if os.path.isfile(path):
            return path
    return None


def main():
    force = '--force' in sys.argv
    items = load_catalog()
    manual_csv = load_sources_csv()
    manifest = {}
    if os.path.isfile(MANIFEST):
        with open(MANIFEST, newline='', encoding='utf-8') as fh:
            manifest = {r['file']: r for r in csv.DictReader(fh)}
    used = {r['source_url'] for r in manifest.values()}
    failed = []
    for n, it in enumerate(items, 1):
        dest = abs_path(it)
        name = os.path.basename(it['rel'])
        manual = find_manual(it['rel'])
        if manual:
            save_jpeg(open(manual, 'rb').read(), dest)
            manifest[name] = {'file': name, 'item': it['name'], 'restaurant': it['restaurant'], 'source': 'manual download by project owner',
                              'source_url': 'manual_photos/' + os.path.basename(manual), 'license': 'see original site (Unsplash/Pexels licence)', 'author': ''}
            print(f'[{n:3}/{len(items)}] manual     {name}')
            continue
        if os.path.isfile(dest) and not force:
            print(f'[{n:3}/{len(items)}] already ok {name}')
            continue
        done = False
        try:
            if name in manual_csv:
                row = manual_csv[name]
                save_jpeg(http_get(row['url'].strip()), dest)
                manifest[name] = {'file': name, 'item': it['name'], 'restaurant': it['restaurant'], 'source': row.get('source') or 'direct url',
                                  'source_url': row['url'].strip(), 'license': row.get('license', ''), 'author': row.get('author', '')}
                done = True
            else:
                for q in queries_for(it):
                    hit = commons_search(q, used)
                    time.sleep(1.0)  # be polite to the free API
                    if hit:
                        save_jpeg(http_get(hit['url']), dest)
                        used.add(hit['url'])
                        manifest[name] = {'file': name, 'item': it['name'], 'restaurant': it['restaurant'], 'source': 'Wikimedia Commons: ' + hit['title'],
                                          'source_url': hit['url'], 'license': hit['license'], 'author': hit['author']}
                        done = True
                        break
        except Exception as exc:  # noqa: BLE001
            print(f'   ! error for {name}: {exc}')
        print(f'[{n:3}/{len(items)}] {"downloaded" if done else "NOT FOUND"} {name}')
        if not done:
            failed.append(it)
    with open(MANIFEST, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=['file', 'item', 'restaurant', 'source', 'source_url', 'license', 'author'])
        w.writeheader()
        for k in sorted(manifest):
            w.writerow(manifest[k])
    print('\nSource manifest written to IMAGE_SOURCES.csv')
    if failed:
        print(f'\n{len(failed)} photo(s) could NOT be found automatically. Download a suitable photo yourself and save it in')
        print('manual_photos/ using EXACTLY these file names (any of jpg/png/webp), then run this script again:')
        for it in failed:
            print('  ', os.path.splitext(os.path.basename(it['rel']))[0], '   <-', it['kind'], it['name'])
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
