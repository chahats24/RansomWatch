import joblib
import pandas as pd

MODEL_PATH = "models/ransomware_model.pkl"

model = joblib.load(MODEL_PATH)


def predict_activity(files_changed, renames, extension_changes):

    data = pd.DataFrame([{
        "files_changed": files_changed,
        "renames": renames,
        "extension_changes": extension_changes
    }])

    prediction = model.predict(data)[0]

    if prediction == 1:
        return "RANSOMWARE"
    else:
        return "NORMAL"


if __name__ == "__main__":

    result1 = predict_activity(
        files_changed=2,
        renames=0,
        extension_changes=0
    )

    result2 = predict_activity(
        files_changed=50,
        renames=15,
        extension_changes=25
    )

    print("Normal test:", result1)
    print("Ransomware test:", result2)