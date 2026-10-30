import time
import joblib
import pandas as pd

from features import create_features
from database import initialize_database, log_alert


# ==============================
# CONFIGURATION
# ==============================

MODEL_PATH = "models/ransomware_model.pkl"

# How often the detector checks the database
CHECK_INTERVAL = 5

# Probability threshold
RANSOMWARE_THRESHOLD = 0.50


# ==============================
# LOAD MODEL
# ==============================

print("Loading ransomware detection model...")

model = joblib.load(MODEL_PATH)

print("Model loaded successfully!")


# Keep track of already processed windows
processed_windows = set()


# ==============================
# PREDICT ACTIVITY
# ==============================

def predict_activity(files_changed, renames, extension_changes):

    data = pd.DataFrame([{
        "files_changed": files_changed,
        "renames": renames,
        "extension_changes": extension_changes
    }])

    prediction = model.predict(data)[0]

    # Get probability if the model supports it
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(data)[0]

        # Probability of ransomware class (1)
        if 1 in model.classes_:
            ransomware_index = list(model.classes_).index(1)
            ransomware_probability = probabilities[ransomware_index]
        else:
            ransomware_probability = float(prediction)
    else:
        ransomware_probability = float(prediction)

    if ransomware_probability >= RANSOMWARE_THRESHOLD:
        result = "RANSOMWARE"
    else:
        result = "NORMAL"

    return result, ransomware_probability


# ==============================
# DETECT ACTIVITY
# ==============================

def detect_activity():

    features = create_features(window_seconds=5)

    if features.empty:
        return

    # Process each feature window
    for _, row in features.iterrows():

        window = str(row["window"])

        # Don't process the same window repeatedly
        if window in processed_windows:
            continue

        files_changed = int(row["files_changed"])
        renames = int(row["renames"])
        extension_changes = int(row["extension_changes"])

        result, probability = predict_activity(
            files_changed,
            renames,
            extension_changes
        )

        print()
        print("==========================================")
        print("RANSOMWATCH DETECTION")
        print("==========================================")

        print(f"Window             : {window}")
        print(f"Files changed      : {files_changed}")
        print(f"Renames            : {renames}")
        print(f"Extension changes  : {extension_changes}")
        print(f"Prediction         : {result}")
        print(f"Ransomware score   : {probability:.2f}")

        # ==============================
        # RANSOMWARE DETECTED
        # ==============================

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
                anomaly_score=probability,
                message=message
            )

            print()
            print("🚨 ALERT: RANSOMWARE DETECTED!")
            print(f"Message: {message}")

        else:

            print("Status: Normal activity")

        print("==========================================")

        processed_windows.add(window)


# ==============================
# MAIN LOOP
# ==============================

if __name__ == "__main__":

    initialize_database()

    print()
    print("==========================================")
    print("     RANSOMWATCH DETECTOR STARTED")
    print("==========================================")
    print("Monitoring database for suspicious activity...")
    print("Press CTRL+C to stop.")
    print()

    try:

        while True:

            detect_activity()

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:

        print()
        print("Detector stopped.")