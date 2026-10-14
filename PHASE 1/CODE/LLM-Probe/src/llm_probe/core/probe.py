import os
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix

def train_probe(X, y, use_mlp=False):
    if use_mlp:
        probe = MLPClassifier(
            hidden_layer_sizes=(128, 64),
            activation='relu',
            solver='adam',
            max_iter=500,
            random_state=42
        )
    else:
        probe = LogisticRegression(
            class_weight='balanced',
            max_iter=1000,
            random_state=42
        )
    probe.fit(X, y)
    return probe

def evaluate_probe(probe, X_test, y_test):
    preds = probe.predict(X_test)
    return {
        'accuracy': accuracy_score(y_test, preds),
        'precision': precision_score(y_test, preds, zero_division=0),
        'recall': recall_score(y_test, preds, zero_division=0),
        'f1': f1_score(y_test, preds, zero_division=0),
        'report': classification_report(y_test, preds, zero_division=0),
        'confusion_matrix': confusion_matrix(y_test, preds)
    }

def save_probe(probe, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(probe, path)

def load_probe(path: str):
    return joblib.load(path)
