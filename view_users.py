import sqlite3

conn = sqlite3.connect('instance/foodconnect.db')
cursor = conn.cursor()

cursor.execute("SELECT id, username, email, is_verified, created_at FROM users")
rows = cursor.fetchall()

print(f"\nTotal users: {len(rows)}\n")
for row in rows:
    print(f"ID: {row[0]} | Username: {row[1]} | Email: {row[2]} | Verified: {row[3]} | Created: {row[4]}")

conn.close()