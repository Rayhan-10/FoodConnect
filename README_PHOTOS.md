# FoodConnect – real photographs (replaces the cartoon/SVG images)

All 12 restaurants and 120 dishes use **local JPEG files** in `static/images/` – nothing is loaded from
the internet at runtime, and no API key is needed.

| What | Location | File name rule |
|---|---|---|
| Restaurant interior | `static/images/restaurants/` | `<restaurant-slug>.jpg`  e.g. `spice-garden.jpg` |
| Dish | `static/images/food/` | `<restaurant-slug>--<dish-slug>.jpg`  e.g. `spice-garden--chicken-biryani.jpg` |
| Neutral fallback (only if a photo is missing) | `static/images/fallback/photo-unavailable.jpg` | plain dark image, not an illustration |

File names come from `image_paths.py`; the web app, `seed_data.py` and the tools all use it.

## Collecting the photographs (run on your own computer)
```
python tools/fetch_photos.py          # fills every missing photo
python tools/audit_images.py --contact-sheet   # then open audit/contact_sheet.html and LOOK at every photo
```
Order of sources for each file: (1) your own download in `manual_photos/` (same file name, any of jpg/png/webp);
(2) a direct image URL you put in `tools/photo_sources.csv`; (3) Wikimedia Commons (official API, only CC0 /
public-domain / CC BY / CC BY-SA photos). Everything is converted to a real JPEG (max 1400 px wide).
Author, licence and source link of each photo are written to `IMAGE_SOURCES.csv` (keep it – CC BY needs attribution).
Photos that cannot be found are listed by exact file name – they are never replaced by an unrelated picture.
To replace a wrong-looking photo: save the right one in `manual_photos/` with the same file name, run the fetch script again.

## What the audit checks
`tools/audit_images.py [--db]` – file exists, not empty, really a JPEG, at least 600x400, no duplicate files,
no `.svg` left in `static/images`, and (with `--db`) every database reference resolves to a real photo.
Exit code 0 only when all 132 are valid.

## Database / seed behaviour
`seed_data.py` is safe to run repeatedly (Render runs it before every deploy). It only replaces *legacy* image
values (empty, external URL, `.svg`). Paths of photos and user uploads (`uploads/...`) are never overwritten; reviews,
ratings, comments and users are untouched. The web app also derives the photo from restaurant/dish name, so rows that
still hold an old SVG path show the correct photo immediately.

## Tests
`python tests/test_app.py` – 46 checks: seed twice, legacy-row repair, home/list/search/detail pages, image serving,
signup + OTP + login/logout, review with photo upload, comment, like, add restaurant with cover, menu item upload,
non-image upload rejection.
