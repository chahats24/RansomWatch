
import os
import joblib
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.metrics import confusion_matrix, classification_report

DATA_PATH = "data/ransomwatch_dataset.csv"
CURRENT_MODEL_PATH = "models/isolation_forest.pkl"
BACKUP_MODEL_PATH = "models/isolation_forest_backup.pkl"
CANDIDATE_PATH = "models/isolation_forest_candidate.pkl"

FEATURES = ["files_changed", "renames", "ext_changes"]


def main():
    print("\n=== RANSOMWATCH CANDIDATE MODEL EVALUATION ===")

    if not os.path.exists(DATA_PATH):
        print("ERROR: Dataset not found:", DATA_PATH)
        return

    if not os.path.exists(BACKUP_MODEL_PATH):
        print("ERROR: Model backup not found. Stop here.")
        return

    df = pd.read_csv(DATA_PATH)

    required = FEATURES + ["label"]
    missing = [column for column in required if column not in df.columns]

    if missing:
        print("ERROR: Missing columns:", missing)
        return

    df = df.dropna(subset=required).copy()
    df["label"] = df["label"].astype(int)

    normal = df[df["label"] == 0]
    attacks = df[df["label"] == 1]

    if len(normal) < 10 or attacks.empty:
        print("ERROR: Not enough normal or attack-like windows.")
        return

    X_normal = normal[FEATURES]
    X_all = df[FEATURES]
    y = df["label"]

    # Train only on normal activity.
    # Contamination is a model parameter, not a ransomware probability.
    candidate = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        random_state=42
    )
    candidate.fit(X_normal)

    # Evaluate on the collected dataset.
    # This is diagnostic, not an independent test.
    predictions = candidate.predict(X_all)
    predicted_attack = (predictions == -1).astype(int)

    # Existing alert policy: anomaly AND more than 10 changed files.
    alerts = (
        (predicted_attack == 1) &
        (df["files_changed"] > 10)
    ).astype(int)

    print("\nDataset rows:", len(df))
    print("Normal training windows:", len(normal))
    print("Attack-like evaluation windows:", len(attacks))

    print("\n=== ISOLATION FOREST RESULTS ===")
    print("Confusion matrix (rows=true, columns=predicted; order 0, 1):")
    print(confusion_matrix(y, predicted_attack, labels=[0, 1]))

    print("\nClassification report:")
    print(classification_report(
        y, predicted_attack,
        labels=[0, 1],
        target_names=["Normal", "Attack-like"],
        zero_division=0
    ))

    true_alerts = int(((y == 1) & (alerts == 1)).sum())
    false_alerts = int(((y == 0) & (alerts == 1)).sum())

    print("\n=== ALERT THRESHOLD (>10 FILES) ===")
    print("Attack-like windows alerted:", true_alerts, "/", len(attacks))
    print("Normal windows alerted:", false_alerts, "/", len(normal))
    print("Total alerts:", int(alerts.sum()))

    print("\n=== ATTACK-LIKE WINDOWS NOT ALERTED ===")
    missed = df.loc[
        (y == 1) & (alerts == 0),
        ["scenario"] + FEATURES
    ]
    print(missed.to_string(index=False) if not missed.empty else "None")

    # Save only as a separate candidate. Do not overwrite the live model.
    os.makedirs("models", exist_ok=True)
    joblib.dump(candidate, CANDIDATE_PATH)

    print("\nCandidate saved to:", CANDIDATE_PATH)
    print("Current live model remains unchanged.")
    print("Backup remains available at:", BACKUP_MODEL_PATH)
    print("\nIMPORTANT: These results use the collected dataset itself.")
    print("They do not establish real-world detection accuracy.")


if __name__ == "__main__":
    main()
