# FoodConnect — Community Restaurant Discovery & Reviews

FoodConnect combines restaurant discovery with a community-driven review experience: users can explore local places, search by restaurant/cuisine, filter by cuisine and budget, share reviews with ratings and photos, and discuss reviews through comments and reactions.

## Project scope: Master Plan Phases 0–9

- **Phase 0 — Environment:** Python, virtual environment, Git and `.gitignore` setup instructions.
- **Phase 1 — Flask skeleton:** Flask routes, templates, static CSS/JS and local server.
- **Phase 2 — Database:** SQLite + Flask-SQLAlchemy models for users, restaurants, locations, reviews, ratings, comments, likes and media.
- **Phase 3 — Authentication:** signup, username availability check, bcrypt password hashing, OTP verification and session login/logout. If email credentials are not configured, the OTP is printed in the terminal for local demos.
- **Phase 4 — CRUD:** restaurant suggestion form, restaurant details, review creation, star ratings and optional review photo upload.
- **Phase 5 — Social layer:** AJAX comments and like/dislike reactions plus Flask-SocketIO room broadcasting. Open the same restaurant page in two browser sessions to see new comments and reaction counts update without a page reload. The Socket.IO browser client is loaded from a CDN, so cross-browser live updates need internet access; AJAX actions still work if the socket client cannot load.
- **Phase 6 — Discovery:** search by restaurant name or cuisine, cuisine/budget filters and six-card pagination.
- **Phase 7 — Media/maps/date:** review visit-date picker, optional YouTube embed on restaurant details, and OpenStreetMap embed when latitude/longitude is available.
- **Phase 8 — Sentiment analysis:** review sentiment labels (`positive`, `neutral`, `negative`). A small explainable lexical fallback works without ML packages. An optional TensorFlow training script can create a starter `.tflite` model and vocabulary file; this tiny starter corpus is educational and must not be represented as a production-quality classifier.
- **Phase 9 — Frontend polish:** responsive editorial design, accessible focus states, reduced-motion support, Sass source tokens and progressive GSAP entrance animation. The app remains usable if the animation CDN is unavailable.

## Run on Windows

1. Extract this ZIP into a clean folder such as `C:\FoodConnect_Final`. Keep a backup of your previous folder and database.
2. Open the extracted folder in VS Code.
3. In the terminal run:

   ```bat
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Optional email OTP: copy `.env.example` to `.env`, then set `EMAIL_ADDRESS`, `EMAIL_APP_PASSWORD`, and a unique `SECRET_KEY`. Never upload `.env` to GitHub.
5. Seed sample restaurants (the script only adds missing names; it does not delete user data):

   ```bat
   python seed_data.py
   ```

6. Start the app:

   ```bat
   python app.py
   ```

7. Open `http://127.0.0.1:5000`.

## Phase 8 optional TensorFlow Lite model

The project uses a lexical fallback unless both `models/sentiment.tflite` and `models/sentiment_vocab.json` exist. To train and export a tiny educational TFLite classifier, install TensorFlow in a compatible Python environment and run:

```bat
python -m pip install tensorflow
python train_sentiment_model.py
```

This creates `models/sentiment.tflite` and `models/sentiment_vocab.json`. For TFLite inference, install a compatible `tflite-runtime` build or TensorFlow in the app environment. If those optional packages/model files are missing, the app automatically uses the lexical fallback. The starter model uses a tiny illustrative English dataset, so its predictions are only a demonstration.

## Notes and known limits

- A compatible TensorFlow installation is not bundled because it is large and Python-version/platform-specific. The trainer is included, but the `.tflite` artifact must be generated in a compatible environment; until then, the transparent lexical fallback is used. The included training corpus is intentionally tiny and for demonstration only.

- Restaurant names/addresses and budget bands are demo data. Price bands are approximate and not verified menu prices.
- Images and web fonts use Unsplash/Google Fonts and need internet access; the core routes and text still work if they are unavailable.
- Maps use OpenStreetMap and need coordinates to display. Sample coordinates are demo coordinates for Chattogram.
- GSAP is a progressive enhancement loaded from a CDN. The page does not depend on it for core behavior.
- The existing SQLite schema is upgraded at app startup for the added `sentiment_label` and `video_url` columns. Back up `foodconnect.db` before replacing project files.
- This is a local academic demo. Before public deployment, set a strong secret key, configure CSRF protection/rate limits, review upload security, and use a production WSGI server.

## Quick demo path

1. Homepage search and featured places.
2. Explore page: search, cuisine/budget filters and pagination.
3. Open a restaurant, inspect budget/location/rating and map/video if configured.
4. Sign up; read the terminal for OTP if email is not configured; verify and log in.
5. Post a review with a star rating, visit date and optional photo.
6. Show sentiment tag, then add a comment and like/dislike a review.
7. Suggest a new restaurant while logged in.

Do not present a feature as fully working until you have tested it locally with your current database and browser.

## Food menu feature (new)

- Each restaurant detail page now includes a food menu with dish photos, BDT prices, descriptions and categories.
- Visitors can search dish names and filter by category.
- Logged-in users can suggest a menu item with an image URL or upload a PNG/JPG/JPEG/GIF/WEBP photo (up to 5 MB).
- `FoodItem` is stored in its own SQLite table. `db.create_all()` creates the new table without deleting existing users, reviews or restaurants.
- `seed_data.py` adds illustrative sample dishes only for sample restaurants that do not already have menu items. These prices and photos are demo content, not verified official restaurant menus.

To create the table and add sample menu items in your existing project, activate the virtual environment, install dependencies if needed, then run `python seed_data.py`. Restart `python app.py` and open a restaurant detail page.


### Repair demo image references
After merging this update into your existing project, run `python seed_data.py` once while your virtual environment is active. The script updates image URLs for the existing demo Spring Rolls, Steamed Dumplings, and Golden Dragon records without deleting the database. These use external Unsplash URLs and therefore require internet access in the browser.
