from database import get_connection
from datetime import datetime, timedelta
import random


def insert_dummy_data():
    conn = get_connection()
    cursor = conn.cursor()

    # Clear old dummy data
    cursor.execute("DELETE FROM events")
    cursor.execute("DELETE FROM alerts")

    # Sample files
    files = [
        ("report.docx", ".docx"),
        ("photo.jpg", ".jpg"),
        ("notes.txt", ".txt"),
        ("presentation.pptx", ".pptx"),
        ("data.xlsx", ".xlsx"),
        ("project.pdf", ".pdf"),
        ("image.png", ".png")
    ]

    event_types = ["CREATE", "MODIFY", "DELETE", "RENAME"]

    start_time = datetime.now() - timedelta(minutes=30)

    # Insert normal events
    for i in range(30):
        filename, extension = random.choice(files)
        event_type = random.choice(event_types)

        timestamp = (
            start_time + timedelta(seconds=i * 40)
        ).strftime("%Y-%m-%d %H:%M:%S")

        fake_hash = "".join(
            random.choices("0123456789abcdef", k=64)
        )

        cursor.execute("""
            INSERT INTO events
            (timestamp, filename, event_type, file_extension, file_hash)
            VALUES (?, ?, ?, ?, ?)
        """, (
            timestamp,
            filename,
            event_type,
            extension,
            fake_hash
        ))

    # Insert a few suspicious alerts
    alerts = [
        (42, 18, 15, -0.72, "SUSPICIOUS"),
        (35, 12, 10, -0.65, "SUSPICIOUS"),
        (28, 8, 7, -0.51, "SUSPICIOUS")
    ]

    for i, alert in enumerate(alerts):
        timestamp = (
            datetime.now() - timedelta(minutes=i * 5)
        ).strftime("%Y-%m-%d %H:%M:%S")

        files_changed, renames, extension_changes, score, status = alert

        cursor.execute("""
            INSERT INTO alerts
            (timestamp, files_changed, renames,
             extension_changes, anomaly_score, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            files_changed,
            renames,
            extension_changes,
            score,
            status
        ))

    conn.commit()
    conn.close()

    print("Dummy data inserted successfully!")


if __name__ == "__main__":
    insert_dummy_data()