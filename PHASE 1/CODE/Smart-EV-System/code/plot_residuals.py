import pandas as pd
import matplotlib.pyplot as plt

# Load XGBoost predictions
file = r"D:\EV_TripPlanner\results\main\xgboost_actual_vs_predicted.csv"

df = pd.read_csv(file)

actual = df["Actual_Energy_kWh"]
predicted = df["Predicted_Energy_kWh"]

# Residual = Actual - Predicted
residual = actual - predicted

# Create residual plot
plt.figure(figsize=(7, 5))

plt.scatter(
    predicted,
    residual,
    s=18,
    alpha=0.6
)

# Zero-error reference line
plt.axhline(
    y=0,
    linestyle="--"
)

plt.xlabel("Predicted Energy Consumption (kWh)")
plt.ylabel("Residual Error (kWh)")
plt.title("Residual Error Plot for XGBoost")

plt.tight_layout()

# Save figure
output = r"D:\EV_TripPlanner\results\main\xgboost_residual_plot.png"

plt.savefig(
    output,
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("Residual plot saved:")
print(output)