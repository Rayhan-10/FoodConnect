# FoodConnect — Community Discovery Redesign

This version redesigns the presentation around FoodConnect's core idea: restaurant discovery plus community reviews and conversation.

## Included in this build
- Warm, responsive editorial homepage with restaurant search, cuisine shortcuts, platform counts, featured places, and a community review feed.
- Restaurant discovery page with search, cuisine and budget filters, six cards per page, and pagination.
- Restaurant profile pages with review submission, star selection, optional photo upload, visit date, comments, likes/dislikes, budget/location summary, and an OpenStreetMap embed when coordinates exist.
- Logged-in users can suggest restaurants through the existing submission form.
- Existing Flask/SQLite backend and authentication routes are retained.

## Run on Windows
1. Extract this folder into your project location (keep a backup of your current folder and `foodconnect.db`).
2. Activate your virtual environment: `venv\Scripts\activate`
3. Install dependencies if needed: `pip install -r requirements.txt`
4. Seed any missing sample restaurants: `python seed_data.py`
5. Start the app: `python app.py`
6. Open `http://127.0.0.1:5000`.

## Notes
- Restaurant and food cards use local SVG artwork. Google Fonts and optional embeds still use external network access.
- The map uses OpenStreetMap and appears only when location coordinates exist. No API key is required for the embedded map.
- Prices shown are broad illustrative budget bands, not verified menu prices.
- This package's Python syntax and Jinja template parsing were checked. Full Flask/browser integration testing could not be run in the build environment because Flask dependencies were not installed there; please test on your PC before presenting.
- This is a local academic demo, not production deployment.
