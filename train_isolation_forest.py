import sqlite3
import pandas as pd
import os
import joblib

from sklearn.ensemble import IsolationForest


DB_PATH = "data/ransomwatch.db"
MODEL_PATH = "models/isolation_forest.pkl"



def load_normal_events():
    connection = sqlite3.connect(DB_PATH)
    try:
        query = """
            SELECT timestamp, event_type, file_path,
                   old_extension, new_extension
            FROM events
            WHERE file_path NOT LIKE '%attack_test%'
              AND file_path NOT LIKE '%demo_%'
              AND file_path NOT LIKE '%.locked'
            ORDER BY timestamp
        """
        df = pd.read_sql_query(query, connection)
    finally:
        connection.close()

    return df



def create_normal_features(window_seconds=5):
    df = load_normal_events()

    if df.empty:
        print("No normal events found.")
        return pd.DataFrame()

    df["timestamp"] = pd.to_datetime(
        df["timestamp"], format="ISO8601"
    )
    df = df.sort_values("timestamp")

    df["window"] = df["timestamp"].dt.floor(
        f"{window_seconds}s"
    )

   
    df["extension_changed"] = (
        (df["event_type"] == "renamed") &
        (
            df["old_extension"].fillna("") !=
            df["new_extension"].fillna("")
        )
    )

    grouped = df.groupby("window")

    features = grouped.agg(
        files_changed=("file_path", "nunique"),
        renames=(
            "event_type",
            lambda x: (x == "renamed").sum()
        ),
        extension_changes=("extension_changed", "sum")
    ).reset_index()

    for column in [
        "files_changed", "renames", "extension_changes"
    ]:
        features[column] = features[column].astype(int)

    return features



def main():
    print()
    print("==========================================")
    print("   RANSOMWATCH ISOLATION FOREST TRAINING")
    print("==========================================")
    print()

    features = create_normal_features()

    if features.empty:
        print("Training stopped.")
        return

    print("Normal training windows:", len(features))
    print()
    print(features.to_string(index=False))
    print()

    X = features[
        [
            "files_changed",
            "renames",
            "extension_changes"
        ]
    ]

    model = IsolationForest(
        n_estimators=100,
        contamination=0.02,
        random_state=42
    )

    model.fit(X)

    predictions = model.predict(X)

    normal_count = (predictions == 1).sum()
    anomaly_count = (predictions == -1).sum()

    print()
    print("Training completed!")
    print()
    print("Normal samples :", normal_count)
    print("Anomaly samples:", anomaly_count)

    os.makedirs("models", exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print()
    print("Isolation Forest model saved successfully!")
    print("Location:", MODEL_PATH)
    print()
    print("==========================================")


if __name__ == "__main__":
    main()
