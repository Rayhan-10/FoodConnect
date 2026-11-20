# FoodConnect image reliability update

## What changed
- Restaurant covers and menu images now use original local SVG artwork stored under `static/images/restaurants/` and `static/images/food/`.
- Homepage, Explore Restaurants and Restaurant Details no longer depend on Unsplash image URLs.
- Old database rows containing external image URLs resolve to a local cuisine/dish illustration.
- Review, restaurant and food uploads are validated as actual images and saved to the configured upload folder.
- Uploaded images are served through `/uploads/<filename>`. On Render, set `UPLOAD_FOLDER=/var/data/uploads` and attach the persistent disk described in `render.yaml`.
- A local placeholder remains available for genuinely missing images.

## Apply safely on Windows
1. Stop the Flask server with `Ctrl+C`.
2. Back up `instance/foodconnect.db` and your current project folder.
3. Extract the complete updated ZIP to a new folder.
4. Keep your `.env` private. Run `pip install -r requirements.txt`.
5. Run `python seed_data.py` to create missing demo data and migrate old external demo image references to local SVG assets.
6. Start with `python app.py` and inspect the homepage, Explore page and restaurant detail pages.

## Important note
The bundled illustrations are locally stored SVG artwork, not restaurant-verified photographs. Users can upload their own actual JPG, PNG, WEBP or GIF photos. Sample restaurant/menu names, locations and prices are illustrative demo data.
