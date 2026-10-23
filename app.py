import os
import random
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_socketio import SocketIO, emit, join_room
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from models import db, User, Restaurant, Location, Review, Rating, Comment, Like, Media, FoodItem
from sentiment import analyze_sentiment
from sqlalchemy import or_

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///foodconnect.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'foodconnect-local-demo-key-change-before-deployment')
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB max upload

db.init_app(app)
bcrypt = Bcrypt(app)
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
    # FoodItem is a new table; db.create_all() creates it without deleting old data.

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
    exists = User.query.filter_by(username=username).first() is not None
    return jsonify({'available': not exists})


# ---------------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already taken.')
            return redirect(url_for('signup'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return redirect(url_for('signup'))

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        otp = str(random.randint(100000, 999999))

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

        if user and user.otp_code == entered_otp:
            user.is_verified = True
            user.otp_code = None
            db.session.commit()
            session.pop('pending_user_id', None)
            flash('Account verified! Please log in.')
            return redirect(url_for('login'))
        else:
            flash('Incorrect OTP. Please try again.')
            return redirect(url_for('verify_otp'))

    return render_template('verify_otp.html')


# ---------------------------------------------------------------------------
# Login / Logout
# ---------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if not user or not bcrypt.check_password_hash(user.password_hash, password):
            flash('Invalid username or password.')
            return redirect(url_for('login'))

        if not user.is_verified:
            flash('Please verify your account first.')
            return redirect(url_for('login'))

        session['user_id'] = user.id
        session['username'] = user.username
        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/logout')
def logout():
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

    query = Restaurant.query

    if search_query:
        query = query.filter(or_(Restaurant.name.ilike(f'%{search_query}%'), Restaurant.cuisine_type.ilike(f'%{search_query}%')))
    if cuisine_filter:
        query = query.filter(Restaurant.cuisine_type == cuisine_filter)
    if price_filter:
        query = query.filter(Restaurant.price_range == price_filter)

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
        cover_image = request.form.get('cover_image', '').strip()
        video_url = request.form.get('video_url', '').strip()

        if not name or not cuisine or not price or not address:
            flash('Please complete all required fields.')
            return render_template('add_restaurant.html', form=request.form)
        if Restaurant.query.filter(db.func.lower(Restaurant.name) == name.lower()).first():
            flash('A restaurant with this name already exists.')
            return render_template('add_restaurant.html', form=request.form)

        restaurant = Restaurant(name=name, cuisine_type=cuisine, price_range=price,
                                cover_image=cover_image or 'default_restaurant.jpg', video_url=video_url or None)
        db.session.add(restaurant)
        db.session.flush()
        db.session.add(Location(restaurant_id=restaurant.id, address=address))
        db.session.commit()
        flash('Restaurant suggestion added successfully!')
        return redirect(url_for('restaurant_detail', restaurant_id=restaurant.id))

    return render_template('add_restaurant.html', form={})


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
    if menu_search:
        menu_query = menu_query.filter(FoodItem.name.ilike(f'%{menu_search}%'))
    if menu_category:
        menu_query = menu_query.filter_by(category=menu_category)
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
    image_url = (request.form.get('image_url') or '').strip()
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

    image_path = image_url or None
    if image_file and image_file.filename:
        if not allowed_file(image_file.filename):
            flash('Food photo must be PNG, JPG, JPEG, GIF or WEBP.')
            return redirect(url_for('restaurant_detail', restaurant_id=restaurant.id) + '#food-menu')
        upload_folder = os.path.join(app.root_path, 'static', 'images', 'food_uploads')
        os.makedirs(upload_folder, exist_ok=True)
        safe_name = secure_filename(image_file.filename)
        unique_name = f"food_{restaurant.id}_{int(datetime.now().timestamp())}_{safe_name}"
        image_file.save(os.path.join(upload_folder, unique_name))
        image_path = f'images/food_uploads/{unique_name}'

    item = FoodItem(restaurant_id=restaurant.id, name=name, description=description[:500],
                    price=price, category=category[:60] or 'Main Course', image_path=image_path, is_available=True)
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
    stars = int(request.form.get('stars', 0))

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
    if photo and photo.filename and allowed_file(photo.filename):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filename = secure_filename(f"review_{new_review.id}_{photo.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(filepath)
        url = '/' + filepath.replace('\\', '/')
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
    review = Review.query.get(review_id)
    payload = {'review_id': review_id, 'like_count': like_count, 'dislike_count': dislike_count}
    socketio.emit('reaction_updated', payload, to=f'restaurant_{review.restaurant_id}')
    return jsonify(payload)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        upgrade_local_schema()
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
