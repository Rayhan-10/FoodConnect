"""End-to-end smoke tests (Flask test client, throw-away SQLite DB + upload folder).
Run from the project root:   python tests/test_app.py
"""
import io
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
TMP = tempfile.mkdtemp()
os.environ['DATABASE_URL'] = 'sqlite:///' + os.path.join(TMP, 'test.db')
os.environ['UPLOAD_FOLDER'] = os.path.join(TMP, 'uploads')
os.environ['SECRET_KEY'] = 'test-secret'

from PIL import Image  # noqa: E402
import app as appmod  # noqa: E402
from models import db, Restaurant, FoodItem, User, Review, Rating, Comment, Like, Location  # noqa: E402

results = []


def check(name, cond, extra=''):
    results.append((name, bool(cond), extra))
    print(('PASS  ' if cond else 'FAIL  ') + name + (f'  [{extra}]' if extra and not cond else ''))


def png_bytes():
    buf = io.BytesIO()
    Image.new('RGB', (80, 60), (180, 90, 30)).save(buf, 'PNG')
    buf.seek(0)
    return buf


app = appmod.app
app.config['TESTING'] = True
with app.app_context():
    db.create_all()
    appmod.upgrade_local_schema()

# ---- seed in a subprocess-free way: simulate LEGACY production rows first, then run the real seed ----
with app.app_context():
    spice = Restaurant(name='Spice Garden', cuisine_type='Indian', price_range='$$', cover_image='images/restaurants/indian.svg')
    db.session.add(spice)
    db.session.flush()
    db.session.add(Location(restaurant_id=spice.id, latitude=22.35, longitude=91.78, address='GEC Circle, Chattogram'))
    db.session.add_all([
        FoodItem(restaurant_id=spice.id, name='Chicken Biryani', price=280, category='Rice & Biryani', image_path='images/food/biryani.svg'),
        FoodItem(restaurant_id=spice.id, name='Butter Chicken', price=360, image_path='https://images.unsplash.com/photo-x'),
        FoodItem(restaurant_id=spice.id, name='Owner Special', price=999, image_path='uploads/keep_me.jpg'),
        FoodItem(restaurant_id=spice.id, name='Community Dish', price=50, image_path='images/food/curry.svg'),
    ])
    user = User(username='olduser', email='old@example.com', password_hash='x', is_verified=True)
    db.session.add(user)
    db.session.flush()
    rev = Review(user_id=user.id, restaurant_id=spice.id, content='Great old review')
    db.session.add(rev)
    db.session.add(Rating(user_id=user.id, restaurant_id=spice.id, stars=4))
    db.session.commit()
    legacy_review_id = rev.id

import runpy  # noqa: E402
import contextlib  # noqa: E402
with contextlib.redirect_stdout(io.StringIO()):
    runpy.run_path(os.path.join(ROOT, 'seed_data.py'), run_name='__seed__')
    runpy.run_path(os.path.join(ROOT, 'seed_data.py'), run_name='__seed__')  # twice: must be idempotent

with app.app_context():
    check('seed: 12 restaurants after running seed twice', Restaurant.query.count() == 12, Restaurant.query.count())
    check('seed: re-running seed creates no duplicate dishes',
          FoodItem.query.filter_by(name='Chicken Biryani', restaurant_id=Restaurant.query.filter_by(name='Spice Garden').first().id).count() == 1)
    sg = Restaurant.query.filter_by(name='Spice Garden').first()
    check('legacy SVG cover repaired to local jpg', sg.cover_image == 'images/restaurants/spice-garden.jpg', sg.cover_image)
    biryani = FoodItem.query.filter_by(name='Chicken Biryani', restaurant_id=sg.id).first()
    butter = FoodItem.query.filter_by(name='Butter Chicken', restaurant_id=sg.id).first()
    owner = FoodItem.query.filter_by(name='Owner Special').first()
    comm = FoodItem.query.filter_by(name='Community Dish').first()
    check('legacy SVG food repaired', biryani.image_path == 'images/food/spice-garden--chicken-biryani.jpg', biryani.image_path)
    check('legacy external URL food repaired', butter.image_path == 'images/food/spice-garden--butter-chicken.jpg', butter.image_path)
    check('user upload path NOT overwritten', owner.image_path == 'uploads/keep_me.jpg', owner.image_path)
    check('non-catalog SVG ref cleared (falls back to neutral image)', comm.image_path is None, comm.image_path)
    check('existing review + rating preserved', Review.query.get(legacy_review_id) is not None and Rating.query.count() >= 1)
    n_food = FoodItem.query.filter(FoodItem.restaurant_id != sg.id).count()
    check('total seeded food items for 11 other restaurants = 110', n_food == 110, n_food)
    sg_id = sg.id

c = app.test_client()
home = c.get('/')
check('GET / returns 200', home.status_code == 200)
html = home.get_data(as_text=True)
check('home has no SVG image reference', '.svg' not in html)
imgs = re.findall(r'<img[^>]+src="([^"]+)"', html)
bad = [u for u in imgs if u.startswith('http')]
check('home <img> tags are all local (no external image URL)', not bad, bad)
for u in imgs:
    r = c.get(u)
    ok = r.status_code == 200 and r.mimetype == 'image/jpeg'
    r.close()
    check(f'image served as JPEG: {u}', ok)

r = c.get('/restaurants')
check('GET /restaurants 200', r.status_code == 200)
check('GET /restaurants?q=spice (search) finds Spice Garden', b'Spice Garden' in c.get('/restaurants?q=spice').data)
check('GET /restaurants?cuisine=Indian filter', c.get('/restaurants?cuisine=Indian').status_code == 200)
rd = c.get(f'/restaurant/{sg_id}')
check('GET restaurant detail 200', rd.status_code == 200)
dh = rd.get_data(as_text=True)
check('detail: no .svg and no external image', '.svg' not in dh and not re.findall(r'<img[^>]+src="http', dh))
for u in set(re.findall(r'<img[^>]+src="([^"]+)"', dh)):
    resp = c.get(u)
    check(f'detail image 200: {u}', resp.status_code == 200 and resp.mimetype == 'image/jpeg')
    resp.close()
check('GET all 12 restaurant detail pages', all(c.get(f'/restaurant/{i}').status_code == 200 for i in range(1, 13)))
check('GET /api/restaurants 200', c.get('/api/restaurants').status_code == 200)

# ---- auth flow ----
s = c.post('/signup', data={'username': 'tester1', 'email': 'tester1@example.com', 'password': 'Password123'}, follow_redirects=False)
check('signup redirects to verify-otp', s.status_code == 302 and 'verify-otp' in s.headers['Location'])
with app.app_context():
    otp = User.query.filter_by(username='tester1').first().otp_code
v = c.post('/verify-otp', data={'otp': otp}, follow_redirects=False)
check('OTP verification accepted', v.status_code == 302 and 'login' in v.headers['Location'])
bad = c.post('/login', data={'username': 'tester1', 'password': 'wrong'}, follow_redirects=True)
check('wrong password rejected', b'Invalid username or password' in bad.data)
ok = c.post('/login', data={'username': 'tester1', 'password': 'Password123'}, follow_redirects=False)
check('login succeeds with username', ok.status_code == 302)
c.get('/logout')
email_login = c.post('/login', data={'username': 'tester1@example.com', 'password': 'Password123'}, follow_redirects=False)
check('login succeeds with email address', email_login.status_code == 302)
check('dashboard (profile) 200 when logged in', c.get('/dashboard').status_code == 200)

# ---- review with photo upload ----
rv = c.post(f'/restaurant/{sg_id}/review', data={'content': 'Lovely biryani, great service!', 'stars': '5', 'photo': (png_bytes(), 'meal.png')},
            content_type='multipart/form-data', follow_redirects=True)
check('review with photo posted', b'Review posted successfully' in rv.data)
with app.app_context():
    new_rev = Review.query.filter_by(content='Lovely biryani, great service!').first()
    check('review stored with rating', new_rev is not None and Rating.query.filter_by(restaurant_id=sg_id, stars=5).count() == 1)
    rid = new_rev.id
rd = c.get(f'/restaurant/{sg_id}').get_data(as_text=True)
up = re.findall(r'src="(/uploads/[^"]+)"', rd)
check('uploaded review photo shown and served', bool(up) and c.get(up[0]).status_code == 200, up)
cm = c.post(f'/review/{rid}/comment', json={'content': 'Agree!'}, follow_redirects=True)
check('comment posted', cm.status_code in (200, 201), cm.status_code)
rc = c.post(f'/review/{rid}/react', json={'type': 'like'})
check('reaction (like) works', rc.status_code == 200, rc.status_code)

# ---- add restaurant with cover upload; menu item with upload ----
ar = c.post('/restaurants/add', data={'name': 'Test Bistro', 'cuisine_type': 'Cafe', 'price_range': '$$', 'address': 'Test Road',
            'cover_photo': (png_bytes(), 'cover.png')}, content_type='multipart/form-data', follow_redirects=False)
check('add restaurant with cover photo', ar.status_code in (302, 200), ar.status_code)
with app.app_context():
    tb = Restaurant.query.filter_by(name='Test Bistro').first()
    check('new restaurant saved with uploads/ cover', tb is not None and (tb.cover_image or '').startswith('uploads/'), getattr(tb, 'cover_image', None))
    tb_id = tb.id
page = c.get(f'/restaurant/{tb_id}').get_data(as_text=True)
src = re.findall(r'class="detail-hero".*?<img src="([^"]+)"', page, re.S) or re.findall(r'<img src="(/uploads/[^"]+)"', page)
check('uploaded restaurant cover served', bool(src) and c.get(src[0]).status_code == 200, src)
ar2 = c.post('/restaurants/add', data={'name': 'No Photo Place', 'cuisine_type': 'Korean', 'price_range': '$', 'address': 'Somewhere'}, follow_redirects=False)
with app.app_context():
    npp = Restaurant.query.filter_by(name='No Photo Place').first()
    nid = npp.id
r = c.get(f'/restaurant/{nid}')
check('restaurant without photo renders with neutral fallback (no broken layout)', r.status_code == 200 and b'photo-unavailable.jpg' in r.data)
mi = c.post(f'/restaurant/{sg_id}/menu/add', data={'name': 'Test Dish', 'price': '123', 'category': 'Main Course', 'description': 'x',
            'image_file': (png_bytes(), 'dish.png')}, content_type='multipart/form-data', follow_redirects=True)
with app.app_context():
    td = FoodItem.query.filter_by(name='Test Dish').first()
    check('menu item with image upload saved', td is not None and (td.image_path or '').startswith('uploads/'), getattr(td, 'image_path', None))
bad_up = c.post(f'/restaurant/{sg_id}/review', data={'content': 'x', 'stars': '3', 'photo': (io.BytesIO(b'<svg></svg>'), 'evil.svg')},
                content_type='multipart/form-data', follow_redirects=True)
check('SVG/non-image upload rejected', b'must be PNG' in bad_up.data)

lo = c.get('/logout', follow_redirects=False)
check('logout redirects', lo.status_code == 302)
check('dashboard blocked after logout', c.get('/dashboard', follow_redirects=False).status_code in (302, 401))
check('review blocked when logged out', c.post(f'/restaurant/{sg_id}/review', data={'content': 'x', 'stars': '3'}).status_code == 302)

failed = [r for r in results if not r[1]]
print(f'\n{len(results) - len(failed)} passed, {len(failed)} failed, of {len(results)} checks')
sys.exit(1 if failed else 0)
