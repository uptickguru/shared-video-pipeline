import sqlite3
conn = sqlite3.connect('pipeline.db')
cursor = conn.cursor()
cursor.execute("SELECT id, status, prompt FROM jobs")
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row[0]} | Status: {row[1]} | Prompt: {row[2][:50]}...")
conn.close()
