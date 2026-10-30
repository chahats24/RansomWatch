import pandas as pd

# Normal activity collected from features.py
normal_data = [
    [1, 0, 0, 0],
    [1, 0, 0, 0],
    [2, 0, 0, 0],
    [1, 0, 0, 0],
    [2, 1, 0, 0],
    [1, 0, 0, 0],
    [2, 0, 0, 0],
    [1, 0, 0, 0],
    [3, 0, 0, 0],
    [2, 1, 0, 0]
]

# Ransomware-like activity
# Many files changed/renamed with extension changes
ransomware_data = [
    [20, 5, 8, 1],
    [30, 10, 15, 1],
    [50, 15, 25, 1],
    [40, 12, 20, 1],
    [60, 20, 30, 1],
    [25, 8, 12, 1],
    [70, 25, 35, 1],
    [45, 18, 22, 1],
    [35, 14, 18, 1],
    [80, 30, 40, 1]
]

data = normal_data + ransomware_data

columns = [
    "files_changed",
    "renames",
    "extension_changes",
    "label"
]

df = pd.DataFrame(data, columns=columns)

# Create data folder if it does not exist
import os
os.makedirs("data", exist_ok=True)

# Save dataset
df.to_csv("data/training_data.csv", index=False)

print("Training dataset created successfully!")
print()
print(df)
print()
print("Dataset shape:", df.shape)