
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    average_precision_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    f1_score,
)
import joblib

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "dataset"
MODEL_DIR = BASE_DIR / "models"

train_file = DATA_DIR / "fasttext-trainmodel.csv"
test_file = DATA_DIR / "fasttext-testmodel.csv"

train = pd.read_csv(train_file, low_memory=False)
test = pd.read_csv(test_file, low_memory=False)

print("Original training rows:", len(train))
print("Original test rows:", len(test))

# Remove repeated complete records from training.
train = train.drop_duplicates().copy()

# Remove test records that exactly match any training record.
combined = pd.concat([train, test], ignore_index=True)
overlap = combined.duplicated(keep=False)

train_keys = set(
    pd.util.hash_pandas_object(train, index=False).tolist()
)
test_keys = pd.util.hash_pandas_object(test, index=False).tolist()

keep_test = [
    key not in train_keys for key in test_keys
]
test = test.loc[keep_test].drop_duplicates().copy()

print("Training rows after deduplication:", len(train))
print("Test rows after overlap removal and deduplication:", len(test))

features = [
    col for col in train.columns
    if col != "class" and col in test.columns
]

X_train = train[features].apply(pd.to_numeric, errors="coerce")
X_test = test[features].apply(pd.to_numeric, errors="coerce")

y_train = pd.to_numeric(train["class"], errors="coerce")
y_test = pd.to_numeric(test["class"], errors="coerce")

valid_train = X_train.notna().all(axis=1) & y_train.isin([0, 1])
valid_test = X_test.notna().all(axis=1) & y_test.isin([0, 1])

X_train = X_train.loc[valid_train]
y_train = y_train.loc[valid_train].astype(int)
X_test = X_test.loc[valid_test]
y_test = y_test.loc[valid_test].astype(int)

model = RandomForestClassifier(
    n_estimators=200,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)
probabilities = model.predict_proba(X_test)
ransomware_index = list(model.classes_).index(1)

print("\nVALIDATION RESULTS")
print("Features:", len(features))
print("Accuracy:", round(accuracy_score(y_test, predictions), 4))

print("MCC:", round(matthews_corrcoef(y_test, predictions), 4))
print(
    "Ransomware precision:",
    round(precision_score(y_test, predictions, pos_label=1, zero_division=0), 4),
)
print(
    "Ransomware recall:",
    round(recall_score(y_test, predictions, pos_label=1, zero_division=0), 4),
)
print(
    "Ransomware F1-score:",
    round(f1_score(y_test, predictions, pos_label=1, zero_division=0), 4),
)

print(
    "Balanced accuracy:",
    round(balanced_accuracy_score(y_test, predictions), 4),
)
print("\nClassification report:")
print(
    classification_report(
        y_test,
        predictions,
        labels=[0, 1],
        target_names=["Goodware", "Ransomware"],
        zero_division=0,
    )
)
print("Confusion matrix:")
print(confusion_matrix(y_test, predictions, labels=[0, 1]))
print(
    "Ransomware average precision:",
    round(
        average_precision_score(
            y_test, probabilities[:, ransomware_index]
        ),
        4,
    ),
)

output_path = MODEL_DIR / "silrad_random_forest_validated.pkl"
joblib.dump({"model": model, "features": features}, output_path)
print("\nSaved separate model:", output_path)
