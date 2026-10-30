CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    filename TEXT NOT NULL,
    event_type TEXT NOT NULL,
    file_extension TEXT,
    file_hash TEXT
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    files_changed INTEGER DEFAULT 0,
    renames INTEGER DEFAULT 0,
    extension_changes INTEGER DEFAULT 0,
    anomaly_score REAL,
    status TEXT NOT NULL
);