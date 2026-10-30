import time
import joblib
import pandas as pd

from features import create_features
from database import initialize_database, log_alert


MODEL_PATH = "models/isolation_forest.pkl"
CHECK_INTERVAL = 5

model = joblib.load(MODEL_PATH)

processed_windows = set()

existing_features = create_features(window_seconds=5)

if not existing_features.empty:
    processed_windows.update(
        existing_features["window"].astype(str)
    )

def predict_activity(files_changed, renames, extension_changes):

    data = pd.DataFrame([{
        "files_changed": files_changed,
        "renames": renames,
        "extension_changes": extension_changes
    }])

    prediction = model.predict(data)[0]
    score = model.decision_function(data)[0]

    if prediction == -1:
        result = "RANSOMWARE"
    else:
        result = "NORMAL"

    return result, score


def detect_activity():

    features = create_features(window_seconds=5)

    if features.empty:
        return

    for _, row in features.iterrows():

        window = str(row["window"])

        if window in processed_windows:
            continue

        files_changed = int(row["files_changed"])
        renames = int(row["renames"])
        extension_changes = int(row["extension_changes"])

        
        model_result, score = predict_activity(
            files_changed,
            renames,
            extension_changes
        )

        
        extension_rename_signal = (
            files_changed > 10 and extension_changes > 0
        )

        
        high_volume_signal = files_changed > 10

        result = (
            "RANSOMWARE"
            if model_result == "RANSOMWARE"
            or extension_rename_signal
            or high_volume_signal
            else "NORMAL"
        )


        print()
        print("==========================================")
        print("RANSOMWATCH ISOLATION FOREST DETECTION")
        print("==========================================")

        print(f"Window             : {window}")
        print(f"Files changed      : {files_changed}")
        print(f"Renames            : {renames}")
        print(f"Extension changes  : {extension_changes}")
        print(f"Model prediction   : {model_result}")
        print(f"Final detection    : {result}")

        if extension_rename_signal and model_result == "NORMAL":
                print("Detection reason   : High-volume extension-changing renames")
                print(f"Anomaly score      : {score:.4f}")

        if result == "RANSOMWARE":

            message = (
                "Ransomware-like activity detected! "
                f"{files_changed} files changed, "
                f"{renames} renames, "
                f"{extension_changes} extension changes."
            )

            log_alert(
                files_changed=files_changed,
                renames=renames,
                extension_changes=extension_changes,
                anomaly_score=score,
                message=message
            )

            print()
            print("🚨 ALERT: RANSOMWARE DETECTED!")
            print(f"Message: {message}")

        else:

            print("Status: Normal activity")

        print("==========================================")

        processed_windows.add(window)


if __name__ == "__main__":

    initialize_database()

    print()
    print("==========================================")
    print(" RANSOMWATCH ISOLATION FOREST DETECTOR")
    print("==========================================")
    print("Monitoring for ransomware-like activity...")
    print("Press CTRL+C to stop.")
    print()

    try:

        while True:

            detect_activity()

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:

        print()
        print("Detector stopped.")