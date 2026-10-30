import pandas as pd

WINDOW_SECONDS = 5
HIGH_ENTROPY = 7.0

FEATURES = [
    "n_events",
    "files_changed",
    "creates",
    "modifies",
    "deletes",
    "renames",
    "ext_changes",
    "mean_entropy",
    "max_entropy",
    "high_entropy_events",
    "high_entropy_ratio",
]

# The three features the original detector used (for comparison)
BASE_FEATURES = ["files_changed", "renames", "ext_changes"]


def events_to_windows(df, window_seconds=WINDOW_SECONDS):
    """
    df columns needed: timestamp, event_type, file_path,
                       old_extension, new_extension, entropy
    Returns one row per time window with FEATURES.
    """
    if df.empty:
        return pd.DataFrame(columns=["window"] + FEATURES)

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"],format="ISO8601")
    df["window"] = df["timestamp"].dt.floor(f"{window_seconds}s")

    df["is_create"] = (df["event_type"] == "created").astype(int)
    df["is_modify"] = (df["event_type"] == "modified").astype(int)
    df["is_delete"] = (df["event_type"] == "deleted").astype(int)
    df["is_rename"] = (df["event_type"] == "renamed").astype(int)

    old_ext = df["old_extension"].fillna("")
    new_ext = df["new_extension"].fillna("")
    df["is_ext_change"] = (
        (df["event_type"] == "renamed") & (old_ext != new_ext)
    ).astype(int)

    # entropy is stored for created, modified AND renamed events
    written = df["entropy"].notna()
    df["ent"] = df["entropy"].where(written)
    df["is_high"] = (df["ent"] >= HIGH_ENTROPY).astype(int)
    df["is_written"] = written.astype(int)

    g = df.groupby("window")
    out = pd.DataFrame({
        "n_events": g.size(),
        "files_changed": g["file_path"].nunique(),
        "creates": g["is_create"].sum(),
        "modifies": g["is_modify"].sum(),
        "deletes": g["is_delete"].sum(),
        "renames": g["is_rename"].sum(),
        "ext_changes": g["is_ext_change"].sum(),
        "mean_entropy": g["ent"].mean().fillna(0.0),
        "max_entropy": g["ent"].max().fillna(0.0),
        "high_entropy_events": g["is_high"].sum(),
        "written_events": g["is_written"].sum(),
    }).reset_index()

    out["high_entropy_ratio"] = (
        out["high_entropy_events"] / out["written_events"].clip(lower=1)
    )
    return out.drop(columns=["written_events"])
