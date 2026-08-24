import sqlite3
conn = sqlite3.connect('swiply.db')
cursor = conn.cursor()
cursor.execute("DELETE FROM swipes WHERE candidate_id = 'demo-candidate'")
conn.commit()
print("Deleted", cursor.rowcount, "rows from swipes")
