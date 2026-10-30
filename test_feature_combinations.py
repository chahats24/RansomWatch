
import joblib
import pandas as pd

model = joblib.load("models/isolation_forest.pkl")

tests = pd.DataFrame([
    [10, 0, 0],
    [100, 0, 0],
    [10, 10, 10],
    [100, 50, 50],
    [157, 79, 79],
], columns=[
    "files_changed",
    "renames",
    "extension_changes"
])

predictions = model.predict(tests)
scores = model.decision_function(tests)

tests["prediction"] = [
    "RANSOMWARE" if value == -1 else "NORMAL"
    for value in predictions
]
tests["anomaly_score"] = scores

print(tests.to_string(index=False))
