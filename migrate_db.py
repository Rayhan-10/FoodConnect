import sqlite3

DB_PATH = "instance/foodconnect.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(reviews)")
columns = [row[1] for row in cursor.fetchall()]

if "image_path" not in columns:
    cursor.execute("ALTER TABLE reviews ADD COLUMN image_path VARCHAR(255)")
    print("Added image_path column")
else:
    print("image_path already exists")

conn.commit()
conn.close()

print("Database migration finished.")