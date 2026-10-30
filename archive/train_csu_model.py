import pandas as pd, numpy as np, joblib, os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (precision_score, recall_score, f1_score,
                             balanced_accuracy_score, confusion_matrix,
                             precision_recall_curve)

LABEL = "Ware Type"
FEATURES = ["File_created", "File_Delete_archived",
            "file_name_entropy", "extension_similarity"]

df = pd.read_csv("data/Ransomware_Data.csv")
df["y"] = (df[LABEL] == "ransom").astype(int)
all_feats = [c for c in df.columns if c not in (LABEL, "y")]

# 1) remove duplicate rows
d = df.drop_duplicates()
# 2) remove rows whose features are identical but labels conflict
bad = d.groupby(all_feats)["y"].nunique()
bad = bad[bad > 1].index
d = d.merge(pd.DataFrame(index=bad).reset_index().assign(_b=1), on=all_feats, how="left")
d = d[d["_b"].isna()].drop(columns="_b")

train, test = train_test_split(d, test_size=0.2, stratify=d["y"], random_state=42)
train, val = train_test_split(train, test_size=0.25, stratify=train["y"], random_state=42)

model = RandomForestClassifier(n_estimators=200, min_samples_leaf=2,
                               class_weight="balanced", random_state=42, n_jobs=-1)
model.fit(train[FEATURES], train["y"])

# threshold chosen on VALIDATION data only (not the test set)
pv = model.predict_proba(val[FEATURES])[:, 1]
P, R, T = precision_recall_curve(val["y"], pv)
thr = float(T[np.argmax((2 * P * R / (P + R + 1e-9))[:-1])])

pt = model.predict_proba(test[FEATURES])[:, 1]
pred = (pt >= thr).astype(int)
cm = confusion_matrix(test["y"], pred)

os.makedirs("models", exist_ok=True)
joblib.dump({"model": model, "features": FEATURES, "threshold": thr}, "models/csu_rf.pkl")

out = f"""CSU model results (deduplicated, independent test set)
Rows after cleaning: {len(d)}  train/val/test: {len(train)}/{len(val)}/{len(test)}
Features: {FEATURES}
Threshold (chosen on validation): {thr:.3f}
Precision: {precision_score(test['y'], pred):.3f}
Recall: {recall_score(test['y'], pred):.3f}
F1: {f1_score(test['y'], pred):.3f}
Balanced accuracy: {balanced_accuracy_score(test['y'], pred):.3f}
Confusion matrix [[TN, FP],[FN, TP]]: {cm.tolist()}
"""
print(out)
open("csu_results.txt", "w").write(out)