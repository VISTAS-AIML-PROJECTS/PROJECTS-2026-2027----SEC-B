"""Placement-readiness model.

HONEST NOTE: there is no real placement-outcome dataset in this project, so the model is trained on a *simulated* cohort of
students. A hidden skill value drives noisy behaviour (accuracy, speed, consistency, trend...), and the readiness label is
derived from skill + noise, so the label is NOT a simple threshold on one feature. The code reports hold-out accuracy,
cross-validation, confusion matrix and feature importances. Swap `simulate_cohort` for real labelled data when available.
"""
import json, os
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import cross_val_score, train_test_split

FEATURES = ["accuracy", "avg_score", "time_per_question", "score_std", "trend", "tests_taken", "hard_accuracy", "topics_covered"]
LABELS = ["Low", "Medium", "High"]
MIN_TESTS = 3

def simulate_cohort(n=3000, seed=42):
    r = np.random.default_rng(seed)
    skill = r.normal(0, 1, n)
    tests = r.integers(3, 30, n)
    accuracy = np.clip(0.62 + 0.17 * skill + r.normal(0, 0.07, n), 0.15, 0.99)
    hard_acc = np.clip(accuracy - 0.12 + 0.05 * skill + r.normal(0, 0.08, n), 0.05, 0.99)
    avg_score = np.clip(accuracy * 100 + r.normal(0, 4, n), 5, 100)
    tpq = np.clip(42 - 6 * skill + r.normal(0, 9, n), 8, 120)
    std = np.clip(14 - 3 * skill + r.normal(0, 4, n), 1, 40)
    trend = np.clip(0.04 * skill + r.normal(0, 0.08, n), -0.4, 0.5)
    topics = np.clip((tests * r.uniform(0.3, 1.0, n)).astype(int) + 1, 1, 60)
    readiness = skill + 0.8 * trend + 0.15 * np.log(tests) + r.normal(0, 0.45, n)
    y = np.where(readiness < -0.45, "Low", np.where(readiness < 0.65, "Medium", "High"))
    X = np.column_stack([accuracy, avg_score, tpq, std, trend, tests, hard_acc, topics])
    return X, y

_cache = {}

def get_model():
    if "m" in _cache: return _cache["m"], _cache["report"]
    X, y = simulate_cohort()
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=7, stratify=y)
    m = RandomForestClassifier(n_estimators=200, max_depth=8, min_samples_leaf=5, random_state=42)
    m.fit(Xtr, ytr); pred = m.predict(Xte)
    cv = cross_val_score(RandomForestClassifier(n_estimators=100, max_depth=8, min_samples_leaf=5, random_state=1), X, y, cv=5)
    report = dict(
        data="Simulated cohort of 3000 students (no real placement outcomes available)",
        holdout_accuracy=round(float(accuracy_score(yte, pred)), 3),
        macro_f1=round(float(f1_score(yte, pred, average="macro")), 3),
        cv_mean=round(float(cv.mean()), 3), cv_std=round(float(cv.std()), 3),
        labels=LABELS, confusion=confusion_matrix(yte, pred, labels=LABELS).tolist(),
        importances=sorted(zip(FEATURES, [round(float(v), 3) for v in m.feature_importances_]), key=lambda t: -t[1]),
        train_size=int(len(ytr)), test_size=int(len(yte)),
    )
    _cache["m"], _cache["report"] = m, report
    try:
        with open(os.path.join(os.path.dirname(__file__), "data", "model_report.json"), "w") as f: json.dump(report, f, indent=2)
    except OSError:
        pass
    return m, report

def features_from_attempts(rows, topics_covered):
    """rows: attempts (newest first) with score,total,correct,time_taken,difficulty. Returns feature list or None."""
    if len(rows) < MIN_TESTS: return None
    rows = list(reversed(rows))  # oldest first
    scores = np.array([r["score"] for r in rows], dtype=float)
    acc = float(np.mean([r["correct"] / r["total"] for r in rows if r["total"]]))
    tpq = float(np.mean([r["time_taken"] / max(r["total"], 1) for r in rows]))
    k = min(3, len(scores) // 2) or 1
    trend = float((scores[-k:].mean() - scores[:k].mean()) / 100)
    hard = [r["correct"] / r["total"] for r in rows if r["difficulty"] == "Hard" and r["total"]]
    hard_acc = float(np.mean(hard)) if hard else max(acc - 0.12, 0.05)
    return [acc, float(scores.mean()), tpq, float(scores.std()), trend, len(rows), hard_acc, topics_covered]

def predict(features):
    m, _ = get_model()
    proba = m.predict_proba([features])[0]
    idx = int(np.argmax(proba))
    return m.classes_[idx], round(float(proba[idx]) * 100, 1), {c: round(float(p) * 100, 1) for c, p in zip(m.classes_, proba)}
