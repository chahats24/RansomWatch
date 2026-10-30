import sqlite3
from datetime import datetime
import os

DB_PATH = "data/ransomwatch.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_database():
    os.makedirs("data", exist_ok=True)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            event_type TEXT,
            file_path TEXT,
            old_path TEXT,
            new_path TEXT,
            old_extension TEXT,
            new_extension TEXT,
            hash_before TEXT,
            hash_after TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            files_changed INTEGER,
            renames INTEGER,
            extension_changes INTEGER,
            anomaly_score REAL,
            message TEXT
        )
    """)

    # Add the entropy column to older databases (safe to run repeatedly)
    cursor.execute("PRAGMA table_info(events)")
    columns = [row[1] for row in cursor.fetchall()]
    if "entropy" not in columns:
        cursor.execute("ALTER TABLE events ADD COLUMN entropy REAL")

    connection.commit()
    connection.close()


def log_event(
    event_type,
    file_path,
    old_path="",
    new_path="",
    old_extension="",
    new_extension="",
    hash_before="",
    hash_after="",
    entropy=None
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO events (
            timestamp,
            event_type,
            file_path,
            old_path,
            new_path,
            old_extension,
            new_extension,
            hash_before,
            hash_after,
            entropy
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        event_type,
        file_path,
        old_path,
        new_path,
        old_extension,
        new_extension,
        hash_before,
        hash_after,
        entropy
    ))

    connection.commit()
    connection.close()


def log_alert(
    files_changed,
    renames,
    extension_changes,
    anomaly_score,
    message
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO alerts (
            timestamp,
            files_changed,
            renames,
            extension_changes,
            anomaly_score,
            message
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        files_changed,
        renames,
        extension_changes,
        anomaly_score,
        message
    ))

    connection.commit()
    connection.close()


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")