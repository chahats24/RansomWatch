import pandas as pd
import os
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report


# 1. Load training dataset
df = pd.read_csv("data/training_data.csv")

print("Dataset loaded successfully!")
print(df)
print()


# 2. Select features
X = df[
    [
        "files_changed",
        "renames",
        "extension_changes"
    ]
]

# 3. Select target/label
y = df["label"]


# 4. Split data into training and testing
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y
)


# 5. Create Random Forest model
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)


# 6. Train the model
model.fit(X_train, y_train)


# 7. Test the model
y_pred = model.predict(X_test)


# 8. Calculate accuracy
accuracy = accuracy_score(y_test, y_pred)

print("Model training completed!")
print()
print("Accuracy:", accuracy)
print()
print("Classification Report:")
print(classification_report(y_test, y_pred))


# 9. Create models folder
os.makedirs("models", exist_ok=True)


# 10. Save trained model
joblib.dump(model, "models/ransomware_model.pkl")

print()
print("Model saved successfully!")
print("Location: models/ransomware_model.pkl")