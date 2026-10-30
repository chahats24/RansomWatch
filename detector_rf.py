import sqlite3
import time
from datetime import datetime, timedelta

import joblib
import pandas as pd

from database import initialize_database, log_alert
from window_features import events_to_windows, WINDOW_SECONDS

DB_PATH = "data/ransomwatch.db"
MODEL_PATH = "models/ransomwatch_rf.pkl"
CHECK_INTERVAL = 2
LOOKBACK_SECONDS = 120
THRESHOLD = 0.5

bundle = joblib.load(MODEL_PATH)
model, FEATS = bundle["model"], bundle["features"]
processed = set()


def recent_events():
    since = (datetime.now() - timedelta(seconds=LOOKBACK_SECONDS)).isoformat()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """SELECT timestamp, event_type, file_path, old_extension,
                  new_extension, entropy
           FROM events WHERE timestamp >= ? ORDER BY timestamp""",
        conn, params=(since,))
    conn.close()
    return df


def detect_once():
    win = events_to_windows(recent_events())
    if win.empty:
        return

    now = datetime.now()
    for _, row in win.iterrows():
        w = pd.Timestamp(row["window"])
        key = str(w)
        # only score windows that are finished
        if key in processed or w + pd.Timedelta(seconds=WINDOW_SECONDS) > now:
            continue
        processed.add(key)

        prob = float(model.predict_proba(pd.DataFrame([row[FEATS]]))[0, 1])
        is_attack = prob >= THRESHOLD

        print(f"[{w}] events={int(row['n_events'])} files={int(row['files_changed'])} "
              f"renames={int(row['renames'])} mean_entropy={row['mean_entropy']:.2f} "
              f"high_entropy={int(row['high_entropy_events'])}  "
              f"P(ransomware)={prob:.2f}  -> {'*** ALERT ***' if is_attack else 'normal'}")

        if is_attack:
            msg = (f"Ransomware-like activity (RF model): {int(row['files_changed'])} files, "
                   f"{int(row['renames'])} renames, {int(row['high_entropy_events'])} "
                   f"high-entropy writes, probability {prob:.2f}.")
            log_alert(
                files_changed=int(row["files_changed"]),
                renames=int(row["renames"]),
                extension_changes=int(row["ext_changes"]),
                anomaly_score=prob,
                message=msg,
            )


if __name__ == "__main__":
    initialize_database()
    # ignore windows that already exist when the detector starts
    for _, r in events_to_windows(recent_events()).iterrows():
        processed.add(str(pd.Timestamp(r["window"])))

    print("RansomWatch RF detector running. Ctrl+C to stop.")
    try:
        while True:
            detect_once()
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("Detector stopped.")
