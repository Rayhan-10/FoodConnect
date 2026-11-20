# FoodConnect — Community Restaurant Discovery & Reviews

FoodConnect combines restaurant discovery with a community-driven review experience: users can explore local places, search by restaurant/cuisine, filter by cuisine and budget, share reviews with ratings and photos, and discuss reviews through comments and reactions.

## Project scope: Master Plan Phases 0–11

- **Phase 0 — Environment:** Python, virtual environment, Git and `.gitignore` setup instructions.
- **Phase 1 — Flask skeleton:** Flask routes, templates, static CSS/JS and local server.
- **Phase 2 — Database:** SQLite + Flask-SQLAlchemy models for users, restaurants, locations, reviews, ratings, comments, likes and media.
- **Phase 3 — Authentication:** signup, username availability check, Werkzeug scrypt password hashing, OTP verification and session login/logout. If email credentials are not configured, the OTP is printed in the terminal for local demos.
- **Phase 4 — CRUD:** restaurant suggestion form, restaurant details, review creation, star ratings and optional review photo upload.
- **Phase 5 — Social layer:** AJAX comments and like/dislike reactions plus Flask-SocketIO room broadcasting. Open the same restaurant page in two browser sessions to see new comments and reaction counts update without a page reload. The Socket.IO browser client is loaded from a CDN, so cross-browser live updates need internet access; AJAX actions still work if the socket client cannot load.
- **Phase 6 — Discovery:** search by restaurant name or cuisine, cuisine/budget filters and six-card pagination.
- **Phase 7 — Media/maps/date:** review visit-date picker, optional YouTube embed on restaurant details, and OpenStreetMap embed when latitude/longitude is available.
- **Phase 8 — Sentiment analysis:** review sentiment labels (`positive`, `neutral`, `negative`). A small explainable lexical fallback works without ML packages. An optional TensorFlow training script can create a starter `.tflite` model and vocabulary file; this tiny starter corpus is educational and must not be represented as a production-quality classifier.
- **Phase 9 — Frontend polish:** responsive editorial design, accessible focus states, reduced-motion support, Sass source tokens and progressive GSAP entrance animation. The app remains usable if the animation CDN is unavailable.
- **Phase 10 — APIs:** JSON REST endpoints for restaurant/review data and an Ariadne GraphQL endpoint at `/graphql`.
- **Phase 11 — Admin reporting:** verified account matching `ADMIN_EMAIL` can view `/admin/reports` and export a PDF report.

## Run on Windows

1. Extract this ZIP into a clean folder such as `C:\FoodConnect_Final`. If you have an older `foodconnect.db`, keep a separate backup before replacing it. The ZIP intentionally does not include account records from the development database.
2. Open the extracted folder in VS Code.
3. In the terminal run:

   ```bat
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Optional email OTP: copy `.env.example` to `.env`, then set `EMAIL_ADDRESS`, `EMAIL_APP_PASSWORD`, and a unique `SECRET_KEY`. Never upload `.env` to GitHub.
5. Create the local database and seed sample restaurants (the script only adds missing names; it does not delete user data):

   ```bat
   python seed_data.py
   ```

6. Start the app:

   ```bat
   python app.py
   ```

7. Open `http://127.0.0.1:5000`.


## API quick tests

- `GET /api/restaurants` — list restaurants (`?q=`, `?cuisine=`, `?page=`, `?per_page=` supported).
- `GET /api/restaurants/1` — restaurant detail; `POST /api/restaurants` creates a restaurant for a signed-in user; `PUT/PATCH/DELETE /api/restaurants/1` are admin-only.
- `GET /api/reviews` — review feed (`?restaurant_id=` and `?page=` supported).
- `POST /api/reviews` — create a review while signed in; JSON body: `{"restaurant_id": 1, "content": "Great food!", "visited_on": "2026-11-19", "stars": 5}`.
- `GET /api/reviews/1` — review detail; `PUT/PATCH/DELETE /api/reviews/1` are available to the review owner (or configured admin).
- `POST /graphql` — GraphQL JSON body, e.g. `{"query":"{ restaurants { id name average_rating } }"}`.

## Admin report setup

Set `ADMIN_EMAIL` in `.env` to the email address of an account that has completed OTP verification. Sign in with that account, then open `/admin/reports`. The report is based on available restaurant ratings; PDF export is available from the page. Do not commit `.env`.

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
- Restaurant and food artwork is stored locally under `static/images/`, so the core image cards do not depend on Unsplash. Uploaded review/menu/restaurant photos are served from the configured upload folder. Google Fonts, OpenStreetMap, YouTube and the Socket.IO browser client may still use external network access.
- Maps use OpenStreetMap and need coordinates to display. Sample coordinates are demo coordinates for Chattogram.
- GSAP is a progressive enhancement loaded from a CDN. The page does not depend on it for core behavior.
- SQLite database is created locally on first run; `seed_data.py` creates the sample restaurants and food menu. If migrating an older database, back it up first because the startup helper adds newer columns without deleting existing data.
- This is an academic demo. Production deployment uses `wsgi.py`, Gunicorn, PostgreSQL and a persistent upload disk when deployed through the supplied Render Blueprint. Review the deployment guide and configure the generated secret key and admin email before public launch.

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


### Migrate older demo image references
After extracting this update, run `python seed_data.py` once while your virtual environment is active. The script safely changes existing demo food/restaurant records that still contain external image URLs to local SVG assets. It does not delete user data.

## Final submission

Use `FINAL_SUBMISSION_CHECKLIST.md` for a last local test run and a short presentation flow.


## Production deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) and the included `render.yaml`. The deployment blueprint provisions a PostgreSQL database and persistent disk; these Render resources may incur charges. A successful build is not the same as a verified live deployment.

## Local image assets

The project includes original locally stored SVG illustrations for restaurant categories and common food/menu categories. If a user-uploaded image is missing or an older database record points to an external image URL, the page falls back to a local category illustration instead of showing a broken-image placeholder.


## Optional Sass build

The full stylesheet source is in `static/scss/style.scss` (plain CSS syntax is valid SCSS). If Node.js is installed, run:

```bash
npm install
npm run build:css
```

The generated stylesheet is `static/css/style.css`. Runtime does not require Node.js because the compiled CSS is already included.
