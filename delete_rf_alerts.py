
import sqlite3

DB_PATH = "data/ransomwatch.db"

connection = sqlite3.connect(DB_PATH)

try:
    cursor = connection.execute("""
        DELETE FROM alerts
        WHERE id IN (12, 13, 14)
          AND message LIKE 'Ransomware-like activity (RF model):%'
    """)

    connection.commit()
    print(f"Deleted {cursor.rowcount} RF alerts.")

    remaining = connection.execute("""
        SELECT id, timestamp, anomaly_score, message
        FROM alerts
        ORDER BY timestamp DESC
        LIMIT 5
    """).fetchall()

    print("\nLatest remaining alerts:")
    for alert in remaining:
        print(alert)

except Exception:
    connection.rollback()
    raise

finally:
    connection.close()
