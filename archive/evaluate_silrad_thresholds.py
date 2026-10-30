
from pathlib import Path

import pandas as pd
import joblib

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    matthews_corrcoef,
    confusion_matrix,
    average_precision_score,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "dataset"
MODEL_DIR = BASE_DIR / "models"

TRAIN_FILE = DATA_DIR / "fasttext-trainmodel.csv"
TEST_FILE = DATA_DIR / "fasttext-testmodel.csv"
MODEL_FILE = MODEL_DIR / "silrad_random_forest_validated.pkl"

# Load the separately validated model.
bundle = joblib.load(MODEL_FILE)
model = bundle["model"]
features = bundle["features"]

# Load the same data used in validation.
train = pd.read_csv(TRAIN_FILE, low_memory=False)
test = pd.read_csv(TEST_FILE, low_memory=False)

print("Original training rows:", len(train))
print("Original test rows:", len(test))

# Remove duplicate training records.
train = train.drop_duplicates().copy()

# Remove test rows that exactly match training records.
train_keys = set(
    pd.util.hash_pandas_object(train, index=False).tolist()
)
test_keys = pd.util.hash_pandas_object(test, index=False).tolist()

keep_test = [key not in train_keys for key in test_keys]
test = test.loc[keep_test].drop_duplicates().copy()

print("Training rows after deduplication:", len(train))
print("Test rows after overlap removal and deduplication:", len(test))

# Prepare test features and labels.
X = test[features].apply(pd.to_numeric, errors="coerce")
y = pd.to_numeric(test["class"], errors="coerce")

valid = y.isin([0, 1]) & X.notna().all(axis=1)
X = X.loc[valid]
y = y.loc[valid].astype(int)

# Get the model's ransomware probabilities.
ransomware_index = list(model.classes_).index(1)
probabilities = model.predict_proba(X)[:, ransomware_index]

print("\nTHRESHOLD EVALUATION")
print("Test samples:", len(y))
print("\nThreshold | Precision | Recall | F1-score | MCC")
print("-" * 57)
for threshold in [0.25, 0.30, 0.35, 0.40]:
    predictions = (probabilities >= threshold).astype(int)

    precision = precision_score(
        y, predictions, pos_label=1, zero_division=0
    )
    recall = recall_score(
        y, predictions, pos_label=1, zero_division=0
    )
    f1 = f1_score(
        y, predictions, pos_label=1, zero_division=0
    )
    mcc = matthews_corrcoef(y, predictions)

    print(
        f"{threshold:9.2f} | {precision:9.4f} | "
        f"{recall:6.4f} | {f1:8.4f} | {mcc:5.4f}"
    )

# Report full metrics at the default threshold.
threshold = 0.50
predictions = (probabilities >= threshold).astype(int)

print(f"\nDETAILED RESULTS AT THRESHOLD {threshold:.2f}")
print("Accuracy:", round(accuracy_score(y, predictions), 4))
print( "Balanced accuracy:",round(balanced_accuracy_score(y, predictions), 4),)
print(
    "Ransomware average precision:",
    round(average_precision_score(y, probabilities), 4),
)
print("Confusion matrix (rows=true, columns=predicted):")
print(confusion_matrix(y, predictions, labels=[0, 1]))

# Report the more sensitive threshold separately for comparison.
threshold = 0.35
predictions = (probabilities >= threshold).astype(int)

print(f"\nCONFUSION MATRIX AT THRESHOLD {threshold:.2f}")
print(confusion_matrix(y, predictions, labels=[0, 1]))
