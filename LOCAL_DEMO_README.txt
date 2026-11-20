FOODCONNECT — LOCAL DEMO BUILD

This package is prepared for running locally (no Render deployment required).

Run on Windows:
1. Extract this ZIP.
2. Open CMD in the extracted FoodConnect folder.
3. Create/activate a virtual environment if needed:
   python -m venv venv
   venv\Scripts\activate
4. Install dependencies:
   pip install -r requirements.txt
5. Start the app:
   python app.py
6. Open http://127.0.0.1:5000

The included instance/foodconnect.db contains 12 restaurants and 120 food items.
The catalog image paths are populated with local JPEG photographs; the website does
not need to download images while running.

PHOTO NOTE:
The supplied project archive contained a limited photo library. The photo paths for
all 132 catalog entries are now populated using those existing real photographs and
the 18 already downloaded photographs. Some representative photos are reused across
related dishes/restaurant cards, so this is a local presentation-ready repair, not a
claim that all 132 photos are unique or individually photographed for each dish.
The original attribution/licence information for the archived photos was not complete;
verify it before public redistribution.

The previous .env file and .git history are intentionally not included in this ZIP.
