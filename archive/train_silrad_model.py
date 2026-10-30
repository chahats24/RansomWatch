from pathlib import Path
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    balanced_accuracy_score,
    average_precision_score
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "dataset"
MODEL_DIR = BASE_DIR / "models"

TRAIN_FILE = DATA_DIR / "fasttext-trainmodel.csv"
TEST_FILE = DATA_DIR / "fasttext-testmodel.csv"
MODEL_FILE = MODEL_DIR / "silrad_random_forest_all_features.pkl"


def load_data(path):
    df = pd.read_csv(path, low_memory=False)

    if "class" not in df.columns:
        raise ValueError(f"Missing class column in {path.name}")

    feature_columns = [column for column in df.columns if column != "class"]

    X = df[feature_columns].apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(df["class"], errors="coerce")

    valid = y.isin([0, 1]) & X.notna().all(axis=1)

    return X.loc[valid], y.loc[valid].astype(int), feature_columns


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading SILRAD training data...")
    X_train, y_train, train_features = load_data(TRAIN_FILE)

    print("Loading SILRAD test data...")
    X_test, y_test, test_features = load_data(TEST_FILE)

    if train_features != test_features:
        raise ValueError("Training and test feature columns do not match.")

    print("Number of input features:", len(train_features))
    print("Training rows:", len(X_train))
    print("Test rows:", len(X_test))
    print("\nTraining label counts:")
    print(y_train.value_counts().sort_index())

    model = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )

    print("\nTraining Random Forest on all SILRAD features...")
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, list(model.classes_).index(1)]

    print("\nAccuracy:", round(accuracy_score(y_test, predictions), 4))
    print("Balanced accuracy:", round(
        balanced_accuracy_score(y_test, predictions), 4
    ))

    print("\nClassification report:")
    print(classification_report(
        y_test,
        predictions,
        labels=[0, 1],
        target_names=["Goodware", "Ransomware"],
        zero_division=0
    ))

    print("Confusion matrix (rows=actual, columns=predicted):")
    print(confusion_matrix(y_test, predictions, labels=[0, 1]))

    print("\nRansomware average precision:", round(
        average_precision_score(y_test, probabilities), 4
    ))

    joblib.dump(
        {"model": model, "features": train_features},
        MODEL_FILE
    )

    print("\nModel saved to:", MODEL_FILE)

    importance = pd.Series(
        model.feature_importances_,
        index=train_features
    ).sort_values(ascending=False)

    print("\nFeature importance:")
    print(importance.to_string())


if __name__ == "__main__":
    main()
