# FoodConnect — Final Submission Checklist

## 1. Run locally (Windows)

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python seed_data.py
python app.py
```

Open `http://127.0.0.1:5000`.

## 2. Test the main user journey

- [ ] Homepage loads and local restaurant artwork appears.
- [ ] Explore search, cuisine, price and dietary filters work together.
- [ ] Add/remove dietary filter rows and pagination preserve filter values.
- [ ] Open a restaurant detail page; menu, address/map and optional video render.
- [ ] Register; verify the OTP from terminal or configured email; test OTP expiry/resend.
- [ ] Log in and log out.
- [ ] Suggest a restaurant; configure `ADMIN_EMAIL` to test admin edit/delete.
- [ ] Post a review with a rating, visit date and valid image upload.
- [ ] Confirm invalid image uploads are rejected.
- [ ] Add a menu item with a local photo and dietary tags.
- [ ] Add a comment and toggle like/dislike; test with two browser sessions for live updates.
- [ ] Check sentiment label (lexical fallback unless TFLite files are supplied).
- [ ] Test REST GET/POST/PATCH/DELETE endpoints.
- [ ] Install requirements and test a GraphQL query at `/graphql`.
- [ ] Configure `ADMIN_EMAIL`, open `/admin/reports`, and export the PDF.

## 3. Production deployment

- [ ] Push to GitHub without `.env`, local databases or uploaded user files.
- [ ] Create the Render Blueprint and review resource costs.
- [ ] Configure email OTP sender variables and admin email.
- [ ] Confirm PostgreSQL and persistent upload disk are connected.
- [ ] Inspect Render build and runtime logs.
- [ ] Test the live website and uploaded images.

## Important notes

- The bundled SVG assets are local illustrations, not verified restaurant photographs.
- OTP is printed in the terminal when SMTP credentials are absent; production deployment should configure email.
- The sentiment fallback is not a trained TensorFlow Lite model. Do not claim TFLite is active unless the `.tflite` model and vocabulary are installed.
- The GraphQL route requires Ariadne, installed through `requirements.txt`.
- Sample restaurant names, addresses, coordinates, menu items and prices are illustrative demo data.
- Local test-client checks do not replace manual browser/mobile testing or live deployment verification.
