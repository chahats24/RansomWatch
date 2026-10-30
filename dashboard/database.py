import sqlite3

from pathlib import Path

DATABASE = str(
    Path(__file__).resolve().parent.parent / "data" / "ransomwatch.db"
)


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():
    conn = get_connection()

    with open("schema.sql", "r") as file:
        schema = file.read()

    conn.executescript(schema)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_database()
    print("Database created successfully!")