
import sqlite3

connection = sqlite3.connect("data/ransomwatch.db")

rows = connection.execute("""
    SELECT id, timestamp, anomaly_score, message
    FROM alerts
    WHERE message LIKE 'Ransomware-like activity (RF model):%'
    ORDER BY timestamp DESC
""").fetchall()

print(f"RF alerts found: {len(rows)}")
for row in rows:
    print(row)

connection.close()
