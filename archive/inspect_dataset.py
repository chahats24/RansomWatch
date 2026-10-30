
import pandas as pd
from pathlib import Path

for file_path in Path("dataset").glob("*.csv"):
    print("\n" + "=" * 60)
    print("FILE:", file_path.name)

    df = pd.read_csv(file_path, low_memory=False)

    print("Shape (rows, columns):", df.shape)
    print("\nColumn names:")
    print(df.columns.tolist())

    print("\nMissing values:", df.isnull().sum().sum())

    if "class" in df.columns:
        print("\nClass distribution:")
        print(df["class"].value_counts(dropna=False).head(20))

    if "EventType" in df.columns:
        print("\nEventType values:")
        print(df["EventType"].value_counts(dropna=False).head(15))

    for column in ["event.code", "task", "class"]:
        if column in df.columns:
            print(f"\nSample values in {column}:")
            print(df[column].drop_duplicates().head(15).tolist())

    print("\nFirst 3 rows (selected columns):")
    selected = [
        c for c in [
            "event.code", "EventType", "TargetObject",
            "Image", "Description", "task", "class"
        ] if c in df.columns
    ]
    print(df[selected].head(3).to_string(index=False))
