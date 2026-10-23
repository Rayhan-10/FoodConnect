from app import app
from models import db, Restaurant, Location, FoodItem
from app import upgrade_local_schema

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
    "Spice Garden": [("Chicken Biryani", 280, "Rice & Biryani", "Aromatic rice with chicken and spices.", "https://images.unsplash.com/photo-1563379091339-03246963d96c?auto=format&fit=crop&w=900&q=85"), ("Butter Chicken", 360, "Main Course", "Creamy tomato curry with tender chicken.", "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?auto=format&fit=crop&w=900&q=85"), ("Garlic Naan", 90, "Snacks & Starters", "Soft naan with garlic and herbs.", "https://images.unsplash.com/photo-1610057099431-d73a1c9d2f2f?auto=format&fit=crop&w=900&q=85")],
    "Sushi Wave": [("Salmon Sushi Roll", 520, "Main Course", "A fresh salmon roll for sushi lovers.", "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=900&q=85"), ("Chicken Teriyaki Bowl", 390, "Main Course", "Teriyaki chicken served with rice.", "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=900&q=85"), ("Miso Soup", 150, "Snacks & Starters", "A warm and light Japanese soup.", "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=85")],
    "Burger Hub": [("Classic Beef Burger", 250, "Fast Food", "Beef patty, lettuce and house sauce.", "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=900&q=85"), ("Crispy Chicken Burger", 220, "Fast Food", "Crunchy chicken with fresh vegetables.", "https://images.unsplash.com/photo-1606755962773-d324e0a13086?auto=format&fit=crop&w=900&q=85"), ("French Fries", 100, "Snacks & Starters", "Golden fries with a light seasoning.", "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?auto=format&fit=crop&w=900&q=85")],
    "Pasta Palace": [("Creamy Alfredo Pasta", 350, "Main Course", "Pasta in a creamy sauce.", "https://images.unsplash.com/photo-1473093295043-cdd812d0e601?auto=format&fit=crop&w=900&q=85"), ("Margherita Pizza", 420, "Fast Food", "Tomato, cheese and basil on a crisp base.", "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?auto=format&fit=crop&w=900&q=85"), ("Tiramisu", 180, "Dessert", "A coffee-flavoured layered dessert.", "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?auto=format&fit=crop&w=900&q=85")],
    "Dhaka Biriyani House": [("Kacchi Biryani", 320, "Rice & Biryani", "Traditional-style biryani with fragrant rice.", "https://images.unsplash.com/photo-1563379091339-03246963d96c?auto=format&fit=crop&w=900&q=85"), ("Beef Tehari", 240, "Rice & Biryani", "Spiced rice cooked with beef.", "https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=900&q=85"), ("Borhani", 70, "Drinks", "A chilled spiced yogurt drink.", "https://images.unsplash.com/photo-1544145945-f90425340c7e?auto=format&fit=crop&w=900&q=85")],
    "Green Leaf Cafe": [("Avocado Toast", 280, "Vegetarian", "Toast topped with avocado and herbs.", "https://images.unsplash.com/photo-1525351484163-7529414344d8?auto=format&fit=crop&w=900&q=85"), ("Pancake Stack", 240, "Dessert", "Fluffy pancakes with a sweet topping.", "https://images.unsplash.com/photo-1528207776546-365bb710ee93?auto=format&fit=crop&w=900&q=85"), ("Iced Latte", 180, "Drinks", "Espresso with chilled milk.", "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=900&q=85")],
    "Golden Dragon": [("Chicken Chow Mein", 260, "Main Course", "Stir-fried noodles with chicken and vegetables.", "https://images.unsplash.com/photo-1585032226651-759b368d7246?auto=format&fit=crop&w=900&q=85"), ("Fried Rice", 220, "Main Course", "Wok-fried rice with vegetables.", "https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=900&q=85"), ("Spring Rolls", 140, "Snacks & Starters", "Crisp rolls with a savoury filling.", "https://images.unsplash.com/photo-1548507200-6a7d8e8fcd16?auto=format&fit=crop&w=900&q=85")],
    "Taco Fiesta": [("Beef Tacos", 260, "Fast Food", "Tacos with seasoned beef and salsa.", "https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?auto=format&fit=crop&w=900&q=85")],
    "Mezban House": [("Beef Mezban", 350, "Main Course", "Spicy beef curry inspired by Chattogram cuisine.", "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=85"), ("Plain Rice", 70, "Main Course", "Steamed rice served with curry.", "https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=900&q=85"), ("Lassi", 120, "Drinks", "A chilled yogurt drink.", "https://images.unsplash.com/photo-1544145945-f90425340c7e?auto=format&fit=crop&w=900&q=85")],
    "The Coffee Atelier": [("Cappuccino", 180, "Drinks", "Espresso with steamed milk foam.", "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=900&q=85"), ("Chocolate Brownie", 150, "Dessert", "A rich chocolate square.", "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=900&q=85"), ("Chicken Sandwich", 220, "Fast Food", "Toasted sandwich with chicken filling.", "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=900&q=85")],
    "Seoul Kitchen": [("Bibimbap", 420, "Main Course", "Rice bowl with vegetables and sauce.", "https://images.unsplash.com/photo-1490645935967-10de6ba17061?auto=format&fit=crop&w=900&q=85"), ("Korean Fried Chicken", 450, "Main Course", "Crispy chicken with a sweet-spicy glaze.", "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?auto=format&fit=crop&w=900&q=85"), ("Kimchi Fried Rice", 320, "Rice & Biryani", "Fried rice with tangy kimchi.", "https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=900&q=85")],
    "Coastal Grill": [("Grilled Fish", 520, "Seafood", "Grilled fish with herbs and lemon.", "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?auto=format&fit=crop&w=900&q=85"), ("Prawn Masala", 480, "Seafood", "Prawns cooked in a spiced sauce.", "https://images.unsplash.com/photo-1565680018434-b513d5e5fd47?auto=format&fit=crop&w=900&q=85"), ("Fish and Chips", 390, "Seafood", "Crispy fish served with fries.", "https://images.unsplash.com/photo-1579208575657-c595a05383b7?auto=format&fit=crop&w=900&q=85")],
}

# Additional cuisine-matched dishes used to bring every demo restaurant to 10 menu items.
# Prices and image links are illustrative demo data, not official restaurant menus.
extra_foods_by_restaurant = {
    "Spice Garden": [
        ("Paneer Tikka", 260, "Snacks & Starters", "Grilled paneer with Indian spices.", "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?auto=format&fit=crop&w=900&q=85"),
        ("Palak Paneer", 290, "Main Course", "Paneer cooked in a spinach curry.", "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?auto=format&fit=crop&w=900&q=85"),
        ("Dal Tadka", 180, "Main Course", "Yellow lentils tempered with spices.", "https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=900&q=85"),
        ("Chicken Tikka", 320, "Snacks & Starters", "Marinated chicken grilled in tandoor style.", "https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?auto=format&fit=crop&w=900&q=85"),
        ("Masala Dosa", 190, "Breakfast", "Crisp dosa with spiced potato filling.", "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=900&q=85"),
        ("Chana Masala", 210, "Main Course", "Chickpeas simmered in a spiced tomato gravy.", "https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=900&q=85"),
        ("Gulab Jamun", 110, "Dessert", "Soft milk dumplings in sweet syrup.", "https://images.unsplash.com/photo-1666190092159-5b7f8b2f4a9f?auto=format&fit=crop&w=900&q=85"),
    ],
    "Sushi Wave": [
        ("California Roll", 380, "Main Course", "Sushi roll with avocado and cucumber.", "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=900&q=85"),
        ("Tempura Prawns", 420, "Snacks & Starters", "Crispy Japanese-style battered prawns.", "https://images.unsplash.com/photo-1559737558-2f5a35f4523b?auto=format&fit=crop&w=900&q=85"),
        ("Chicken Katsu", 390, "Main Course", "Breaded chicken cutlet with rice.", "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?auto=format&fit=crop&w=900&q=85"),
        ("Salmon Nigiri", 460, "Main Course", "Sliced salmon served over seasoned rice.", "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=900&q=85"),
        ("Vegetable Gyoza", 220, "Snacks & Starters", "Japanese pan-fried vegetable dumplings.", "https://images.unsplash.com/photo-1563240769-7d4e3b1f4b1d?auto=format&fit=crop&w=900&q=85"),
        ("Chicken Yakisoba", 340, "Main Course", "Japanese stir-fried noodles with chicken.", "https://images.unsplash.com/photo-1585032226651-759b368d7246?auto=format&fit=crop&w=900&q=85"),
        ("Matcha Ice Cream", 160, "Dessert", "Green tea flavoured ice cream.", "https://images.unsplash.com/photo-1501446529957-6226bd447c46?auto=format&fit=crop&w=900&q=85"),
    ],
    "Burger Hub": [
        ("Double Cheese Burger", 320, "Fast Food", "Double beef patty with melted cheese.", "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=900&q=85"),
        ("BBQ Chicken Burger", 260, "Fast Food", "Grilled chicken with smoky BBQ sauce.", "https://images.unsplash.com/photo-1606755962773-d324e0a13086?auto=format&fit=crop&w=900&q=85"),
        ("Chicken Nuggets", 160, "Snacks & Starters", "Crispy bite-sized chicken pieces.", "https://images.unsplash.com/photo-1562967914-608f82629710?auto=format&fit=crop&w=900&q=85"),
        ("Onion Rings", 120, "Snacks & Starters", "Golden battered onion rings.", "https://images.unsplash.com/photo-1639024471283-03518883512d?auto=format&fit=crop&w=900&q=85"),
        ("Hot Dog", 180, "Fast Food", "Sausage in a soft bun with house sauce.", "https://images.unsplash.com/photo-1612392062126-2f1a1f4c6f3d?auto=format&fit=crop&w=900&q=85"),
        ("Loaded Fries", 190, "Snacks & Starters", "Fries topped with cheese and sauce.", "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?auto=format&fit=crop&w=900&q=85"),
        ("Chocolate Milkshake", 170, "Drinks", "Chilled chocolate milkshake.", "https://images.unsplash.com/photo-1572490122747-3968b75cc699?auto=format&fit=crop&w=900&q=85"),
    ],
    "Pasta Palace": [
        ("Spaghetti Bolognese", 380, "Main Course", "Spaghetti with tomato and minced meat sauce.", "https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=900&q=85"),
        ("Penne Arrabbiata", 320, "Main Course", "Penne pasta in a spicy tomato sauce.", "https://images.unsplash.com/photo-1473093295043-cdd812d0e601?auto=format&fit=crop&w=900&q=85"),
        ("Four Cheese Pizza", 490, "Fast Food", "Pizza topped with four kinds of cheese.", "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?auto=format&fit=crop&w=900&q=85"),
        ("Garlic Bread", 140, "Snacks & Starters", "Toasted bread with garlic butter.", "https://images.unsplash.com/photo-1619531040576-f94167406615?auto=format&fit=crop&w=900&q=85"),
        ("Lasagna", 420, "Main Course", "Baked pasta layered with sauce and cheese.", "https://images.unsplash.com/photo-1619895092538-128341789043?auto=format&fit=crop&w=900&q=85"),
        ("Mushroom Risotto", 360, "Main Course", "Creamy Italian rice with mushrooms.", "https://images.unsplash.com/photo-1476124369491-e7addf5db371?auto=format&fit=crop&w=900&q=85"),
        ("Lemon Soda", 100, "Drinks", "Refreshing lemon soda.", "https://images.unsplash.com/photo-1513558161293-ccadaeab8cc7?auto=format&fit=crop&w=900&q=85"),
    ],
    "Dhaka Biriyani House": [
        ("Chicken Biryani", 220, "Rice & Biryani", "Fragrant rice cooked with spiced chicken.", "https://images.unsplash.com/photo-1563379091339-03246963d96c?auto=format&fit=crop&w=900&q=85"),
        ("Morog Polao", 260, "Rice & Biryani", "Bangladeshi chicken pilaf with aromatic rice.", "https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=900&q=85"),
        ("Beef Khichuri", 250, "Rice & Biryani", "Comforting rice and lentils served with beef.", "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=85"),
        ("Chicken Roast", 180, "Main Course", "Bengali-style roast chicken.", "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?auto=format&fit=crop&w=900&q=85"),
        ("Egg Korma", 130, "Main Course", "Boiled eggs in a mild spiced gravy.", "https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=900&q=85"),
        ("Jali Kebab", 100, "Snacks & Starters", "Bangladeshi minced meat kebab.", "https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?auto=format&fit=crop&w=900&q=85"),
        ("Firni", 90, "Dessert", "Traditional chilled rice pudding.", "https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=900&q=85"),
    ],
    "Green Leaf Cafe": [
        ("Grilled Vegetable Sandwich", 210, "Fast Food", "Toasted sandwich with grilled vegetables.", "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=900&q=85"),
        ("Caesar Salad", 260, "Vegetarian", "Fresh salad with creamy dressing.", "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=900&q=85"),
        ("Blueberry Cheesecake", 220, "Dessert", "Creamy cheesecake with blueberry topping.", "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?auto=format&fit=crop&w=900&q=85"),
        ("Americano", 140, "Drinks", "Espresso diluted with hot water.", "https://images.unsplash.com/photo-1517701604599-bb29b565090c?auto=format&fit=crop&w=900&q=85"),
        ("Chicken Pasta Salad", 290, "Main Course", "Pasta salad with chicken and greens.", "https://images.unsplash.com/photo-1473093295043-cdd812d0e601?auto=format&fit=crop&w=900&q=85"),
        ("Chocolate Muffin", 120, "Dessert", "Soft chocolate muffin baked fresh.", "https://images.unsplash.com/photo-1607958996333-41aef7caefaa?auto=format&fit=crop&w=900&q=85"),
        ("Mango Smoothie", 190, "Drinks", "Smooth mango blended with milk.", "https://images.unsplash.com/photo-1505252585461-04db1eb84625?auto=format&fit=crop&w=900&q=85"),
    ],
    "Golden Dragon": [
        ("Sweet and Sour Chicken", 320, "Main Course", "Crispy chicken with sweet and sour sauce.", "https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=900&q=85"),
        ("Beef with Broccoli", 350, "Main Course", "Stir-fried beef with broccoli.", "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=85"),
        ("Hot and Sour Soup", 150, "Snacks & Starters", "Chinese soup with a tangy spicy flavour.", "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=85"),
        ("Chicken Manchurian", 300, "Main Course", "Chicken tossed in a savoury Indo-Chinese sauce.", "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?auto=format&fit=crop&w=900&q=85"),
        ("Chilli Garlic Noodles", 240, "Main Course", "Noodles tossed with garlic and chilli.", "https://images.unsplash.com/photo-1585032226651-759b368d7246?auto=format&fit=crop&w=900&q=85"),
        ("Steamed Dumplings", 200, "Snacks & Starters", "Steamed dumplings with savoury filling.", "https://images.unsplash.com/photo-1563240769-7d4e3b1f4b1d?auto=format&fit=crop&w=900&q=85"),
        ("Mango Pudding", 130, "Dessert", "Chilled mango-flavoured pudding.", "https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=900&q=85"),
    ],
    "Taco Fiesta": [
        ("Chicken Tacos", 230, "Fast Food", "Seasoned chicken tacos with salsa.", "https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?auto=format&fit=crop&w=900&q=85"),
        ("Cheese Quesadilla", 250, "Snacks & Starters", "Grilled tortilla filled with melted cheese.", "https://images.unsplash.com/photo-1618040996337-56904b7850b9?auto=format&fit=crop&w=900&q=85"),
        ("Chicken Burrito", 320, "Main Course", "Tortilla wrap with chicken, rice and beans.", "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=900&q=85"),
        ("Beef Nachos", 280, "Snacks & Starters", "Tortilla chips topped with beef and cheese.", "https://images.unsplash.com/photo-1513456852971-30c0b8199d4d?auto=format&fit=crop&w=900&q=85"),
        ("Chicken Fajitas", 350, "Main Course", "Sizzling chicken with peppers and onions.", "https://images.unsplash.com/photo-1534352956036-cd81e27dd615?auto=format&fit=crop&w=900&q=85"),
        ("Mexican Rice Bowl", 260, "Main Course", "Rice bowl with beans, corn and salsa.", "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=900&q=85"),
        ("Churros", 150, "Dessert", "Fried dough sticks with cinnamon sugar.", "https://images.unsplash.com/photo-1624371414361-e670edf4898d?auto=format&fit=crop&w=900&q=85"),
        ("Guacamole and Chips", 180, "Snacks & Starters", "Avocado dip served with tortilla chips.", "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=900&q=85"),
        ("Horchata", 120, "Drinks", "Sweet cinnamon rice drink.", "https://images.unsplash.com/photo-1544145945-f90425340c7e?auto=format&fit=crop&w=900&q=85"),
    ],
    "Mezban House": [
        ("Kala Bhuna", 320, "Main Course", "Chattogram-style slow-cooked dark beef curry.", "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=85"),
        ("Mezban Beef with Rice", 390, "Rice & Biryani", "Spiced beef curry served with steamed rice.", "https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=900&q=85"),
        ("Chattogram Beef Bhuna", 330, "Main Course", "Local-style beef bhuna with aromatic spices.", "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?auto=format&fit=crop&w=900&q=85"),
        ("Dal Bhorta", 90, "Sides", "Traditional mashed lentils with seasoning.", "https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=900&q=85"),
        ("Aloo Bhorta", 70, "Sides", "Mashed potato with chilli and onion.", "https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=900&q=85"),
        ("Beef Chap", 220, "Snacks & Starters", "Spiced pressed beef cutlet.", "https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?auto=format&fit=crop&w=900&q=85"),
        ("Paratha", 40, "Sides", "Flaky flatbread served warm.", "https://images.unsplash.com/photo-1610057099431-d73a1c9d2f2f?auto=format&fit=crop&w=900&q=85"),
    ],
    "The Coffee Atelier": [
        ("Flat White", 190, "Drinks", "Espresso with velvety steamed milk.", "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=900&q=85"),
        ("Caramel Macchiato", 220, "Drinks", "Espresso, steamed milk and caramel.", "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=900&q=85"),
        ("Blueberry Muffin", 130, "Dessert", "Soft muffin with blueberries.", "https://images.unsplash.com/photo-1607958996333-41aef7caefaa?auto=format&fit=crop&w=900&q=85"),
        ("Club Sandwich", 260, "Fast Food", "Layered sandwich with chicken and vegetables.", "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=900&q=85"),
        ("Chicken Panini", 280, "Fast Food", "Pressed sandwich with chicken and cheese.", "https://images.unsplash.com/photo-1553909489-cd47e0ef937f?auto=format&fit=crop&w=900&q=85"),
        ("Vanilla Frappe", 230, "Drinks", "Blended iced coffee with vanilla.", "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=900&q=85"),
        ("Waffles with Honey", 210, "Dessert", "Golden waffles served with honey.", "https://images.unsplash.com/photo-1562376552-0d160a2f238d?auto=format&fit=crop&w=900&q=85"),
    ],
    "Seoul Kitchen": [
        ("Bulgogi Beef Bowl", 460, "Main Course", "Korean marinated beef served with rice.", "https://images.unsplash.com/photo-1490645935967-10de6ba17061?auto=format&fit=crop&w=900&q=85"),
        ("Tteokbokki", 280, "Snacks & Starters", "Korean rice cakes in a spicy sauce.", "https://images.unsplash.com/photo-1635363638580-c2809d049eee?auto=format&fit=crop&w=900&q=85"),
        ("Japchae", 330, "Main Course", "Korean glass noodles with vegetables.", "https://images.unsplash.com/photo-1585032226651-759b368d7246?auto=format&fit=crop&w=900&q=85"),
        ("Kimchi Pancake", 250, "Snacks & Starters", "Savoury pancake with kimchi.", "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?auto=format&fit=crop&w=900&q=85"),
        ("Korean Corn Dogs", 220, "Fast Food", "Crispy Korean-style corn dogs.", "https://images.unsplash.com/photo-1612392062126-2f1a1f4c6f3d?auto=format&fit=crop&w=900&q=85"),
        ("Jajangmyeon", 350, "Main Course", "Noodles with Korean black bean sauce.", "https://images.unsplash.com/photo-1585032226651-759b368d7246?auto=format&fit=crop&w=900&q=85"),
        ("Hotteok", 140, "Dessert", "Korean sweet pancake with cinnamon filling.", "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=900&q=85"),
    ],
    "Coastal Grill": [
        ("Grilled Prawns", 490, "Seafood", "Prawns grilled with garlic and lemon.", "https://images.unsplash.com/photo-1559737558-2f5a35f4523b?auto=format&fit=crop&w=900&q=85"),
        ("Fish Curry with Rice", 420, "Seafood", "Fish curry served with steamed rice.", "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?auto=format&fit=crop&w=900&q=85"),
        ("Garlic Butter Calamari", 450, "Seafood", "Tender calamari with garlic butter.", "https://images.unsplash.com/photo-1559737558-2f5a35f4523b?auto=format&fit=crop&w=900&q=85"),
        ("Lemon Herb Salmon", 590, "Seafood", "Salmon fillet with lemon and herbs.", "https://images.unsplash.com/photo-1467003909585-2f8a72700288?auto=format&fit=crop&w=900&q=85"),
        ("Prawn Fried Rice", 380, "Main Course", "Fried rice with prawns and vegetables.", "https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=900&q=85"),
        ("Seafood Chowder", 280, "Snacks & Starters", "Creamy soup with seafood.", "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=85"),
        ("Grilled Squid", 430, "Seafood", "Grilled squid with a light spice rub.", "https://images.unsplash.com/photo-1559737558-2f5a35f4523b?auto=format&fit=crop&w=900&q=85"),
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
            price_range=r["price_range"]
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
                image_path=image_path, is_available=True
            ))
            existing_names.add(food_name.casefold())
            added_foods += 1
        db.session.flush()

    db.session.commit()
    # Repair known broken demo image URLs for records that may already exist in the user's database.
    # These are illustrative image URLs; the app still needs internet access to fetch them.
    image_repairs = {
        "Spring Rolls": "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=900&q=85",
        "Steamed Dumplings": "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=900&q=85",
    }
    repaired_food_images = 0
    for food_name, image_url in image_repairs.items():
        item = FoodItem.query.filter(FoodItem.name.ilike(food_name)).first()
        if item:
            item.image_path = image_url
            repaired_food_images += 1

    # Give Golden Dragon a real restaurant-interior photo URL instead of the placeholder.
    golden_dragon = Restaurant.query.filter_by(name="Golden Dragon").first()
    if golden_dragon:
        golden_dragon.cover_image = "https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=1200&q=85"

    db.session.commit()
    print(f'Added {added_count} new restaurants. Total sample restaurants: {Restaurant.query.count()}. Existing restaurants were kept.')
    print(f'Added {added_foods} demo menu items. Seeded demo restaurants now have at least 10 items when enough unique sample dishes are defined.')
    print(f'Repaired image URLs for {repaired_food_images} existing demo food items and updated Golden Dragon cover image.')
    print('Prices and photos are illustrative demo data, not verified official restaurant menus.')
