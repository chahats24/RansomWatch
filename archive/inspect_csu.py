import pandas as pd

PATH = "data/Ransomware_Data.csv"
LABEL = "Ware Type"

df = pd.read_csv(PATH)
print("Shape:", df.shape)
print("\n=== COLUMNS / DTYPES / UNIQUE VALUES ===")
for c in df.columns:
    print(f"{c:35s} {str(df[c].dtype):10s} nunique={df[c].nunique():<8} min={df[c].min()} max={df[c].max()}")

print("\n=== LABEL COUNTS (raw) ===")
print(df[LABEL].value_counts())

feats = [c for c in df.columns if c != LABEL]
dedup = df.drop_duplicates()
print("\nUnique full rows:", len(dedup))
print("Unique rows by label:\n", dedup[LABEL].value_counts())

conflict = df.drop_duplicates().groupby(feats).agg(n=(LABEL, "nunique"))
print("\nFeature-identical rows that carry BOTH labels:", int((conflict["n"] > 1).sum()))

print("\n=== FIRST 3 ROWS (transposed) ===")
print(df.head(3).T)

print("\n=== MEAN PER CLASS (deduplicated) ===")
print(dedup.groupby(LABEL)[feats].mean().T)