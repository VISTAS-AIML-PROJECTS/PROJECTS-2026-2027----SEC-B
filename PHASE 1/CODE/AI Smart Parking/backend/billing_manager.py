from math import ceil


HOURLY_RATES = {
    "Bike": 10,
    "Car": 20,
    "Bus": 40,
    "Truck": 40,
}


def calculate_dynamic_bill(vehicle_type, duration_minutes):
    base_rate = HOURLY_RATES.get(vehicle_type, HOURLY_RATES["Car"])
    hours = max(1, ceil(max(duration_minutes, 1) / 60))
    standard_hours = min(hours, 2)
    extended_hours = max(0, hours - 2)

    amount = (
        standard_hours * base_rate
        + extended_hours * base_rate * 1.5
    )

    return {
        "amount": round(amount, 2),
        "billable_hours": hours,
        "hourly_rate": base_rate,
        "vehicle_type": vehicle_type,
    }