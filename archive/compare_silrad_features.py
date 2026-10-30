
from pathlib import Path
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    average_precision_score
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "dataset"
MODEL_DIR = BASE_DIR / "models"

TRAIN_FILE = DATA_DIR / "fasttext-trainmodel.csv"
TEST_FILE = DATA_DIR / "fasttext-testmodel.csv"

MODEL_DIR.mkdir(exist_ok=True)

train_df = pd.read_csv(TRAIN_FILE, low_memory=False)
test_df = pd.read_csv(TEST_FILE, low_memory=False)

# Keep only features available in both datasets; exclude the label.
features = [
    col for col in train_df.columns
    if col != "class" and col in test_df.columns
]

X_train_all = train_df[features].apply(pd.to_numeric, errors="coerce")
X_test_all = test_df[features].apply(pd.to_numeric, errors="coerce")

y_train = pd.to_numeric(train_df["class"], errors="coerce")
y_test = pd.to_numeric(test_df["class"], errors="coerce")

# Remove rows with invalid values, using the same feature set.
train_valid = X_train_all.notna().all(axis=1) & y_train.isin([0, 1])
test_valid = X_test_all.notna().all(axis=1) & y_test.isin([0, 1])

X_train_all = X_train_all.loc[train_valid]
y_train = y_train.loc[train_valid].astype(int)
X_test_all = X_test_all.loc[test_valid]
y_test = y_test.loc[test_valid].astype(int)

six_features = [
    "event.code",
    "CallTrace",
    "GrantedAccess",
    "TargetImage",
    "TargetObject",
    "task",
]

if not all(col in features for col in six_features):
    raise ValueError("One or more of the original six features are missing.")

experiments = {
    "six_features": six_features,
    "all_features": features,
}

for name, selected_features in experiments.items():
    print("\n" + "=" * 60)
    print(f"EXPERIMENT: {name}")
    print(f"Number of features: {len(selected_features)}")

    model = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train_all[selected_features], y_train)

    predictions = model.predict(X_test_all[selected_features])
    probabilities = model.predict_proba(X_test_all[selected_features])

    ransomware_index = list(model.classes_).index(1)

    print(f"Accuracy: {accuracy_score(y_test, predictions):.4f}")
    print(
        "Balanced accuracy: "
        f"{balanced_accuracy_score(y_test, predictions):.4f}"
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
        "Ransomware average precision: "
        f"{average_precision_score(y_test, probabilities[:, ransomware_index]):.4f}"
    )

    output_path = MODEL_DIR / f"silrad_random_forest_{name}.pkl"

    joblib.dump(
        {"model": model, "features": selected_features},
        output_path,
    )

    print(f"Saved model: {output_path}")

print("\nBoth experiments completed.")
