import sqlite3
import pandas as pd

from window_features import events_to_windows, FEATURES

DB_PATH = "data/ransomwatch.db"
RUNS_CSV = "data/runs.csv"
OUT_CSV = "data/ransomwatch_dataset.csv"

conn = sqlite3.connect(DB_PATH)
events = pd.read_sql_query(
    """SELECT timestamp, event_type, file_path, old_extension,
              new_extension, entropy
       FROM events ORDER BY timestamp""", conn)
conn.close()

events["timestamp"] = pd.to_datetime(events["timestamp"], format="ISO8601")
runs = pd.read_csv(RUNS_CSV, parse_dates=["start", "end"])

parts = []
for _, r in runs.iterrows():
    ev = events[(events["timestamp"] >= r["start"]) & (events["timestamp"] <= r["end"])]
    win = events_to_windows(ev)
    if win.empty:
        continue
    win["session_id"] = r["session_id"]
    win["scenario"] = r["scenario"]
    win["label"] = int(r["label"])
    parts.append(win)

data = pd.concat(parts, ignore_index=True)
data.to_csv(OUT_CSV, index=False)

print("Saved:", OUT_CSV)
print("Runs:", len(runs), " Windows:", len(data))
print("\nWindows per label (0 = normal, 1 = attack-like):")
print(data["label"].value_counts().to_string())
print("\nWindows per scenario:")
print(data.groupby(["label", "scenario"]).size().to_string())
