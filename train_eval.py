import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import (precision_score, recall_score, f1_score,
                             balanced_accuracy_score, confusion_matrix)
from sklearn.model_selection import StratifiedGroupKFold

from window_features import FEATURES, BASE_FEATURES

data = pd.read_csv("data/ransomwatch_dataset.csv")
y = data["label"].values
groups = data["session_id"].values

n_sessions = data.groupby("label")["session_id"].nunique().min()
n_splits = int(min(5, n_sessions))
cv = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=42)


def rf():
    return RandomForestClassifier(n_estimators=300, min_samples_leaf=2,
                                  class_weight="balanced", random_state=42, n_jobs=-1)


def out_of_fold(make_pred, cols):
    pred = np.zeros(len(data), dtype=int)
    for tr, te in cv.split(data, y, groups):
        pred[te] = make_pred(data.iloc[tr][cols], y[tr], data.iloc[te][cols])
    return pred


def rf_pred(Xtr, ytr, Xte):
    return rf().fit(Xtr, ytr).predict(Xte)


def iforest_pred(Xtr, ytr, Xte):
    m = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
    m.fit(Xtr[ytr == 0])                      # trained on NORMAL windows only
    return (m.predict(Xte) == -1).astype(int)


def metrics(pred):
    cm = confusion_matrix(y, pred, labels=[0, 1])
    return {
        "precision": precision_score(y, pred, zero_division=0),
        "recall": recall_score(y, pred, zero_division=0),
        "f1": f1_score(y, pred, zero_division=0),
        "bal_acc": balanced_accuracy_score(y, pred),
        "cm": cm.tolist(),
    }


experiments = {
    "Isolation Forest, 3 original features": (iforest_pred, BASE_FEATURES),
    "Random Forest, 3 original features": (rf_pred, BASE_FEATURES),
    "Random Forest, all features (with entropy)": (rf_pred, FEATURES),
}

lines = []
lines.append("RansomWatch self-collected dataset - session-wise cross-validation")
lines.append(f"Windows: {len(data)}  (normal {int((y==0).sum())}, attack-like {int((y==1).sum())})")
lines.append(f"Sessions: {data['session_id'].nunique()}  | folds: {n_splits} "
             "(windows from one run never appear in both train and test)")
lines.append("")

preds = {}
for name, (fn, cols) in experiments.items():
    p = out_of_fold(fn, cols)
    preds[name] = p
    m = metrics(p)
    lines.append(name)
    lines.append(f"  precision={m['precision']:.3f}  recall={m['recall']:.3f}  "
                 f"F1={m['f1']:.3f}  balanced_acc={m['bal_acc']:.3f}")
    lines.append(f"  confusion [[TN, FP],[FN, TP]] = {m['cm']}")

best = "Random Forest, all features (with entropy)"
data["pred"] = preds[best]

lines.append("")
lines.append(f"Per-scenario results ({best})")
for (label, sc), g in data.groupby(["label", "scenario"]):
    if label == 1:
        lines.append(f"  attack  {sc:22s} windows={len(g):4d}  detected={g['pred'].mean():.2f}")
    else:
        lines.append(f"  normal  {sc:22s} windows={len(g):4d}  false-alarm={g['pred'].mean():.2f}")

# session-level detection and time to first alert (attack sessions)
det, delays = 0, []
atk = data[data["label"] == 1].sort_values("window")
sessions = atk["session_id"].unique()
for s in sessions:
    g = atk[atk["session_id"] == s].reset_index(drop=True)
    hit = g.index[g["pred"] == 1]
    if len(hit):
        det += 1
        t0 = pd.to_datetime(g["window"].iloc[0], format="ISO8601")
        t1 = pd.to_datetime(g["window"].iloc[hit[0]], format="ISO8601")
        delays.append((t1 - t0).total_seconds() + 5)
lines.append("")
lines.append(f"Attack runs detected at least once: {det}/{len(sessions)}")
if delays:
    lines.append(f"Time from attack start to first alert (window end): "
                 f"median {np.median(delays):.0f}s, max {np.max(delays):.0f}s")

final = rf().fit(data[FEATURES], y)
imp = sorted(zip(FEATURES, final.feature_importances_), key=lambda x: -x[1])
lines.append("")
lines.append("Feature importance (final model):")
for f, v in imp:
    lines.append(f"  {f:22s} {v:.3f}")

joblib.dump({"model": final, "features": FEATURES}, "models/ransomwatch_rf.pkl")
lines.append("")
lines.append("Saved final model to models/ransomwatch_rf.pkl")

text = "\n".join(lines)
print(text)
open("ransomwatch_results.txt", "w").write(text)
