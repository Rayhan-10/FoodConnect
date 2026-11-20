# FoodConnect — UI refresh

This update refreshes the existing Flask project with a dark charcoal + orange visual theme while keeping the existing Flask routes, templates, models, and database flow in place.

## Run locally (Windows / VS Code)

1. Open the `foodconnect_project` folder in VS Code.
2. Activate your existing virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
3. Install project packages if needed:
   ```powershell
   pip install -r requirements.txt
   ```
4. Add sample restaurants (safe to run more than once; existing restaurant names are skipped):
   ```powershell
   python seed_data.py
   ```
5. Start the site:
   ```powershell
   python app.py
   ```
6. Open `http://127.0.0.1:5000`.

## UI changes

- Rebuilt the homepage into a dark editorial-style landing page.
- Restyled restaurant listing, search/filter controls, cards, pagination, and empty state.
- Applied a consistent charcoal/orange theme to restaurant details, reviews, auth forms, and dashboard.
- Added responsive layouts for narrower screens.
- Restaurant and food cards use local SVG artwork; Google Fonts and optional embeds may use external network access.

## Important

This is a UI refresh, not a guarantee that every backend feature has been fully tested. Before a faculty demo, test signup + OTP, login, restaurant search/filter, review submission, comments, and like/dislike. The app's current secret key is a development placeholder and should not be used for a public production deployment.
