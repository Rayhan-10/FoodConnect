from app import app
from models import db, Restaurant, Location, FoodItem
from app import upgrade_local_schema


def local_food_asset(food_name):
    name = (food_name or '').lower()
    rules = [
        (('biryani', 'polao', 'tehari'), 'biryani.svg'),
        (('sushi', 'nigiri', 'roll'), 'sushi.svg'),
        (('burger', 'hot dog', 'sandwich'), 'burger.svg'),
        (('pasta', 'lasagna', 'risotto'), 'pasta.svg'),
        (('pizza',), 'pizza.svg'),
        (('mezban', 'bhuna', 'kacchi'), 'mezban.svg'),
        (('fish', 'prawn', 'seafood', 'squid'), 'grilled-fish.svg'),
        (('noodle', 'chow mein', 'yakisoba'), 'noodles.svg'),
        (('dumpling', 'gyoza', 'spring roll'), 'dumplings.svg'),
        (('taco', 'burrito', 'quesadilla'), 'tacos.svg'),
        (('bibimbap', 'kimchi', 'korean'), 'bibimbap.svg'),
        (('coffee', 'latte', 'cappuccino', 'americano', 'frappe'), 'coffee.svg'),
        (('salad', 'avocado'), 'salad.svg'),
        (('chicken', 'curry', 'paneer', 'dal'), 'curry.svg'),
    ]
    for words, filename in rules:
        if any(word in name for word in words):
            return f'images/food/{filename}'
    return 'images/food/curry.svg'


def sample_dietary_tags(food_name):
    name = (food_name or '').lower()
    vegetarian_terms = ('paneer', 'dal ', 'masala dosa', 'chana', 'fries', 'salad', 'avocado',
                        'pancake', 'latte', 'coffee', 'americano', 'muffin', 'cheesecake',
                        'margherita', 'garlic bread', 'risotto', 'guacamole', 'mango', 'fruit')
    vegan_terms = ('avocado', 'guacamole', 'salad', 'fries', 'chana masala', 'dal tadka')
    tags = []
    if any(term in name for term in vegetarian_terms):
        tags.append('Vegetarian')
    if any(term in name for term in vegan_terms):
        tags.append('Vegan')
    return ','.join(tags)


def local_restaurant_asset(cuisine):
    mapping = {
        'Indian': 'indian.svg', 'Japanese': 'japanese.svg', 'Fast Food': 'fast-food.svg',
        'Italian': 'italian.svg', 'Bangladeshi': 'bangladeshi.svg', 'Cafe': 'cafe.svg',
        'Chinese': 'chinese.svg', 'Mexican': 'mexican.svg', 'Korean': 'korean.svg',
        'Seafood': 'seafood.svg',
    }
    return f"images/restaurants/{mapping.get(cuisine, 'bangladeshi.svg')}"


sample_restaurants = [
    {"name": "Spice Garden", "cuisine_type": "Indian", "price_range": "$$", "lat": 22.3569, "lng": 91.7832, "address": "GEC Circle, Chattogram"},
    {"name": "Sushi Wave", "cuisine_type": "Japanese", "price_range": "$$$", "lat": 22.3600, "lng": 91.7900, "address": "Agrabad, Chattogram"},
    {"name": "Burger Hub", "cuisine_type": "Fast Food", "price_range": "$", "lat": 22.3500, "lng": 91.7800, "address": "Nasirabad, Chattogram"},
    {"name": "Pasta Palace", "cuisine_type": "Italian", "price_range": "$$", "lat": 22.3650, "lng": 91.7950, "address": "Khulshi, Chattogram"},
    {"name": "Dhaka Biriyani House", "cuisine_type": "Bangladeshi", "price_range": "$", "lat": 22.3450, "lng": 91.7750, "address": "Chawkbazar, Chattogram"},
    {"name": "Green Leaf Cafe", "cuisine_type": "Cafe", "price_range": "$$", "lat": 22.3550, "lng": 91.7850, "address": "CDA Avenue, Chattogram"},
    {"name": "Golden Dragon", "cuisine_type": "Chinese", "price_range": "$$", "lat": 22.3480, "lng": 91.7920, "address": "Panchlaish, Chattogram"},
    {"name": "Taco Fiesta", "cuisine_type": "Mexican", "price_range": "$$", "lat": 22.3620, "lng": 91.7770, "address": "Halishahar, Chattogram"},
    {"name": "Mezban House", "cuisine_type": "Bangladeshi", "price_range": "$$", "lat": 22.3574, "lng": 91.8123, "address": "Anderkilla, Chattogram"},
    {"name": "The Coffee Atelier", "cuisine_type": "Cafe", "price_range": "$", "lat": 22.3591, "lng": 91.8020, "address": "Nasirabad, Chattogram"},
    {"name": "Seoul Kitchen", "cuisine_type": "Korean", "price_range": "$$$", "lat": 22.3632, "lng": 91.7891, "address": "Khulshi, Chattogram"},
    {"name": "Coastal Grill", "cuisine_type": "Seafood", "price_range": "$$$", "lat": 22.3488, "lng": 91.8064, "address": "Patenga, Chattogram"},
]



# Illustrative sample menu for the local demo. Prices/images are demo data, not verified restaurant menus.
sample_foods_by_restaurant = {
    "Spice Garden": [("Chicken Biryani", 280, "Rice & Biryani", "Aromatic rice with chicken and spices.", ""), ("Butter Chicken", 360, "Main Course", "Creamy tomato curry with tender chicken.", ""), ("Garlic Naan", 90, "Snacks & Starters", "Soft naan with garlic and herbs.", "")],
    "Sushi Wave": [("Salmon Sushi Roll", 520, "Main Course", "A fresh salmon roll for sushi lovers.", ""), ("Chicken Teriyaki Bowl", 390, "Main Course", "Teriyaki chicken served with rice.", ""), ("Miso Soup", 150, "Snacks & Starters", "A warm and light Japanese soup.", "")],
    "Burger Hub": [("Classic Beef Burger", 250, "Fast Food", "Beef patty, lettuce and house sauce.", ""), ("Crispy Chicken Burger", 220, "Fast Food", "Crunchy chicken with fresh vegetables.", ""), ("French Fries", 100, "Snacks & Starters", "Golden fries with a light seasoning.", "")],
    "Pasta Palace": [("Creamy Alfredo Pasta", 350, "Main Course", "Pasta in a creamy sauce.", ""), ("Margherita Pizza", 420, "Fast Food", "Tomato, cheese and basil on a crisp base.", ""), ("Tiramisu", 180, "Dessert", "A coffee-flavoured layered dessert.", "")],
    "Dhaka Biriyani House": [("Kacchi Biryani", 320, "Rice & Biryani", "Traditional-style biryani with fragrant rice.", ""), ("Beef Tehari", 240, "Rice & Biryani", "Spiced rice cooked with beef.", ""), ("Borhani", 70, "Drinks", "A chilled spiced yogurt drink.", "")],
    "Green Leaf Cafe": [("Avocado Toast", 280, "Vegetarian", "Toast topped with avocado and herbs.", ""), ("Pancake Stack", 240, "Dessert", "Fluffy pancakes with a sweet topping.", ""), ("Iced Latte", 180, "Drinks", "Espresso with chilled milk.", "")],
    "Golden Dragon": [("Chicken Chow Mein", 260, "Main Course", "Stir-fried noodles with chicken and vegetables.", ""), ("Fried Rice", 220, "Main Course", "Wok-fried rice with vegetables.", ""), ("Spring Rolls", 140, "Snacks & Starters", "Crisp rolls with a savoury filling.", "")],
    "Taco Fiesta": [("Beef Tacos", 260, "Fast Food", "Tacos with seasoned beef and salsa.", "")],
    "Mezban House": [("Beef Mezban", 350, "Main Course", "Spicy beef curry inspired by Chattogram cuisine.", ""), ("Plain Rice", 70, "Main Course", "Steamed rice served with curry.", ""), ("Lassi", 120, "Drinks", "A chilled yogurt drink.", "")],
    "The Coffee Atelier": [("Cappuccino", 180, "Drinks", "Espresso with steamed milk foam.", ""), ("Chocolate Brownie", 150, "Dessert", "A rich chocolate square.", ""), ("Chicken Sandwich", 220, "Fast Food", "Toasted sandwich with chicken filling.", "")],
    "Seoul Kitchen": [("Bibimbap", 420, "Main Course", "Rice bowl with vegetables and sauce.", ""), ("Korean Fried Chicken", 450, "Main Course", "Crispy chicken with a sweet-spicy glaze.", ""), ("Kimchi Fried Rice", 320, "Rice & Biryani", "Fried rice with tangy kimchi.", "")],
    "Coastal Grill": [("Grilled Fish", 520, "Seafood", "Grilled fish with herbs and lemon.", ""), ("Prawn Masala", 480, "Seafood", "Prawns cooked in a spiced sauce.", ""), ("Fish and Chips", 390, "Seafood", "Crispy fish served with fries.", "")],
}

# Additional cuisine-matched dishes used to bring every demo restaurant to 10 menu items.
# Prices and image links are illustrative demo data, not official restaurant menus.
extra_foods_by_restaurant = {
    "Spice Garden": [
        ("Paneer Tikka", 260, "Snacks & Starters", "Grilled paneer with Indian spices.", ""),
        ("Palak Paneer", 290, "Main Course", "Paneer cooked in a spinach curry.", ""),
        ("Dal Tadka", 180, "Main Course", "Yellow lentils tempered with spices.", ""),
        ("Chicken Tikka", 320, "Snacks & Starters", "Marinated chicken grilled in tandoor style.", ""),
        ("Masala Dosa", 190, "Breakfast", "Crisp dosa with spiced potato filling.", ""),
        ("Chana Masala", 210, "Main Course", "Chickpeas simmered in a spiced tomato gravy.", ""),
        ("Gulab Jamun", 110, "Dessert", "Soft milk dumplings in sweet syrup.", ""),
    ],
    "Sushi Wave": [
        ("California Roll", 380, "Main Course", "Sushi roll with avocado and cucumber.", ""),
        ("Tempura Prawns", 420, "Snacks & Starters", "Crispy Japanese-style battered prawns.", ""),
        ("Chicken Katsu", 390, "Main Course", "Breaded chicken cutlet with rice.", ""),
        ("Salmon Nigiri", 460, "Main Course", "Sliced salmon served over seasoned rice.", ""),
        ("Vegetable Gyoza", 220, "Snacks & Starters", "Japanese pan-fried vegetable dumplings.", ""),
        ("Chicken Yakisoba", 340, "Main Course", "Japanese stir-fried noodles with chicken.", ""),
        ("Matcha Ice Cream", 160, "Dessert", "Green tea flavoured ice cream.", ""),
    ],
    "Burger Hub": [
        ("Double Cheese Burger", 320, "Fast Food", "Double beef patty with melted cheese.", ""),
        ("BBQ Chicken Burger", 260, "Fast Food", "Grilled chicken with smoky BBQ sauce.", ""),
        ("Chicken Nuggets", 160, "Snacks & Starters", "Crispy bite-sized chicken pieces.", ""),
        ("Onion Rings", 120, "Snacks & Starters", "Golden battered onion rings.", ""),
        ("Hot Dog", 180, "Fast Food", "Sausage in a soft bun with house sauce.", ""),
        ("Loaded Fries", 190, "Snacks & Starters", "Fries topped with cheese and sauce.", ""),
        ("Chocolate Milkshake", 170, "Drinks", "Chilled chocolate milkshake.", ""),
    ],
    "Pasta Palace": [
        ("Spaghetti Bolognese", 380, "Main Course", "Spaghetti with tomato and minced meat sauce.", ""),
        ("Penne Arrabbiata", 320, "Main Course", "Penne pasta in a spicy tomato sauce.", ""),
        ("Four Cheese Pizza", 490, "Fast Food", "Pizza topped with four kinds of cheese.", ""),
        ("Garlic Bread", 140, "Snacks & Starters", "Toasted bread with garlic butter.", ""),
        ("Lasagna", 420, "Main Course", "Baked pasta layered with sauce and cheese.", ""),
        ("Mushroom Risotto", 360, "Main Course", "Creamy Italian rice with mushrooms.", ""),
        ("Lemon Soda", 100, "Drinks", "Refreshing lemon soda.", ""),
    ],
    "Dhaka Biriyani House": [
        ("Chicken Biryani", 220, "Rice & Biryani", "Fragrant rice cooked with spiced chicken.", ""),
        ("Morog Polao", 260, "Rice & Biryani", "Bangladeshi chicken pilaf with aromatic rice.", ""),
        ("Beef Khichuri", 250, "Rice & Biryani", "Comforting rice and lentils served with beef.", ""),
        ("Chicken Roast", 180, "Main Course", "Bengali-style roast chicken.", ""),
        ("Egg Korma", 130, "Main Course", "Boiled eggs in a mild spiced gravy.", ""),
        ("Jali Kebab", 100, "Snacks & Starters", "Bangladeshi minced meat kebab.", ""),
        ("Firni", 90, "Dessert", "Traditional chilled rice pudding.", ""),
    ],
    "Green Leaf Cafe": [
        ("Grilled Vegetable Sandwich", 210, "Fast Food", "Toasted sandwich with grilled vegetables.", ""),
        ("Caesar Salad", 260, "Vegetarian", "Fresh salad with creamy dressing.", ""),
        ("Blueberry Cheesecake", 220, "Dessert", "Creamy cheesecake with blueberry topping.", ""),
        ("Americano", 140, "Drinks", "Espresso diluted with hot water.", ""),
        ("Chicken Pasta Salad", 290, "Main Course", "Pasta salad with chicken and greens.", ""),
        ("Chocolate Muffin", 120, "Dessert", "Soft chocolate muffin baked fresh.", ""),
        ("Mango Smoothie", 190, "Drinks", "Smooth mango blended with milk.", ""),
    ],
    "Golden Dragon": [
        ("Sweet and Sour Chicken", 320, "Main Course", "Crispy chicken with sweet and sour sauce.", ""),
        ("Beef with Broccoli", 350, "Main Course", "Stir-fried beef with broccoli.", ""),
        ("Hot and Sour Soup", 150, "Snacks & Starters", "Chinese soup with a tangy spicy flavour.", ""),
        ("Chicken Manchurian", 300, "Main Course", "Chicken tossed in a savoury Indo-Chinese sauce.", ""),
        ("Chilli Garlic Noodles", 240, "Main Course", "Noodles tossed with garlic and chilli.", ""),
        ("Steamed Dumplings", 200, "Snacks & Starters", "Steamed dumplings with savoury filling.", ""),
        ("Mango Pudding", 130, "Dessert", "Chilled mango-flavoured pudding.", ""),
    ],
    "Taco Fiesta": [
        ("Chicken Tacos", 230, "Fast Food", "Seasoned chicken tacos with salsa.", ""),
        ("Cheese Quesadilla", 250, "Snacks & Starters", "Grilled tortilla filled with melted cheese.", ""),
        ("Chicken Burrito", 320, "Main Course", "Tortilla wrap with chicken, rice and beans.", ""),
        ("Beef Nachos", 280, "Snacks & Starters", "Tortilla chips topped with beef and cheese.", ""),
        ("Chicken Fajitas", 350, "Main Course", "Sizzling chicken with peppers and onions.", ""),
        ("Mexican Rice Bowl", 260, "Main Course", "Rice bowl with beans, corn and salsa.", ""),
        ("Churros", 150, "Dessert", "Fried dough sticks with cinnamon sugar.", ""),
        ("Guacamole and Chips", 180, "Snacks & Starters", "Avocado dip served with tortilla chips.", ""),
        ("Horchata", 120, "Drinks", "Sweet cinnamon rice drink.", ""),
    ],
    "Mezban House": [
        ("Kala Bhuna", 320, "Main Course", "Chattogram-style slow-cooked dark beef curry.", ""),
        ("Mezban Beef with Rice", 390, "Rice & Biryani", "Spiced beef curry served with steamed rice.", ""),
        ("Chattogram Beef Bhuna", 330, "Main Course", "Local-style beef bhuna with aromatic spices.", ""),
        ("Dal Bhorta", 90, "Sides", "Traditional mashed lentils with seasoning.", ""),
        ("Aloo Bhorta", 70, "Sides", "Mashed potato with chilli and onion.", ""),
        ("Beef Chap", 220, "Snacks & Starters", "Spiced pressed beef cutlet.", ""),
        ("Paratha", 40, "Sides", "Flaky flatbread served warm.", ""),
    ],
    "The Coffee Atelier": [
        ("Flat White", 190, "Drinks", "Espresso with velvety steamed milk.", ""),
        ("Caramel Macchiato", 220, "Drinks", "Espresso, steamed milk and caramel.", ""),
        ("Blueberry Muffin", 130, "Dessert", "Soft muffin with blueberries.", ""),
        ("Club Sandwich", 260, "Fast Food", "Layered sandwich with chicken and vegetables.", ""),
        ("Chicken Panini", 280, "Fast Food", "Pressed sandwich with chicken and cheese.", ""),
        ("Vanilla Frappe", 230, "Drinks", "Blended iced coffee with vanilla.", ""),
        ("Waffles with Honey", 210, "Dessert", "Golden waffles served with honey.", ""),
    ],
    "Seoul Kitchen": [
        ("Bulgogi Beef Bowl", 460, "Main Course", "Korean marinated beef served with rice.", ""),
        ("Tteokbokki", 280, "Snacks & Starters", "Korean rice cakes in a spicy sauce.", ""),
        ("Japchae", 330, "Main Course", "Korean glass noodles with vegetables.", ""),
        ("Kimchi Pancake", 250, "Snacks & Starters", "Savoury pancake with kimchi.", ""),
        ("Korean Corn Dogs", 220, "Fast Food", "Crispy Korean-style corn dogs.", ""),
        ("Jajangmyeon", 350, "Main Course", "Noodles with Korean black bean sauce.", ""),
        ("Hotteok", 140, "Dessert", "Korean sweet pancake with cinnamon filling.", ""),
    ],
    "Coastal Grill": [
        ("Grilled Prawns", 490, "Seafood", "Prawns grilled with garlic and lemon.", ""),
        ("Fish Curry with Rice", 420, "Seafood", "Fish curry served with steamed rice.", ""),
        ("Garlic Butter Calamari", 450, "Seafood", "Tender calamari with garlic butter.", ""),
        ("Lemon Herb Salmon", 590, "Seafood", "Salmon fillet with lemon and herbs.", ""),
        ("Prawn Fried Rice", 380, "Main Course", "Fried rice with prawns and vegetables.", ""),
        ("Seafood Chowder", 280, "Snacks & Starters", "Creamy soup with seafood.", ""),
        ("Grilled Squid", 430, "Seafood", "Grilled squid with a light spice rub.", ""),
    ],
}

with app.app_context():
    db.create_all()
    upgrade_local_schema()

    added_count = 0
    for r in sample_restaurants:
        existing = Restaurant.query.filter_by(name=r["name"]).first()
        if existing:
            continue
        restaurant = Restaurant(
            name=r["name"],
            cuisine_type=r["cuisine_type"],
            price_range=r["price_range"],
            cover_image=local_restaurant_asset(r["cuisine_type"])
        )
        db.session.add(restaurant)
        db.session.flush()
        db.session.add(Location(
            restaurant_id=restaurant.id,
            latitude=r["lat"], longitude=r["lng"], address=r["address"]
        ))
        added_count += 1
    db.session.commit()

    added_foods = 0
    for restaurant_name, base_dishes in sample_foods_by_restaurant.items():
        restaurant = Restaurant.query.filter_by(name=restaurant_name).first()
        if not restaurant:
            continue
        existing_names = {name.casefold() for (name,) in db.session.query(FoodItem.name).filter_by(restaurant_id=restaurant.id).all()}
        combined = list(base_dishes) + extra_foods_by_restaurant.get(restaurant_name, [])
        for food_name, price, category, description, image_path in combined:
            if food_name.casefold() in existing_names:
                continue
            # Ensure every seeded demo restaurant has at least 10 distinct dishes.
            current_count = FoodItem.query.filter_by(restaurant_id=restaurant.id).count()
            if current_count >= 10:
                break
            db.session.add(FoodItem(
                restaurant_id=restaurant.id, name=food_name, price=price,
                category=category, description=description,
                image_path=local_food_asset(food_name), dietary_tags=sample_dietary_tags(food_name), is_available=True
            ))
            existing_names.add(food_name.casefold())
            added_foods += 1
        db.session.flush()

    db.session.commit()
    # Convert previously seeded external demo image URLs to stable local assets.
    repaired_food_images = 0
    for item in FoodItem.query.all():
        if not item.image_path or item.image_path.startswith(('http://', 'https://')):
            item.image_path = local_food_asset(item.name)
            repaired_food_images += 1

    for item in FoodItem.query.all():
        if not item.dietary_tags:
            item.dietary_tags = sample_dietary_tags(item.name)

    repaired_restaurant_images = 0
    for place in Restaurant.query.all():
        if not place.cover_image or place.cover_image.startswith(('http://', 'https://')) or place.cover_image == 'default_restaurant.jpg':
            place.cover_image = local_restaurant_asset(place.cuisine_type)
            repaired_restaurant_images += 1

    db.session.commit()
    print(f'Added {added_count} new restaurants. Total sample restaurants: {Restaurant.query.count()}. Existing restaurants were kept.')
    print(f'Added {added_foods} demo menu items. Seeded demo restaurants now have at least 10 items when enough unique sample dishes are defined.')
    print(f'Converted {repaired_food_images} food images and {repaired_restaurant_images} restaurant covers to local assets.')
    print('Prices and photos are illustrative demo data, not verified official restaurant menus.')
