# FoodConnect: review notes and deployment configuration

## Changes included in this revised package
- Login accepts either a username or email address (case-insensitive).
- A previous unverified signup using the same email can be retried without manually deleting the database row. Verified accounts remain protected.
- Added an `/admin` dashboard route and page with counts for users, restaurants, food items and reviews.
- The signed-in user's dashboard shows the Admin Panel link only when the account is authorized as admin.

## Required Render configuration
Set these values in the Render service's Environment section:
- `ADMIN_EMAIL`: the exact email address of the FoodConnect account that should be the administrator. That account must complete OTP verification and sign in.
- `EMAIL_ADDRESS`: the Gmail address used to send verification emails.
- `EMAIL_APP_PASSWORD`: the Gmail App Password for that sender account.

Do not put these values in source code, ZIP files, GitHub, or chat. After changing Environment Variables, redeploy the service.

## Important behavior
- OTP email delivery requires valid Gmail SMTP configuration. If it is missing, the application cannot send an email; the verification page will not magically receive a code. Check Render logs and configure the email variables.
- `/admin` and `/admin/reports` return an access-denied response unless `ADMIN_EMAIL` matches a verified signed-in user.
- This source package has been syntax-checked. Full Flask integration tests could not be executed in this environment because the required Python packages were not available and network installation was unavailable. Run `python tests/test_app.py` in the project's configured virtual environment before submitting.
- Existing database records have not been deleted or reset. Back up the production database before making any manual data changes.
