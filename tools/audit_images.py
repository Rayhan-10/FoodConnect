"""Image audit for FoodConnect.  Run:  python tools/audit_images.py [--db] [--contact-sheet]

Checks every expected photograph (12 restaurants + 120 dishes):
exists, non-empty, genuinely a JPEG that opens, big enough, not a duplicate of another item,
and that no SVG illustration is left under static/images.  With --db it also checks that every
Restaurant.cover_image / FoodItem.image_path in the configured database resolves to a real file.
Exit code 0 only if everything is OK.
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from catalog import ROOT, load_catalog, abs_path  # noqa: E402
from PIL import Image  # noqa: E402

MIN_W, MIN_H = 600, 400


def audit():
    items = load_catalog()
    report = {'expected_restaurants': 0, 'expected_foods': 0, 'valid_restaurants': 0, 'valid_foods': 0,
              'missing': [], 'empty': [], 'corrupt': [], 'wrong_format': [], 'too_small': [],
              'duplicates': [], 'svg_files': [], 'extension_mismatch': []}
    hashes = {}
    for it in items:
        report['expected_restaurants' if it['kind'] == 'restaurant' else 'expected_foods'] += 1
        path = abs_path(it)
        label = f"{it['kind']}: {it['restaurant']} / {it['name']}  ({it['rel']})"
        if not os.path.isfile(path):
            report['missing'].append(label)
            continue
        if os.path.getsize(path) == 0:
            report['empty'].append(label)
            continue
        try:
            with Image.open(path) as im:
                fmt, (w, h) = im.format, im.size
                im.verify()
        except Exception as exc:  # noqa: BLE001
            report['corrupt'].append(f'{label}: {exc}')
            continue
        if fmt != 'JPEG':
            report['wrong_format'].append(f'{label}: actually {fmt}')
            continue
        if w < MIN_W or h < MIN_H:
            report['too_small'].append(f'{label}: {w}x{h}')
            continue
        digest = hashlib.sha256(open(path, 'rb').read()).hexdigest()
        if digest in hashes:
            report['duplicates'].append(f"{label} == {hashes[digest]}")
        else:
            hashes[digest] = it['rel']
        report['valid_restaurants' if it['kind'] == 'restaurant' else 'valid_foods'] += 1
    for base, _dirs, files in os.walk(os.path.join(ROOT, 'static', 'images')):
        for name in files:
            if name.lower().endswith('.svg'):
                report['svg_files'].append(os.path.relpath(os.path.join(base, name), ROOT))
    return report


def audit_db():
    sys.path.insert(0, ROOT)
    from app import app, restaurant_image, food_image  # noqa: WPS433
    from models import Restaurant, FoodItem
    out = {'restaurants_in_db': 0, 'foods_in_db': 0, 'fallback_restaurants': [], 'fallback_foods': [], 'svg_or_http_refs': []}
    with app.app_context(), app.test_request_context():
        for r in Restaurant.query.all():
            out['restaurants_in_db'] += 1
            if 'photo-unavailable' in restaurant_image(r):
                out['fallback_restaurants'].append(r.name)
            if (r.cover_image or '').lower().endswith('.svg') or (r.cover_image or '').startswith('http'):
                out['svg_or_http_refs'].append(f'restaurant {r.name}: {r.cover_image}')
        for f in FoodItem.query.all():
            out['foods_in_db'] += 1
            if 'photo-unavailable' in food_image(f):
                out['fallback_foods'].append(f'{f.restaurant.name} / {f.name}')
            if (f.image_path or '').lower().endswith('.svg') or (f.image_path or '').startswith('http'):
                out['svg_or_http_refs'].append(f'food {f.name}: {f.image_path}')
    return out


def contact_sheet():
    items = load_catalog()
    rows = []
    for it in items:
        ok = os.path.isfile(abs_path(it))
        img = f'../static/{it["rel"]}' if ok else ''
        body = f'<img src="{img}" loading="lazy">' if ok else '<div class="miss">MISSING</div>'
        rows.append(f'<figure>{body}<figcaption><b>{it["name"]}</b><br>{it["kind"]} - {it["restaurant"]}<br><code>{it["rel"].split("/")[-1]}</code></figcaption></figure>')
    html = ('<!doctype html><meta charset="utf-8"><title>FoodConnect photo check</title>'
            '<style>body{background:#161616;color:#eee;font:14px sans-serif;margin:16px}'
            'main{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}'
            'figure{margin:0;background:#222;border-radius:8px;overflow:hidden}img,.miss{width:100%;height:160px;object-fit:cover;display:block}'
            '.miss{background:#5a1d1d;display:flex;align-items:center;justify-content:center}figcaption{padding:8px;font-size:12px}</style>'
            '<h2>Check every photo matches its label. Wrong one? Put the right image in manual_photos/ with the file name shown, then run tools/fetch_photos.py</h2><main>'
            + ''.join(rows) + '</main>')
    os.makedirs(os.path.join(ROOT, 'audit'), exist_ok=True)
    path = os.path.join(ROOT, 'audit', 'contact_sheet.html')
    open(path, 'w', encoding='utf-8').write(html)
    return path


def main():
    rep = audit()
    problems = sum(len(rep[k]) for k in ('missing', 'empty', 'corrupt', 'wrong_format', 'too_small', 'duplicates', 'svg_files'))
    db_rep = None
    if '--db' in sys.argv:
        db_rep = audit_db()
        problems += len(db_rep['svg_or_http_refs'])
    print('FOODCONNECT IMAGE AUDIT')
    print(f"  restaurants expected {rep['expected_restaurants']:>3} | valid photos {rep['valid_restaurants']:>3}")
    print(f"  food items  expected {rep['expected_foods']:>3} | valid photos {rep['valid_foods']:>3}")
    print(f"  total valid photographs: {rep['valid_restaurants'] + rep['valid_foods']} / {rep['expected_restaurants'] + rep['expected_foods']}")
    for key in ('missing', 'empty', 'corrupt', 'wrong_format', 'too_small', 'duplicates', 'svg_files'):
        print(f'  {key}: {len(rep[key])}')
        for line in rep[key]:
            print('     -', line)
    if db_rep:
        print(f"  DB: {db_rep['restaurants_in_db']} restaurants, {db_rep['foods_in_db']} food items; "
              f"showing fallback: {len(db_rep['fallback_restaurants'])} restaurants, {len(db_rep['fallback_foods'])} foods; "
              f"svg/http refs: {len(db_rep['svg_or_http_refs'])}")
        for line in db_rep['svg_or_http_refs']:
            print('     -', line)
    if '--contact-sheet' in sys.argv:
        print('  contact sheet:', contact_sheet())
    with open(os.path.join(ROOT, 'audit_report.json'), 'w', encoding='utf-8') as fh:
        json.dump({'files': rep, 'db': db_rep}, fh, indent=2)
    print('RESULT:', 'OK' if problems == 0 else f'{problems} PROBLEM(S) FOUND')
    return 0 if problems == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
