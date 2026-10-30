import joblib
import pandas as pd


MODEL_PATH = "models/isolation_forest.pkl"

model = joblib.load(MODEL_PATH)


def test_activity(files_changed, renames, extension_changes):

    data = pd.DataFrame([{
        "files_changed": files_changed,
        "renames": renames,
        "extension_changes": extension_changes
    }])

    prediction = model.predict(data)[0]
    score = model.decision_function(data)[0]

    if prediction == -1:
        result = "ANOMALY"
    else:
        result = "NORMAL"

    print()
    print("==========================================")
    print("ISOLATION FOREST TEST")
    print("==========================================")
    print(f"Files changed     : {files_changed}")
    print(f"Renames           : {renames}")
    print(f"Extension changes : {extension_changes}")
    print(f"Prediction        : {result}")
    print(f"Anomaly score     : {score:.4f}")
    print("==========================================")


print("\nTesting normal activity...")
test_activity(2, 0, 0)

print("\nTesting suspicious activity...")
test_activity(40, 20, 20)