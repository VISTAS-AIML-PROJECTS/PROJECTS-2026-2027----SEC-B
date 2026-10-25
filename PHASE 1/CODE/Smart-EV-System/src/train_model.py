import joblib
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

from src.database import load_trips_as_dataframe
from config.settings import SAVED_MODEL_PATH

def train_chennai_model():
    print("Fetching trip dataset directly from MongoDB 'ev_trips'...")
    df = load_trips_as_dataframe()
    
    if df.empty:
        print("Error: No trips found in MongoDB. Ensure data_generator.py has finished.")
        return

    print(f"Loaded {len(df)} trips from MongoDB.")

    features = [
        "Manufacturer", "Model", "Year", "Battery_Capacity_kWh", "Motor_Power_kW",
        "Vehicle_Weight_kg", "Distance_km", "Avg_Speed", "Ambient_Temp_C",
        "Weather", "Road_Type", "SOH_pct", "Driving_Style"
    ]
    target = "Energy_Consumed_kWh"

    X = df[features]
    y = df[target]

    categorical = ["Manufacturer", "Model", "Weather", "Road_Type", "Driving_Style"]
    numeric = [col for col in features if col not in categorical]

    # Preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
            ("num", "passthrough", numeric),
        ]
    )

    # XGBoost regression pipeline
    model = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", XGBRegressor(
            n_estimators=180,
            learning_rate=0.07,
            max_depth=5,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=42
        ))
    ])

    # 80/20 train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training XGBoost regression model on Chennai district data...")
    model.fit(X_train, y_train)

    # Evaluation
    predictions = model.predict(X_test)
    r2 = r2_score(y_test, predictions)
    mae = mean_absolute_error(y_test, predictions)
    rmse = mean_squared_error(y_test, predictions) ** 0.5

    print("\n==========================================")
    print("       MODEL VALIDATION RESULTS           ")
    print("==========================================")
    print(f"Held-out Test R²: {r2:.4f}")
    print(f"Mean Absolute Error (MAE): {mae:.4f} kWh")
    print(f"Root Mean Squared Error (RMSE): {rmse:.4f} kWh")
    print("==========================================\n")

    SAVED_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, SAVED_MODEL_PATH)
    print(f"Model saved successfully to: {SAVED_MODEL_PATH}")

if __name__ == "__main__":
    train_chennai_model()