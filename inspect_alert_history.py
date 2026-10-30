
import sqlite3

connection = sqlite3.connect("data/ransomwatch.db")

rows = connection.execute("""
    SELECT id, timestamp, files_changed, renames,
           extension_changes, anomaly_score, message
    FROM alerts
    ORDER BY id DESC
""").fetchall()

print("Total alerts:", len(rows))

for row in rows:
    print(row)

connection.close()
