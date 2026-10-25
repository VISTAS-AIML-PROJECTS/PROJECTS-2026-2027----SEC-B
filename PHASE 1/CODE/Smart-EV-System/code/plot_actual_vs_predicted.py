import pandas as pd
import matplotlib.pyplot as plt

# Load XGBoost test predictions
file = r"D:\EV_TripPlanner\results\main\xgboost_actual_vs_predicted.csv"

df = pd.read_csv(file)

actual = df["Actual_Energy_kWh"]
predicted = df["Predicted_Energy_kWh"]

# Create plot
plt.figure(figsize=(7, 5))

plt.scatter(
    actual,
    predicted,
    s=18,
    alpha=0.6
)

# Perfect prediction line
min_value = min(actual.min(), predicted.min())
max_value = max(actual.max(), predicted.max())

plt.plot(
    [min_value, max_value],
    [min_value, max_value],
    linestyle="--"
)

plt.xlabel("Actual Energy Consumption (kWh)")
plt.ylabel("Predicted Energy Consumption (kWh)")
plt.title("Actual vs. Predicted Energy Consumption Using XGBoost")

plt.tight_layout()

# Save figure
output = r"D:\EV_TripPlanner\results\main\xgboost_actual_vs_predicted.png"

plt.savefig(
    output,
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("Plot saved:")
print(output)