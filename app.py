import os
import secrets
import uuid
import smtplib
from datetime import datetime, timezone, timedelta
from email.message import EmailMessage

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file, send_from_directory
from flask_login import LoginManager, login_user, logout_user
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError
from image_paths import FALLBACK_REL, restaurant_photo_rel, food_photo_rel
from dotenv import load_dotenv

from models import db, User, Restaurant, Location, Review, Rating, Comment, Like, Media, FoodItem
from sentiment import analyze_sentiment
from sqlalchemy import or_

load_dotenv()

app = Flask(__name__)
database_url = os.getenv('DATABASE_URL', 'sqlite:///foodconnect.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'foodconnect-local-demo-key-change-before-deployment'
upload_folder_setting = os.getenv('UPLOAD_FOLDER', os.path.join('static', 'images', 'uploads'))
app.config['UPLOAD_FOLDER'] = (
    upload_folder_setting if os.path.isabs(upload_folder_setting)
    else os.path.join(app.root_path, upload_folder_setting)
)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB max upload
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('COOKIE_SECURE', '0') == '1'

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def _restaurant_asset_path(cuisine=None):
    """Default cover for a restaurant with no photo yet: a neutral, non-illustrated fallback."""
    return FALLBACK_REL


def _fallback_url():
    return url_for('static', filename=FALLBACK_REL)


def _safe_static_url(relative):
    relative = (relative or '').replace('\\\\', '/').lstrip('/')
    if relative.startswith('static/'):
        relative = relative[len('static/'):]
    target = os.path.abspath(os.path.join(app.static_folder, relative))
    if os.path.commonpath([os.path.abspath(app.static_folder), target]) != os.path.abspath(app.static_folder):
        return None
    if os.path.isfile(target):
        return url_for('static', filename=relative)
    return None


def _safe_upload_url(relative):
    relative = (relative or '').replace('\\\\', '/').lstrip('/')
    target = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], relative))
    if os.path.commonpath([os.path.abspath(app.config['UPLOAD_FOLDER']), target]) != os.path.abspath(app.config['UPLOAD_FOLDER']):
        return None
    if os.path.isfile(target):
        return url_for('uploaded_file', filename=relative)
    return None


def _is_illustration(stored):
    return (stored or '').lower().endswith('.svg')


def restaurant_image(place):
    stored = (getattr(place, 'cover_image', '') or '').strip()
    if stored.startswith('uploads/'):
        found = _safe_upload_url(stored[len('uploads/'):])
        if found:
            return found
    elif stored and not stored.startswith(('http://', 'https://')) and not _is_illustration(stored):
        found = _safe_static_url(stored)
        if found:
            return found
    # Seeded restaurants: derive the photo from the name (also repairs rows that still hold an old SVG path).
    found = _safe_static_url(restaurant_photo_rel(getattr(place, 'name', '')))
    return found or _fallback_url()


def food_image(item):
    stored = (getattr(item, 'image_path', '') or '').strip()
    if stored.startswith('/uploads/'):
        stored = stored[1:]
    if stored.startswith('uploads/'):
        found = _safe_upload_url(stored[len('uploads/'):])
        if found:
            return found
    elif stored and not stored.startswith(('http://', 'https://')) and not _is_illustration(stored):
        found = _safe_static_url(stored)
        if found:
            return found
    restaurant = getattr(item, 'restaurant', None)
    found = _safe_static_url(food_photo_rel(getattr(restaurant, 'name', ''), getattr(item, 'name', '')))
    return found or _fallback_url()


def media_image(stored):
    value = (stored or '').strip()
    if value.startswith('/static/'):
        found = _safe_static_url(value[len('/static/'):])
        if found:
            return found
    if value.startswith('/uploads/'):
        found = _safe_upload_url(value[len('/uploads/'):])
        if found:
            return found
    return _fallback_url()


def static_photo(rel):
    """Local photo URL for a fixed path, or the neutral fallback when the file is missing."""
    return _safe_static_url(rel) or _fallback_url()


app.jinja_env.filters['static_photo'] = static_photo
app.jinja_env.filters['restaurant_image'] = restaurant_image
app.jinja_env.filters['food_image'] = food_image
app.jinja_env.filters['media_image'] = media_image
# Socket.IO uses threading mode for simple, reliable local Windows demos.
socketio = SocketIO(app, cors_allowed_origins=None, async_mode='threading')


def upgrade_local_schema():
    """Add non-destructive columns introduced after the initial local demo DB."""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    tables = set(inspector.get_table_names())
    if 'reviews' in tables:
        columns = {col['name'] for col in inspector.get_columns('reviews')}
        if 'sentiment_label' not in columns:
            db.session.execute(text("ALTER TABLE reviews ADD COLUMN sentiment_label VARCHAR(20) DEFAULT 'neutral'"))
            db.session.commit()
    if 'restaurants' in tables:
        columns = {col['name'] for col in inspector.get_columns('restaurants')}
        if 'video_url' not in columns:
            db.session.execute(text('ALTER TABLE restaurants ADD COLUMN video_url VARCHAR(255)'))
            db.session.commit()
    if 'food_items' in tables:
        food_columns = {col['name'] for col in inspector.get_columns('food_items')}
        if 'dietary_tags' not in food_columns:
            db.session.execute(text("ALTER TABLE food_items ADD COLUMN dietary_tags VARCHAR(255) DEFAULT ''"))
            db.session.commit()
    # FoodItem is a new table; db.create_all() creates it without deleting old data.

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def valid_image_upload(file_storage):
    """Validate both extension and actual image content before saving an upload."""
    if not file_storage or not file_storage.filename or not allowed_file(file_storage.filename):
        return False
    try:
        file_storage.stream.seek(0)
        with Image.open(file_storage.stream) as image:
            image.verify()
        file_storage.stream.seek(0)
        return True
    except (UnidentifiedImageError, OSError, ValueError):
        file_storage.stream.seek(0)
        return False


def send_otp_email(to_email, otp):
    """Try to send a real email with the OTP. Falls back to printing in the
    terminal if email credentials are missing or sending fails, so local
    development / testing is never blocked."""
    email_address = os.getenv('EMAIL_ADDRESS')
    email_password = os.getenv('EMAIL_APP_PASSWORD')

    if not email_address or not email_password:
        print(f'===== (No email configured) OTP for {to_email}: {otp} =====')
        return False

    msg = EmailMessage()
    msg['Subject'] = 'Your FoodConnect Verification Code'
    msg['From'] = email_address
    msg['To'] = to_email
    msg.set_content(f'Your FoodConnect OTP code is: {otp}\n\nThis code will expire soon.')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(email_address, email_password)
            smtp.send_message(msg)
        print(f'OTP email sent to {to_email}')
        return True
    except Exception as e:
        print(f'Email sending failed ({e}). ===== Fallback OTP for {to_email}: {otp} =====')
        return False


# ---------------------------------------------------------------------------
# Real-time room subscription (Phase 5)
# ---------------------------------------------------------------------------
@socketio.on('join_restaurant')
def join_restaurant(data):
    try:
        restaurant_id = int((data or {}).get('restaurant_id'))
    except (TypeError, ValueError):
        return
    if Restaurant.query.get(restaurant_id):
        join_room(f'restaurant_{restaurant_id}')
        emit('room_joined', {'restaurant_id': restaurant_id})


# ---------------------------------------------------------------------------
# Homepage
# ---------------------------------------------------------------------------
@app.route('/')
def home():
    featured = Restaurant.query.order_by(Restaurant.id.desc()).limit(6).all()
    for place in featured:
        values = Rating.query.filter_by(restaurant_id=place.id).all()
        place.display_rating = round(sum(x.stars for x in values) / len(values), 1) if values else None
        place.display_address = (Location.query.filter_by(restaurant_id=place.id).first().address if Location.query.filter_by(restaurant_id=place.id).first() else 'Discover this local spot')
    recent_reviews = Review.query.order_by(Review.created_at.desc()).limit(3).all()
    review_feed = []
    for review in recent_reviews:
        author = User.query.get(review.user_id)
        restaurant = Restaurant.query.get(review.restaurant_id)
        rating = Rating.query.filter_by(user_id=review.user_id, restaurant_id=review.restaurant_id).first()
        media = Media.query.filter_by(review_id=review.id).first()
        review_feed.append({
            'id': review.id, 'username': author.username if author else 'Food lover',
            'restaurant': restaurant, 'content': review.content,
            'created_at': review.created_at, 'stars': rating.stars if rating else 0,
            'image_url': media.url if media else None
        })
    return render_template('home.html', featured=featured, review_feed=review_feed,
                           restaurant_count=Restaurant.query.count(), user_count=User.query.count(),
                           review_count=Review.query.count())


# ---------------------------------------------------------------------------
# Real-time username availability check
# ---------------------------------------------------------------------------
@app.route('/check-username')
def check_username():
    username = request.args.get('username', '')
    exists = User.query.filter(db.func.lower(User.username) == username.strip().lower()).first() is not None
    return jsonify({'available': not exists})


# ---------------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if len(username) < 3 or len(username) > 80 or not username.replace('_', '').replace('-', '').isalnum():
            flash('Username must be 3–80 characters and use letters, numbers, _ or -.')
            return redirect(url_for('signup'))
        if '@' not in email or len(email) > 120:
            flash('Please enter a valid email address.')
            return redirect(url_for('signup'))
        if len(password) < 8:
            flash('Password must be at least 8 characters long.')
            return redirect(url_for('signup'))
        if User.query.filter(db.func.lower(User.username) == username.lower()).first():
            flash('Username already taken.')
            return redirect(url_for('signup'))
        if User.query.filter(db.func.lower(User.email) == email).first():
            flash('Email already registered.')
            return redirect(url_for('signup'))

        password_hash = generate_password_hash(password, method='scrypt')
        otp = f"{secrets.randbelow(1000000):06d}"

        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            otp_code=otp,
            otp_created_at=datetime.now(timezone.utc),
            is_verified=False
        )
        db.session.add(new_user)
        db.session.commit()

        send_otp_email(email, otp)

        session['pending_user_id'] = new_user.id
        return redirect(url_for('verify_otp'))

    return render_template('signup.html')


# ---------------------------------------------------------------------------
# OTP Verification
# ---------------------------------------------------------------------------
@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp'].strip()
        user_id = session.get('pending_user_id')

        if not user_id:
            flash('Session expired. Please sign up again.')
            return redirect(url_for('signup'))

        user = User.query.get(user_id)

        otp_is_fresh = False
        if user and user.otp_created_at:
            created_at = user.otp_created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            otp_is_fresh = datetime.now(timezone.utc) - created_at <= timedelta(minutes=10)

        if user and user.otp_code == entered_otp and otp_is_fresh:
            user.is_verified = True
            user.otp_code = None
            user.otp_created_at = None
            db.session.commit()
            session.pop('pending_user_id', None)
            flash('Account verified! Please log in.')
            return redirect(url_for('login'))
        else:
            flash('Incorrect or expired OTP. Use the resend button to request a fresh code.')
            return redirect(url_for('verify_otp'))

    return render_template('verify_otp.html')


@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    user_id = session.get('pending_user_id')
    if not user_id:
        flash('Verification session expired. Please sign up again.')
        return redirect(url_for('signup'))
    user = db.session.get(User, user_id)
    if not user or user.is_verified:
        session.pop('pending_user_id', None)
        flash('No pending account verification was found.')
        return redirect(url_for('login'))
    otp = f"{secrets.randbelow(1000000):06d}"
    user.otp_code = otp
    user.otp_created_at = datetime.now(timezone.utc)
    db.session.commit()
    send_otp_email(user.email, otp)
    flash('A new verification code has been sent. It is valid for 10 minutes.')
    return redirect(url_for('verify_otp'))


# ---------------------------------------------------------------------------
# Login / Logout
# ---------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid username or password.')
            return redirect(url_for('login'))

        if not user.is_verified:
            flash('Please verify your account first.')
            return redirect(url_for('login'))

        login_user(user)
        session['user_id'] = user.id  # retained for existing templates/routes
        session['username'] = user.username
        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])


# ---------------------------------------------------------------------------
# Restaurant listing — search, filters, pagination (Phase 4 & 6)
# ---------------------------------------------------------------------------
@app.route('/restaurants')
def restaurants():
    page = request.args.get('page', 1, type=int)
    per_page = 6

    search_query = request.args.get('q', '').strip()
    cuisine_filter = request.args.get('cuisine', '').strip()
    price_filter = request.args.get('price', '').strip()
    dietary_filters = [x.strip() for x in request.args.getlist('dietary_tag') if x.strip()]

    query = Restaurant.query

    if search_query:
        query = query.filter(or_(Restaurant.name.ilike(f'%{search_query}%'), Restaurant.cuisine_type.ilike(f'%{search_query}%')))
    if cuisine_filter:
        query = query.filter(Restaurant.cuisine_type == cuisine_filter)
    if price_filter:
        query = query.filter(Restaurant.price_range == price_filter)
    for dietary_tag in dietary_filters:
        matching_restaurants = db.session.query(FoodItem.restaurant_id).filter(
            FoodItem.dietary_tags.ilike(f'%{dietary_tag}%')
        ).distinct()
        query = query.filter(Restaurant.id.in_(matching_restaurants))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # For the filter dropdowns, get the distinct list of cuisines/prices that exist
    all_cuisines = sorted({r.cuisine_type for r in Restaurant.query.all() if r.cuisine_type})
    all_prices = sorted({r.price_range for r in Restaurant.query.all() if r.price_range})
    rating_map = {}
    location_map = {}
    for item in pagination.items:
        values = Rating.query.filter_by(restaurant_id=item.id).all()
        rating_map[item.id] = round(sum(x.stars for x in values) / len(values), 1) if values else None
        loc = Location.query.filter_by(restaurant_id=item.id).first()
        location_map[item.id] = loc.address if loc and loc.address else 'Chattogram'

    return render_template(
        'restaurants.html',
        restaurants=pagination.items,
        pagination=pagination,
        all_cuisines=all_cuisines,
        all_prices=all_prices,
        search_query=search_query,
        cuisine_filter=cuisine_filter,
        price_filter=price_filter,
        dietary_filters=dietary_filters,
        rating_map=rating_map,
        location_map=location_map,
    )


# ---------------------------------------------------------------------------
# Community restaurant submission
# ---------------------------------------------------------------------------
@app.route('/restaurants/add', methods=['GET', 'POST'])
def add_restaurant():
    if 'user_id' not in session:
        flash('Please log in to suggest a restaurant.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        cuisine = request.form.get('cuisine_type', '').strip()
        price = request.form.get('price_range', '').strip()
        address = request.form.get('address', '').strip()
        cover_image = ''
        cover_photo = request.files.get('cover_photo')
        video_url = request.form.get('video_url', '').strip()

        if not name or not cuisine or price not in ('$', '$$', '$$$') or not address:
            flash('Please complete all required fields and choose a valid price range.')
            return render_template('add_restaurant.html', form=request.form)
        if Restaurant.query.filter(db.func.lower(Restaurant.name) == name.lower()).first():
            flash('A restaurant with this name already exists.')
            return render_template('add_restaurant.html', form=request.form)

        if cover_photo and cover_photo.filename:
            if not valid_image_upload(cover_photo):
                flash('Restaurant photo must be PNG, JPG, JPEG, GIF or WEBP.')
                return render_template('add_restaurant.html', form=request.form)
            safe_name = secure_filename(cover_photo.filename)
            unique_name = f"restaurant_{uuid.uuid4().hex[:10]}_{safe_name}"
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            cover_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
            cover_image = f'uploads/{unique_name}'

        restaurant = Restaurant(name=name, cuisine_type=cuisine, price_range=price,
                                cover_image=cover_image or _restaurant_asset_path(cuisine), video_url=video_url or None)
        db.session.add(restaurant)
        db.session.flush()
        db.session.add(Location(restaurant_id=restaurant.id, address=address))
        db.session.commit()
        flash('Restaurant suggestion added successfully!')
        return redirect(url_for('restaurant_detail', restaurant_id=restaurant.id))

    return render_template('add_restaurant.html', form={})


# ---------------------------------------------------------------------------
# Admin restaurant maintenance
# ---------------------------------------------------------------------------
@app.route('/restaurant/<int:restaurant_id>/edit', methods=['GET', 'POST'])
def edit_restaurant(restaurant_id):
    if not current_user_is_admin():
        return ('Admin access required. Configure ADMIN_EMAIL and sign in with that verified account.', 403)
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    location = Location.query.filter_by(restaurant_id=restaurant.id).first()
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        cuisine = (request.form.get('cuisine_type') or '').strip()
        price = (request.form.get('price_range') or '').strip()
        address = (request.form.get('address') or '').strip()
        video_url = (request.form.get('video_url') or '').strip()
        if not name or not cuisine or price not in ('$', '$$', '$$$') or not address:
            flash('Name, cuisine, valid price range and address are required.')
            return render_template('edit_restaurant.html', restaurant=restaurant, location=location)
        restaurant.name, restaurant.cuisine_type, restaurant.price_range = name, cuisine, price
        restaurant.video_url = video_url or None
        cover_photo = request.files.get('cover_photo')
        if cover_photo and cover_photo.filename:
            if not valid_image_upload(cover_photo):
                flash('Restaurant photo must be PNG, JPG, JPEG, GIF or WEBP.')
                return render_template('edit_restaurant.html', restaurant=restaurant, location=location)
            filename = secure_filename(f"restaurant_{restaurant.id}_{uuid.uuid4().hex[:10]}_{cover_photo.filename}")
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            cover_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            restaurant.cover_image = f'uploads/{filename}'
        if location:
            location.address = address
        else:
            db.session.add(Location(restaurant_id=restaurant.id, address=address))
        db.session.commit()
        flash('Restaurant updated.')
        return redirect(url_for('restaurant_detail', restaurant_id=restaurant.id))
    return render_template('edit_restaurant.html', restaurant=restaurant, location=location)


@app.route('/restaurant/<int:restaurant_id>/delete', methods=['POST'])
def delete_restaurant(restaurant_id):
    if not current_user_is_admin():
        return ('Admin access required.', 403)
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    review_ids = [row.id for row in Review.query.filter_by(restaurant_id=restaurant.id).all()]
    if review_ids:
        Comment.query.filter(Comment.review_id.in_(review_ids)).delete(synchronize_session=False)
        Like.query.filter(Like.review_id.in_(review_ids)).delete(synchronize_session=False)
        Media.query.filter(Media.review_id.in_(review_ids)).delete(synchronize_session=False)
        Review.query.filter(Review.id.in_(review_ids)).delete(synchronize_session=False)
    Rating.query.filter_by(restaurant_id=restaurant.id).delete(synchronize_session=False)
    FoodItem.query.filter_by(restaurant_id=restaurant.id).delete(synchronize_session=False)
    Location.query.filter_by(restaurant_id=restaurant.id).delete(synchronize_session=False)
    db.session.delete(restaurant)
    db.session.commit()
    flash('Restaurant and its related demo content were deleted.')
    return redirect(url_for('restaurants'))


# ---------------------------------------------------------------------------
# Restaurant detail page
# ---------------------------------------------------------------------------
@app.route('/restaurant/<int:restaurant_id>')
def restaurant_detail(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    reviews = Review.query.filter_by(restaurant_id=restaurant_id).order_by(Review.created_at.desc()).all()

    ratings = Rating.query.filter_by(restaurant_id=restaurant_id).all()
    avg_rating = round(sum(r.stars for r in ratings) / len(ratings), 1) if ratings else 0

    # Build a lookup of username, comments, and like counts for each review
    review_data = []
    for review in reviews:
        author = User.query.get(review.user_id)
        comments = Comment.query.filter_by(review_id=review.id).order_by(Comment.created_at.asc()).all()
        comment_data = []
        for c in comments:
            c_author = User.query.get(c.user_id)
            comment_data.append({'username': c_author.username if c_author else 'Unknown', 'content': c.content})

        like_count = Like.query.filter_by(review_id=review.id, type='like').count()
        dislike_count = Like.query.filter_by(review_id=review.id, type='dislike').count()

        media = Media.query.filter_by(review_id=review.id).first()

        rating = Rating.query.filter_by(user_id=review.user_id, restaurant_id=review.restaurant_id).first()
        review_data.append({
            'id': review.id,
            'username': author.username if author else 'Unknown',
            'content': review.content,
            'stars': rating.stars if rating else 0,
            'sentiment_label': getattr(review, 'sentiment_label', 'neutral') or 'neutral',
            'created_at': review.created_at,
            'comments': comment_data,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'image_url': media.url if media else None,
        })

    location = Location.query.filter_by(restaurant_id=restaurant_id).first()
    menu_query = FoodItem.query.filter_by(restaurant_id=restaurant_id, is_available=True)
    menu_search = request.args.get('food', '').strip()
    menu_category = request.args.get('food_category', '').strip()
    menu_dietary = request.args.get('dietary', '').strip()
    if menu_search:
        menu_query = menu_query.filter(FoodItem.name.ilike(f'%{menu_search}%'))
    if menu_category:
        menu_query = menu_query.filter_by(category=menu_category)
    if menu_dietary:
        menu_query = menu_query.filter(FoodItem.dietary_tags.ilike(f'%{menu_dietary}%'))
    food_items = menu_query.order_by(FoodItem.category.asc(), FoodItem.name.asc()).all()
    food_categories = sorted({item.category for item in FoodItem.query.filter_by(restaurant_id=restaurant_id, is_available=True).all() if item.category})
    return render_template(
        'restaurant_detail.html',
        restaurant=restaurant,
        location=location,
        reviews=review_data,
        avg_rating=avg_rating,
        total_reviews=len(reviews),
        food_items=food_items,
        food_categories=food_categories,
        menu_search=menu_search,
        menu_category=menu_category,
        menu_dietary=menu_dietary,
        is_admin=current_user_is_admin(),
    )


# ---------------------------------------------------------------------------
# Restaurant menu management
# ---------------------------------------------------------------------------
@app.route('/restaurant/<int:restaurant_id>/menu/add', methods=['POST'])
def add_food_item(restaurant_id):
    if 'user_id' not in session:
        flash('Please log in to suggest a menu item.')
        return redirect(url_for('login'))

    restaurant = Restaurant.query.get_or_404(restaurant_id)
    name = (request.form.get('name') or '').strip()
    description = (request.form.get('description') or '').strip()
    category = (request.form.get('category') or 'Main Course').strip()
    raw_price = (request.form.get('price') or '').strip()
    dietary_tags = ','.join(sorted({tag.strip().title() for tag in request.form.get('dietary_tags', '').split(',') if tag.strip()}))
    image_file = request.files.get('image_file')

    if not name or not raw_price:
        flash('Food name and price are required.')
        return redirect(url_for('restaurant_detail', restaurant_id=restaurant.id) + '#food-menu')
    try:
        price = float(raw_price)
        if price < 0 or price > 10000000:
            raise ValueError
    except ValueError:
        flash('Enter a valid food price.')
        return redirect(url_for('restaurant_detail', restaurant_id=restaurant.id) + '#food-menu')

    image_path = None
    if image_file and image_file.filename:
        if not valid_image_upload(image_file):
            flash('Food photo must be PNG, JPG, JPEG, GIF or WEBP.')
            return redirect(url_for('restaurant_detail', restaurant_id=restaurant.id) + '#food-menu')
        upload_folder = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        safe_name = secure_filename(image_file.filename)
        unique_name = f"food_{restaurant.id}_{uuid.uuid4().hex[:10]}_{safe_name}"
        image_file.save(os.path.join(upload_folder, unique_name))
        image_path = f'uploads/{unique_name}'

    item = FoodItem(restaurant_id=restaurant.id, name=name, description=description[:500],
                    price=price, category=category[:60] or 'Main Course', image_path=image_path,
                    dietary_tags=dietary_tags[:255], is_available=True)
    db.session.add(item)
    db.session.commit()
    flash(f'{name} added to the menu.')
    return redirect(url_for('restaurant_detail', restaurant_id=restaurant.id) + '#food-menu')


# ---------------------------------------------------------------------------
# Post a review (with optional photo + star rating)
# ---------------------------------------------------------------------------
@app.route('/restaurant/<int:restaurant_id>/review', methods=['POST'])
def post_review(restaurant_id):
    if 'user_id' not in session:
        flash('Please log in to post a review.')
        return redirect(url_for('login'))

    Restaurant.query.get_or_404(restaurant_id)
    content = (request.form.get('content') or '').strip()
    if not content:
        flash('Please write a few words about your experience.')
        return redirect(url_for('restaurant_detail', restaurant_id=restaurant_id))
    if len(content) > 3000:
        flash('Please keep your review under 3,000 characters.')
        return redirect(url_for('restaurant_detail', restaurant_id=restaurant_id))
    visited_on_str = request.form.get('visited_on') or None
    visited_on = None
    if visited_on_str:
        try:
            visited_on = datetime.strptime(visited_on_str, '%Y-%m-%d').date()
        except ValueError:
            visited_on = None
    try:
        stars = int(request.form.get('stars', 0))
    except (TypeError, ValueError):
        stars = 0
    if stars not in range(1, 6):
        flash('Rating must be between 1 and 5 stars.')
        return redirect(url_for('restaurant_detail', restaurant_id=restaurant_id))

    new_review = Review(
        user_id=session['user_id'],
        restaurant_id=restaurant_id,
        content=content,
        visited_on=visited_on,
        sentiment_label=analyze_sentiment(content)
    )
    db.session.add(new_review)
    db.session.flush()  # get new_review.id before commit

    if stars > 0:
        existing_rating = Rating.query.filter_by(user_id=session['user_id'], restaurant_id=restaurant_id).first()
        if existing_rating:
            existing_rating.stars = stars
        else:
            db.session.add(Rating(user_id=session['user_id'], restaurant_id=restaurant_id, stars=stars))

    # Optional photo upload
    photo = request.files.get('photo')
    if photo and photo.filename:
        if not valid_image_upload(photo):
            db.session.rollback()
            flash('Review photo must be PNG, JPG, JPEG, GIF or WEBP.')
            return redirect(url_for('restaurant_detail', restaurant_id=restaurant_id))
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filename = secure_filename(f"review_{new_review.id}_{uuid.uuid4().hex[:10]}_{photo.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(filepath)
        url = url_for('uploaded_file', filename=filename)
        db.session.add(Media(review_id=new_review.id, type='image', url=url))

    db.session.commit()
    flash('Review posted successfully!')
    return redirect(url_for('restaurant_detail', restaurant_id=restaurant_id))


# ---------------------------------------------------------------------------
# Comments — AJAX (Phase 5)
# ---------------------------------------------------------------------------
@app.route('/review/<int:review_id>/comment', methods=['POST'])
def post_comment(review_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Please log in to comment.'}), 401

    data = request.get_json(silent=True) or {}
    content = (data.get('content') or '').strip()
    if not content:
        return jsonify({'error': 'Comment cannot be empty.'}), 400

    if not Review.query.get(review_id):
        return jsonify({'error': 'Review not found.'}), 404
    if len(content) > 500:
        return jsonify({'error': 'Comment must be 500 characters or fewer.'}), 400
    comment = Comment(review_id=review_id, user_id=session['user_id'], content=content)
    db.session.add(comment)
    db.session.commit()

    review = Review.query.get(review_id)
    payload = {
        'review_id': review_id,
        'username': session['username'],
        'content': comment.content,
        'created_at': comment.created_at.strftime('%d %b %Y %H:%M'),
    }
    # Broadcast to every open detail page for this restaurant, including the sender.
    socketio.emit('comment_added', payload, to=f'restaurant_{review.restaurant_id}')
    return jsonify(payload)


# ---------------------------------------------------------------------------
# Like / Dislike — AJAX (Phase 5)
# ---------------------------------------------------------------------------
@app.route('/review/<int:review_id>/react', methods=['POST'])
def react_to_review(review_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Please log in to react.'}), 401

    data = request.get_json(silent=True) or {}
    reaction_type = data.get('type')  # 'like' or 'dislike'
    if reaction_type not in ('like', 'dislike'):
        return jsonify({'error': 'Invalid reaction type.'}), 400

    review = Review.query.get(review_id)
    if not review:
        return jsonify({'error': 'Review not found.'}), 404

    existing = Like.query.filter_by(review_id=review_id, user_id=session['user_id']).first()
    if existing:
        if existing.type == reaction_type:
            db.session.delete(existing)  # toggle off
        else:
            existing.type = reaction_type
    else:
        db.session.add(Like(review_id=review_id, user_id=session['user_id'], type=reaction_type))

    db.session.commit()

    like_count = Like.query.filter_by(review_id=review_id, type='like').count()
    dislike_count = Like.query.filter_by(review_id=review_id, type='dislike').count()
    payload = {'review_id': review_id, 'like_count': like_count, 'dislike_count': dislike_count}
    socketio.emit('reaction_updated', payload, to=f'restaurant_{review.restaurant_id}')
    return jsonify(payload)

# ---------------------------------------------------------------------------
# Phase 10 — REST API
# ---------------------------------------------------------------------------
def restaurant_json(place):
    location = Location.query.filter_by(restaurant_id=place.id).first()
    ratings = Rating.query.filter_by(restaurant_id=place.id).all()
    average = round(sum(item.stars for item in ratings) / len(ratings), 1) if ratings else None
    return {'id': place.id, 'name': place.name, 'cuisine_type': place.cuisine_type,
            'price_range': place.price_range, 'cover_image': restaurant_image(place),
            'video_url': place.video_url,
            'location': ({'address': location.address, 'latitude': location.latitude,
                          'longitude': location.longitude} if location else None),
            'average_rating': average, 'rating_count': len(ratings)}


def review_json(review):
    author = User.query.get(review.user_id)
    place = Restaurant.query.get(review.restaurant_id)
    rating = Rating.query.filter_by(user_id=review.user_id, restaurant_id=review.restaurant_id).first()
    return {'id': review.id, 'content': review.content,
            'visited_on': review.visited_on.isoformat() if review.visited_on else None,
            'sentiment': review.sentiment_label,
            'created_at': review.created_at.isoformat() if review.created_at else None,
            'username': author.username if author else 'Unknown',
            'restaurant': {'id': place.id, 'name': place.name} if place else None,
            'rating': rating.stars if rating else None,
            'image_url': media_image((Media.query.filter_by(review_id=review.id).first().url
                                      if Media.query.filter_by(review_id=review.id).first() else None)),
            'likes': Like.query.filter_by(review_id=review.id, type='like').count(),
            'dislikes': Like.query.filter_by(review_id=review.id, type='dislike').count()}


@app.route('/api/restaurants', methods=['GET', 'POST'])
def api_restaurants():
    if request.method == 'POST':
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required.'}), 401
        data = request.get_json(silent=True) or {}
        name = (data.get('name') or '').strip()
        cuisine = (data.get('cuisine_type') or '').strip()
        price = (data.get('price_range') or '').strip()
        address = (data.get('address') or '').strip()
        if not name or not cuisine or price not in ('$', '$$', '$$$') or not address:
            return jsonify({'error': 'name, cuisine_type, valid price_range and address are required.'}), 400
        place = Restaurant(name=name[:150], cuisine_type=cuisine[:80], price_range=price,
                           cover_image=_restaurant_asset_path(cuisine))
        db.session.add(place)
        db.session.flush()
        db.session.add(Location(restaurant_id=place.id, address=address[:255]))
        db.session.commit()
        return jsonify(restaurant_json(place)), 201

    query = Restaurant.query
    search_term = (request.args.get('q') or '').strip()
    cuisine = (request.args.get('cuisine') or '').strip()
    price = (request.args.get('price_range') or '').strip()
    if search_term:
        query = query.filter(or_(Restaurant.name.ilike(f'%{search_term}%'),
                                 Restaurant.cuisine_type.ilike(f'%{search_term}%')))
    if cuisine:
        query = query.filter(Restaurant.cuisine_type.ilike(f'%{cuisine}%'))
    if price:
        query = query.filter_by(price_range=price)
    page = max(request.args.get('page', 1, type=int), 1)
    per_page = min(max(request.args.get('per_page', 10, type=int), 1), 50)
    pagination = query.order_by(Restaurant.name.asc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({'data': [restaurant_json(x) for x in pagination.items],
                    'pagination': {'page': page, 'per_page': per_page, 'total': pagination.total,
                                   'pages': pagination.pages}})


@app.route('/api/restaurants/<int:restaurant_id>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
def api_restaurant_detail(restaurant_id):
    place = Restaurant.query.get_or_404(restaurant_id)
    if request.method == 'GET':
        return jsonify(restaurant_json(place))
    if not current_user_is_admin():
        return jsonify({'error': 'Admin access required.'}), 403
    if request.method == 'DELETE':
        review_ids = [row.id for row in Review.query.filter_by(restaurant_id=place.id).all()]
        if review_ids:
            Comment.query.filter(Comment.review_id.in_(review_ids)).delete(synchronize_session=False)
            Like.query.filter(Like.review_id.in_(review_ids)).delete(synchronize_session=False)
            Media.query.filter(Media.review_id.in_(review_ids)).delete(synchronize_session=False)
            Review.query.filter(Review.id.in_(review_ids)).delete(synchronize_session=False)
        Rating.query.filter_by(restaurant_id=place.id).delete(synchronize_session=False)
        FoodItem.query.filter_by(restaurant_id=place.id).delete(synchronize_session=False)
        Location.query.filter_by(restaurant_id=place.id).delete(synchronize_session=False)
        db.session.delete(place)
        db.session.commit()
        return jsonify({'message': 'Restaurant deleted.'})
    data = request.get_json(silent=True) or {}
    if 'name' in data:
        new_name = str(data['name']).strip()
        if not new_name:
            return jsonify({'error': 'name cannot be empty.'}), 400
        place.name = new_name[:150]
    if 'cuisine_type' in data:
        new_cuisine = str(data['cuisine_type']).strip()
        if not new_cuisine:
            return jsonify({'error': 'cuisine_type cannot be empty.'}), 400
        place.cuisine_type = new_cuisine[:80]
    if 'price_range' in data:
        if data['price_range'] not in ('$', '$$', '$$$'):
            return jsonify({'error': 'price_range must be $, $$ or $$$.'}), 400
        place.price_range = data['price_range']
    if 'video_url' in data:
        place.video_url = (str(data['video_url']).strip() or None)
    if 'address' in data:
        location = Location.query.filter_by(restaurant_id=place.id).first()
        if location:
            location.address = str(data['address']).strip()[:255]
        else:
            db.session.add(Location(restaurant_id=place.id, address=str(data['address']).strip()[:255]))
    db.session.commit()
    return jsonify(restaurant_json(place))


@app.route('/api/reviews', methods=['GET', 'POST'])
def api_reviews():
    if request.method == 'GET':
        query = Review.query
        restaurant_id = request.args.get('restaurant_id', type=int)
        if restaurant_id:
            query = query.filter_by(restaurant_id=restaurant_id)
        page = max(request.args.get('page', 1, type=int), 1)
        pagination = query.order_by(Review.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
        return jsonify({'data': [review_json(x) for x in pagination.items],
                        'pagination': {'page': page, 'total': pagination.total, 'pages': pagination.pages}})
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required.'}), 401
    data = request.get_json(silent=True) or {}
    restaurant_id = data.get('restaurant_id')
    content = (data.get('content') or '').strip()
    if not isinstance(restaurant_id, int) or not Restaurant.query.get(restaurant_id):
        return jsonify({'error': 'A valid restaurant_id is required.'}), 400
    if not content or len(content) > 3000:
        return jsonify({'error': 'Review content must contain 1–3000 characters.'}), 400
    visited_on = None
    if data.get('visited_on'):
        try:
            visited_on = datetime.strptime(data['visited_on'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return jsonify({'error': 'visited_on must use YYYY-MM-DD.'}), 400
    review = Review(user_id=session['user_id'], restaurant_id=restaurant_id, content=content,
                    visited_on=visited_on, sentiment_label=analyze_sentiment(content))
    db.session.add(review)
    stars = data.get('stars')
    if stars is not None:
        try:
            stars = int(stars)
        except (TypeError, ValueError):
            return jsonify({'error': 'stars must be an integer from 1 to 5.'}), 400
        if stars not in range(1, 6):
            return jsonify({'error': 'stars must be an integer from 1 to 5.'}), 400
        existing_rating = Rating.query.filter_by(user_id=session['user_id'], restaurant_id=restaurant_id).first()
        if existing_rating:
            existing_rating.stars = stars
        else:
            db.session.add(Rating(user_id=session['user_id'], restaurant_id=restaurant_id, stars=stars))
    db.session.commit()
    return jsonify(review_json(review)), 201


@app.route('/api/reviews/<int:review_id>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
def api_review_detail(review_id):
    review = Review.query.get_or_404(review_id)
    if request.method == 'GET':
        return jsonify(review_json(review))
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required.'}), 401
    if session['user_id'] != review.user_id and not current_user_is_admin():
        return jsonify({'error': 'You can only modify your own review.'}), 403
    if request.method == 'DELETE':
        Comment.query.filter_by(review_id=review.id).delete(synchronize_session=False)
        Like.query.filter_by(review_id=review.id).delete(synchronize_session=False)
        Media.query.filter_by(review_id=review.id).delete(synchronize_session=False)
        Rating.query.filter_by(user_id=review.user_id, restaurant_id=review.restaurant_id).delete(synchronize_session=False)
        db.session.delete(review)
        db.session.commit()
        return jsonify({'message': 'Review deleted.'})
    data = request.get_json(silent=True) or {}
    if 'content' in data:
        content = str(data['content']).strip()
        if not content or len(content) > 3000:
            return jsonify({'error': 'Review content must contain 1–3000 characters.'}), 400
        review.content = content
        review.sentiment_label = analyze_sentiment(content)
    if 'visited_on' in data:
        try:
            review.visited_on = datetime.strptime(data['visited_on'], '%Y-%m-%d').date() if data['visited_on'] else None
        except (ValueError, TypeError):
            return jsonify({'error': 'visited_on must use YYYY-MM-DD.'}), 400
    if 'stars' in data:
        try:
            stars = int(data['stars'])
        except (TypeError, ValueError):
            return jsonify({'error': 'stars must be an integer from 1 to 5.'}), 400
        if stars not in range(1, 6):
            return jsonify({'error': 'stars must be an integer from 1 to 5.'}), 400
        rating = Rating.query.filter_by(user_id=review.user_id, restaurant_id=review.restaurant_id).first()
        if rating:
            rating.stars = stars
        else:
            db.session.add(Rating(user_id=review.user_id, restaurant_id=review.restaurant_id, stars=stars))
    db.session.commit()
    return jsonify(review_json(review))


# ---------------------------------------------------------------------------
# Phase 10 — GraphQL endpoint (Ariadne)
# ---------------------------------------------------------------------------
@app.route('/graphql', methods=['POST'])
def graphql_endpoint():
    try:
        from ariadne import QueryType, ObjectType, make_executable_schema, graphql_sync
    except ImportError:
        return jsonify({'errors': [{'message': 'Install dependencies with pip install -r requirements.txt.'}]}), 503
    type_defs = '''
    type Location { address: String, latitude: Float, longitude: Float }
    type Restaurant { id: Int!, name: String!, cuisine_type: String, price_range: String,
                      average_rating: Float, location: Location }
    type Review { id: Int!, content: String, sentiment: String, username: String,
                  restaurant_name: String, rating: Int }
    type Query { restaurants(search: String, cuisine: String, priceRange: String): [Restaurant!]!, restaurant(id: Int!): Restaurant,
                 reviews(restaurantId: Int): [Review!]! }
    '''
    query = QueryType()
    def resolve_restaurants(_, info, search=None, cuisine=None, priceRange=None):
        q = Restaurant.query
        if search:
            q = q.filter(or_(Restaurant.name.ilike(f'%{search}%'), Restaurant.cuisine_type.ilike(f'%{search}%')))
        if cuisine:
            q = q.filter(Restaurant.cuisine_type.ilike(f'%{cuisine}%'))
        if priceRange:
            q = q.filter_by(price_range=priceRange)
        return q.order_by(Restaurant.name.asc()).all()
    query.set_field('restaurants', resolve_restaurants)
    query.set_field('restaurant', lambda _, info, id: Restaurant.query.get(id))
    query.set_field('reviews', lambda _, info, restaurantId=None: (
        Review.query.filter_by(restaurant_id=restaurantId) if restaurantId else Review.query
    ).order_by(Review.created_at.desc()).limit(100).all())
    restaurant_type = ObjectType('Restaurant')
    def resolve_average(obj, *_):
        ratings = Rating.query.filter_by(restaurant_id=obj.id).all()
        return round(sum(x.stars for x in ratings) / len(ratings), 1) if ratings else None
    restaurant_type.set_field('average_rating', resolve_average)
    restaurant_type.set_field('location', lambda obj, *_: Location.query.filter_by(restaurant_id=obj.id).first())
    review_type = ObjectType('Review')
    review_type.set_field('username', lambda obj, *_: (User.query.get(obj.user_id).username if User.query.get(obj.user_id) else None))
    review_type.set_field('restaurant_name', lambda obj, *_: (Restaurant.query.get(obj.restaurant_id).name if Restaurant.query.get(obj.restaurant_id) else None))
    def resolve_review_rating(obj, *_):
        item = Rating.query.filter_by(user_id=obj.user_id, restaurant_id=obj.restaurant_id).first()
        return item.stars if item else None
    review_type.set_field('rating', resolve_review_rating)
    schema = make_executable_schema(type_defs, query, restaurant_type, review_type)
    success, result = graphql_sync(schema, request.get_json(silent=True) or {},
                                   context_value={'request': request}, debug=app.debug)
    return jsonify(result), (200 if success else 400)


# ---------------------------------------------------------------------------
# Phase 11 — Admin monthly report (ADMIN_EMAIL must match a verified account)
# ---------------------------------------------------------------------------
def current_user_is_admin():
    admin_email = (os.getenv('ADMIN_EMAIL') or '').strip().lower()
    if not admin_email or 'user_id' not in session:
        return False
    user = User.query.get(session['user_id'])
    return bool(user and user.is_verified and user.email.lower() == admin_email)


def monthly_top_restaurants():
    from sqlalchemy import func, distinct
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Ratings are attached to a user's restaurant review in this schema, so
    # include ratings connected to reviews created during the current month.
    rows = db.session.query(Restaurant.id, Restaurant.name, Restaurant.cuisine_type,
        func.avg(Rating.stars).label('average_rating'),
        func.count(distinct(Rating.id)).label('rating_count'))\
        .join(Review, Review.restaurant_id == Restaurant.id)\
        .join(Rating, (Rating.restaurant_id == Review.restaurant_id) & (Rating.user_id == Review.user_id))\
        .filter(Review.created_at >= month_start)\
        .group_by(Restaurant.id, Restaurant.name, Restaurant.cuisine_type)\
        .order_by(func.avg(Rating.stars).desc(), func.count(distinct(Rating.id)).desc()).limit(10).all()
    return [{'id': r.id, 'name': r.name, 'cuisine': r.cuisine_type or '—',
             'average_rating': round(float(r.average_rating), 2), 'rating_count': r.rating_count} for r in rows]


@app.route('/admin/reports')
def admin_reports():
    if not current_user_is_admin():
        return ('Admin access required. Set ADMIN_EMAIL in .env and sign in with that verified account.', 403)
    return render_template('admin_reports.html', rows=monthly_top_restaurants())


@app.route('/admin/reports/monthly.pdf')
def admin_monthly_pdf():
    if not current_user_is_admin():
        return ('Admin access required.', 403)
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from io import BytesIO
    except ImportError:
        return ('Install dependencies with pip install -r requirements.txt.', 503)
    rows = monthly_top_restaurants()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title='FoodConnect Monthly Restaurant Report')
    styles = getSampleStyleSheet()
    story = [Paragraph('FoodConnect — Top-Rated Restaurants', styles['Title']),
             Paragraph(datetime.utcnow().strftime('Generated %B %Y'), styles['Normal']), Spacer(1, 18)]
    data = [['Restaurant', 'Cuisine', 'Average rating', 'Ratings']]
    data += [[r['name'], r['cuisine'], f"{r['average_rating']:.2f}/5", str(r['rating_count'])] for r in rows]
    if len(data) == 1:
        data.append(['No ratings yet', '—', '—', '0'])
    table = Table(data, repeatRows=1, colWidths=[190, 120, 110, 70])
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#243b32')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d9dfdb')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f6f4')]),
        ('PADDING', (0, 0), (-1, -1), 8)]))
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                     download_name='foodconnect-monthly-report.pdf')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        upgrade_local_schema()
    socketio.run(app, debug=os.getenv('FLASK_DEBUG', '0') == '1', allow_unsafe_werkzeug=True)
