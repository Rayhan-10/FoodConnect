# FoodConnect image reliability update

## What changed
- Newly uploaded food photos are saved inside `static/uploads/foods/`.
- Food menu cards now fall back to `static/images/food-placeholder.svg` if an image is missing or an external image URL fails.
- Existing database image paths such as `images/food_uploads/...` and external `https://...` URLs remain supported. Existing records are not deleted or rewritten.

## Apply safely on Windows
1. Stop the Flask server with `Ctrl+C`.
2. Back up `instance/foodconnect.db` and your current project folder.
3. Extract this ZIP to a separate folder first and copy the changed `app.py`, `templates/restaurant_detail.html`, `static/images/food-placeholder.svg`, and this README into your working project. Keep your existing `.env` and database.
4. New uploads will be stored in `static/uploads/foods/`. The folder is created automatically when the first photo is uploaded.
5. Start with `python app.py`, open a restaurant detail page, and check a broken image. It should show the local fallback illustration.

## Important note
Sample menu photos defined by `seed_data.py` are still external demo URLs; this update does not download or convert those images into local files. If one of those URLs fails, the local placeholder prevents a broken-image icon. Photos uploaded through the FoodConnect menu form are stored locally.
