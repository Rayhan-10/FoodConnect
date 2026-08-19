import random
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_bcrypt import Bcrypt
from models import db, User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///foodconnect.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key-change-later'

db.init_app(app)
bcrypt = Bcrypt(app)

# ---------- Homepage ----------
@app.route('/')
def home():
    return render_template('home.html')

# ---------- Real-time username check ----------
@app.route('/check-username')
def check_username():
    username = request.args.get('username', '')
    exists = User.query.filter_by(username=username).first() is not None
    return jsonify({'available': not exists})

# ---------- Signup ----------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already taken.')
            return redirect(url_for('signup'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return redirect(url_for('signup'))

        # Hash the password (never store plain text)
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        # Generate a 6-digit OTP
        otp = str(random.randint(100000, 999999))

        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            otp_code=otp,
            otp_created_at=datetime.utcnow(),
            is_verified=False
        )
        db.session.add(new_user)
        db.session.commit()

        # Simulate sending OTP (prints to terminal for now)
        print(f'===== OTP for {username}: {otp} =====')

        session['pending_user_id'] = new_user.id
        return redirect(url_for('verify_otp'))

    return render_template('signup.html')

# ---------- OTP Verification ----------
@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        user_id = session.get('pending_user_id')

        if not user_id:
            flash('Session expired. Please sign up again.')
            return redirect(url_for('signup'))

        user = User.query.get(user_id)

        if user.otp_code == entered_otp:
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

# ---------- Login ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
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

# ---------- Dashboard (protected page) ----------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

# ---------- Logout ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)