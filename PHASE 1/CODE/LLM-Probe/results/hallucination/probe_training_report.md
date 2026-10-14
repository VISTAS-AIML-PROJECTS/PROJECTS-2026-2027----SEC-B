# Hallucination Probe Training & Evaluation Report

- **Best Representation**: `mean_pooled`
- **Best Layers (Cohen's d Rankings)**: `[32, 15, 17, 16, 14]`
- **Selected Probe Layers (Top 3)**: `[32, 15, 17]`

## In-Domain Evaluation (80/20 Stratified Split)
- **Accuracy**: `0.6687`
- **Precision**: `0.7160`
- **Recall**: `0.6591`
- **F1 Score**: `0.6864`
- **MLP Validation F1**: `0.7241`

### Confusion Matrix (Linear):
```
[[49 23]
 [30 58]]
```

### Classification Report (Linear):
```
              precision    recall  f1-score   support

           0       0.62      0.68      0.65        72
           1       0.72      0.66      0.69        88

    accuracy                           0.67       160
   macro avg       0.67      0.67      0.67       160
weighted avg       0.67      0.67      0.67       160

```

## Held-Out Category Generalization Tests

### Hold-Out Category: `Misconceptions`
- **Generalization F1**: `0.3947`
- **Generalization Accuracy**: `0.5400`
- **Generalization Precision**: `0.5000`
- **Generalization Recall**: `0.3261`
- **Positive Predictions Made**: `30`

#### Confusion Matrix:
```
[[39 15]
 [31 15]]
```
```
              precision    recall  f1-score   support

           0       0.56      0.72      0.63        54
           1       0.50      0.33      0.39        46

    accuracy                           0.54       100
   macro avg       0.53      0.52      0.51       100
weighted avg       0.53      0.54      0.52       100

```

### Hold-Out Category: `Law`
- **Generalization F1**: `0.6133`
- **Generalization Accuracy**: `0.5246`
- **Generalization Precision**: `0.6765`
- **Generalization Recall**: `0.5610`
- **Positive Predictions Made**: `34`

#### Confusion Matrix:
```
[[ 9 11]
 [18 23]]
```
```
              precision    recall  f1-score   support

           0       0.33      0.45      0.38        20
           1       0.68      0.56      0.61        41

    accuracy                           0.52        61
   macro avg       0.50      0.51      0.50        61
weighted avg       0.56      0.52      0.54        61

```
