
import sqlite3
import pandas as pd


DB_PATH = "data/ransomwatch.db"


def load_events():
    """
    Load file-system events from SQLite.
    """

    connection = sqlite3.connect(DB_PATH)

    try:
        query = """
            SELECT
                timestamp,
                event_type,
                file_path,
                old_extension,
                new_extension
            FROM events
            ORDER BY timestamp
        """

        df = pd.read_sql_query(query, connection)

    finally:
        connection.close()

    return df


def create_features(window_seconds=5):
    """
    Convert raw file events into short-window features.

    Features:
        - files_changed
        - renames
        - extension_changes
    """

    df = load_events()

    if df.empty:
        print("No events found in database.")
        return pd.DataFrame(
            columns=[
                "window",
                "files_changed",
                "renames",
                "extension_changes"
            ]
        )

    # Convert timestamp column to datetime
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        format="ISO8601"
    )

    # Sort events chronologically
    df = df.sort_values("timestamp")

    # Create time windows
    df["window"] = (
        df["timestamp"]
        .dt.floor(f"{window_seconds}s")
    )

    # Identify actual file-extension changes
    df["extension_changed"] = (
        (df["event_type"] == "renamed") &
        (
            df["old_extension"].fillna("") !=
            df["new_extension"].fillna("")
        )
    )

    # Group events by time window
    grouped = df.groupby("window")

    features = grouped.agg(
        files_changed=("file_path", "nunique"),
        renames=(
            "event_type",
            lambda x: (x == "renamed").sum()
        ),
        extension_changes=(
            "extension_changed",
            "sum"
        )
    ).reset_index()

    # Convert feature counts to integers
    features["files_changed"] = (
        features["files_changed"].astype(int)
    )

    features["renames"] = (
        features["renames"].astype(int)
    )

    features["extension_changes"] = (
        features["extension_changes"].astype(int)
    )

    return features


if __name__ == "__main__":

    print("\n========== RANSOMWATCH FEATURES ==========\n")

    features = create_features(window_seconds=5)

    if not features.empty:

        print(features.to_string(index=False))

        print("\n==========================================")
        print(f"Number of windows: {len(features)}")
