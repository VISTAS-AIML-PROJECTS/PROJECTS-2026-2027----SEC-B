import os
import pandas as pd
import joblib

from sklearn.model_selection import GroupShuffleSplit, GroupKFold, cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline

from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor
)

from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error
)

from xgboost import XGBRegressor
from catboost import CatBoostRegressor


# =========================================================
# 1. LOAD DATA
# =========================================================

file = "D:\\EV_TripPlanner\\data\\main\\EV_20K_Trips.csv"

df = pd.read_csv(file)

print("===== DATASET =====")
print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Unique vehicles:", df["Vehicle_ID"].nunique())
print("Unique trips:", df["Trip_ID"].nunique())


# =========================================================
# 2. SELECT SAFE FEATURES
# =========================================================

features = [
    "Manufacturer",
    "Model",
    "Year",
    "Battery_Capacity_kWh",
    "Battery_Type",
    "Motor_Power_kW",
    "Vehicle_Weight_kg",
    "Distance_km",
    "Avg_Speed",
    "Ambient_Temp_C",
    "Weather",
    "Road_Type",
    "SOH_pct",
    "Driving_Style"
]

target = "Energy_Consumed_kWh"

X = df[features].copy()
y = df[target].copy()

groups = df["Vehicle_ID"]


# =========================================================
# 3. FEATURE TYPES
# =========================================================

categorical_features = [
    "Manufacturer",
    "Model",
    "Battery_Type",
    "Weather",
    "Road_Type",
    "Driving_Style"
]

numeric_features = [
    "Year",
    "Battery_Capacity_kWh",
    "Motor_Power_kW",
    "Vehicle_Weight_kg",
    "Distance_km",
    "Avg_Speed",
    "Ambient_Temp_C",
    "SOH_pct"
]


# =========================================================
# 4. PREPROCESSOR
# =========================================================

preprocessor = ColumnTransformer(
    transformers=[
        (
            "cat",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False
            ),
            categorical_features
        ),
        (
            "num",
            "passthrough",
            numeric_features
        )
    ]
)


# =========================================================
# 5. VEHICLE-AWARE TRAIN / TEST SPLIT
# =========================================================

splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=0.20,
    random_state=42
)

train_idx, test_idx = next(
    splitter.split(X, y, groups=groups)
)

X_train = X.iloc[train_idx].copy()
X_test = X.iloc[test_idx].copy()

y_train = y.iloc[train_idx]
y_test = y.iloc[test_idx]

groups_train = groups.iloc[train_idx]
groups_test = groups.iloc[test_idx]

print("\n===== VEHICLE-AWARE SPLIT =====")
print("Training rows:", len(X_train))
print("Testing rows :", len(X_test))
print("Training vehicles:", groups_train.nunique())
print("Testing vehicles :", groups_test.nunique())


# =========================================================
# 6. MODELS
# =========================================================

models = {

    "Random Forest": RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    ),

    "Extra Trees": ExtraTreesRegressor(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    ),

    "Gradient Boosting": GradientBoostingRegressor(
        n_estimators=200,
        random_state=42
    ),

    "XGBoost": XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
        eval_metric="rmse",
        random_state=42,
        n_jobs=-1
    )
}


# =========================================================
# 7. CATBOOST
# =========================================================

catboost_model = CatBoostRegressor(
    iterations=300,
    depth=7,
    learning_rate=0.05,
    loss_function="RMSE",
    random_seed=42,
    verbose=False
)


# =========================================================
# 8. CROSS-VALIDATION
# =========================================================

cv = GroupKFold(n_splits=5)

results = []
trained_models = {}


# =========================================================
# 9. TRAIN SKLEARN + XGBOOST MODELS
# =========================================================

for name, model in models.items():

    print("\nTraining:", name)

    pipeline = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("model", model)
        ]
    )

    # -----------------------------------------------------
    # Train
    # -----------------------------------------------------

    pipeline.fit(X_train, y_train)

    # -----------------------------------------------------
    # Test prediction
    # -----------------------------------------------------

    y_pred = pipeline.predict(X_test)

    # -----------------------------------------------------
    # EXPORT XGBOOST ACTUAL VS PREDICTED VALUES
    # -----------------------------------------------------

    if name == "XGBoost":

        os.makedirs(
            "D:\\EV_TripPlanner\\results\\main",
            exist_ok=True
        )

        prediction_results = pd.DataFrame({
            "Actual_Energy_kWh": y_test.to_numpy(),
            "Predicted_Energy_kWh": y_pred
        })

        prediction_results.to_csv(
            "D:\\EV_TripPlanner\\results\\main\\xgboost_actual_vs_predicted.csv",
            index=False
        )

        print("\nActual vs Predicted energy values saved.")
        print(prediction_results.head(10))

    # -----------------------------------------------------
    # Test metrics
    # -----------------------------------------------------

    test_r2 = r2_score(
        y_test,
        y_pred
    )

    test_mae = mean_absolute_error(
        y_test,
        y_pred
    )

    test_rmse = mean_squared_error(
        y_test,
        y_pred
    ) ** 0.5

    # -----------------------------------------------------
    # Group-based 5-fold CV
    # -----------------------------------------------------

    cv_scores = cross_val_score(
        pipeline,
        X_train,
        y_train,
        groups=groups_train,
        cv=cv,
        scoring="r2",
        n_jobs=-1
    )

    cv_mean = cv_scores.mean()
    cv_std = cv_scores.std()

    # -----------------------------------------------------
    # Store results
    # -----------------------------------------------------

    results.append({
        "Model": name,
        "Test_R2": test_r2,
        "Test_MAE": test_mae,
        "Test_RMSE": test_rmse,
        "CV_R2_Mean": cv_mean,
        "CV_R2_Std": cv_std
    })

    trained_models[name] = pipeline

    print("Test R2   :", round(test_r2, 4))
    print("Test MAE  :", round(test_mae, 4))
    print("Test RMSE :", round(test_rmse, 4))
    print(
        "CV R2     :",
        round(cv_mean, 4),
        "+/-",
        round(cv_std, 4)
    )


# =========================================================
# 10. TRAIN CATBOOST
# =========================================================

print("\nTraining: CatBoost")

# Copy data because CatBoost handles categoricals directly

X_train_cat = X_train.copy()
X_test_cat = X_test.copy()

cat_indices = [
    X_train_cat.columns.get_loc(col)
    for col in categorical_features
]

catboost_model.fit(
    X_train_cat,
    y_train,
    cat_features=cat_indices
)

cat_pred = catboost_model.predict(
    X_test_cat
)


# =========================================================
# CATBOOST TEST METRICS
# =========================================================

cat_test_r2 = r2_score(
    y_test,
    cat_pred
)

cat_test_mae = mean_absolute_error(
    y_test,
    cat_pred
)

cat_test_rmse = mean_squared_error(
    y_test,
    cat_pred
) ** 0.5


# =========================================================
# CATBOOST GROUP CV
# =========================================================

cat_cv_scores = []

for train_fold, val_fold in cv.split(
    X_train_cat,
    y_train,
    groups=groups_train
):

    fold_model = CatBoostRegressor(
        iterations=300,
        depth=7,
        learning_rate=0.05,
        loss_function="RMSE",
        random_seed=42,
        verbose=False
    )

    fold_model.fit(
        X_train_cat.iloc[train_fold],
        y_train.iloc[train_fold],
        cat_features=cat_indices
    )

    fold_pred = fold_model.predict(
        X_train_cat.iloc[val_fold]
    )

    fold_r2 = r2_score(
        y_train.iloc[val_fold],
        fold_pred
    )

    cat_cv_scores.append(
        fold_r2
    )


cat_cv_mean = sum(cat_cv_scores) / len(cat_cv_scores)

cat_cv_std = (
    sum(
        (score - cat_cv_mean) ** 2
        for score in cat_cv_scores
    ) / len(cat_cv_scores)
) ** 0.5


# =========================================================
# STORE CATBOOST RESULTS
# =========================================================

results.append({
    "Model": "CatBoost",
    "Test_R2": cat_test_r2,
    "Test_MAE": cat_test_mae,
    "Test_RMSE": cat_test_rmse,
    "CV_R2_Mean": cat_cv_mean,
    "CV_R2_Std": cat_cv_std
})

trained_models["CatBoost"] = catboost_model

print("Test R2   :", round(cat_test_r2, 4))
print("Test MAE  :", round(cat_test_mae, 4))
print("Test RMSE :", round(cat_test_rmse, 4))
print(
    "CV R2     :",
    round(cat_cv_mean, 4),
    "+/-",
    round(cat_cv_std, 4)
)


# =========================================================
# 11. RESULTS TABLE
# =========================================================

results_df = pd.DataFrame(
    results
)

results_df = results_df.sort_values(
    "CV_R2_Mean",
    ascending=False
).reset_index(drop=True)

print("\n" + "=" * 75)
print("FINAL MAIN MODEL COMPARISON")
print("=" * 75)

print(
    results_df.to_string(
        index=False
    )
)


# =========================================================
# 12. SELECT FINAL MODEL
# =========================================================

# XGBoost is selected as the final model.
# Random Forest remains as the reference model.

best_name = "XGBoost"

best_model = trained_models[
    best_name
]

print(
    "\n🏆 SELECTED FINAL MODEL:",
    best_name
)

print(
    "Reference model: Random Forest"
)


# =========================================================
# 13. FEATURE IMPORTANCE
# =========================================================

print("\n" + "=" * 75)
print("FEATURE IMPORTANCE")
print("=" * 75)

model_inside_pipeline = best_model.named_steps[
    "model"
]

importances = (
    model_inside_pipeline.feature_importances_
)

feature_names = (
    best_model
    .named_steps["preprocess"]
    .get_feature_names_out()
)

importance_df = pd.DataFrame({
    "Feature": feature_names,
    "Importance": importances
})

importance_df = importance_df.sort_values(
    "Importance",
    ascending=False
)

print(
    importance_df.head(15).to_string(
        index=False
    )
)


# =========================================================
# 14. SAVE RESULTS
# =========================================================

os.makedirs(
    "D:\\EV_TripPlanner\\results\\main",
    exist_ok=True
)

results_df.to_csv(
    "D:\\EV_TripPlanner\\results\\main\\main_model_results.csv",
    index=False
)


# =========================================================
# 15. SAVE BEST MODEL
# =========================================================

os.makedirs(
    "D:\\EV_TripPlanner\\model\\main",
    exist_ok=True
)

joblib.dump(
    best_model,
    "D:\\EV_TripPlanner\\model\\main\\energy_model_main.pkl"
)


# =========================================================
# 16. DONE
# =========================================================

print("\n" + "=" * 75)
print("TRAINING COMPLETE")
print("=" * 75)

print(
    "Best model:",
    best_name
)

print(
    "Model saved:",
    "D:\\EV_TripPlanner\\model\\main\\energy_model_main.pkl"
)

print(
    "Results saved:",
    "D:\\EV_TripPlanner\\results\\main\\main_model_results.csv"
)

print(
    "Prediction file:",
    "D:\\EV_TripPlanner\\results\\main\\xgboost_actual_vs_predicted.csv"
)