import sqlite3
conn = sqlite3.connect('swiply.db')
cursor = conn.cursor()
cursor.execute("DELETE FROM swipes WHERE candidate_id = '58906aec-0f24-48f3-8ea5-a570464c3c77'")
conn.commit()
print("Deleted", cursor.rowcount, "rows from swipes")
