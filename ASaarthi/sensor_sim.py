# sensor_sim.py
# Simulates water sensor readings and posts them to the Django API.

import random
import time
import requests

URL = "http://127.0.0.1:8000/api/water/post/"

# ----------------------------
# STATES & DISTRICTS
# ----------------------------
STATE_DISTRICTS = {
    "Assam": ["Kamrup", "Dibrugarh", "Jorhat", "Tinsukia", "Barpeta"],
    "Arunachal Pradesh": ["Itanagar", "Tawang", "Pasighat", "Ziro", "Roing"],
    "Manipur": ["Imphal West", "Imphal East", "Thoubal", "Bishnupur"],
    "Meghalaya": ["Shillong", "Tura", "Jowai", "Nongpoh"],
    "Mizoram": ["Aizawl", "Lunglei", "Champhai", "Kolasib"],
    "Nagaland": ["Kohima", "Dimapur", "Mokokchung", "Tuensang"],
    "Tripura": ["Agartala", "Udaipur", "Dharmanagar", "Kailashahar"],
}

# ----------------------------
# GENERATE VILLAGES & BASELINE DATA
# ----------------------------
villages = []
for state, districts in STATE_DISTRICTS.items():
    for d in districts:
        villages.append({
            "name": d,
            "state": state,
            "lat": round(random.uniform(25.5, 27.5), 4),
            "lng": round(random.uniform(91.0, 95.0), 4),
        })

# Baseline safe water values per village
baseline = {
    v["name"]: {
        "ph": round(random.uniform(6.5, 7.5), 2),
        "turbidity": round(random.uniform(1.0, 4.0), 2),
        "tds": round(random.uniform(150, 300), 1),
    }
    for v in villages
}

# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def fluctuate(value, low, high, step=0.2):
    """Randomly fluctuate a value within a step and bounds."""
    new_val = value + random.uniform(-step, step)
    return round(max(low, min(high, new_val)), 2)

def inject_warning_or_unsafe(village_values):
    """
    Randomly inject warning or unsafe water values:
      - 10% chance for unsafe
      - 20% chance for warning
    """
    chance = random.random()
    if chance < 0.1:  # Unsafe
        village_values["ph"] = round(random.choice([5.0, 9.0]), 2)
        village_values["turbidity"] = round(random.uniform(6, 12), 2)
        village_values["tds"] = round(random.uniform(501, 700), 1)
    elif chance < 0.3:  # Warning
        village_values["ph"] = round(random.choice([6.0, 8.6]), 2)
        village_values["turbidity"] = round(random.uniform(5, 6), 2)
        village_values["tds"] = round(random.uniform(400, 500), 1)
    # Otherwise, keep baseline (normal) values


# ----------------------------
# MAIN LOOP: SIMULATE & SEND DATA
# ----------------------------
while True:
    v = random.choice(villages)
    b = baseline[v["name"]]

    # Slightly fluctuate baseline
    b["ph"] = fluctuate(b["ph"], 5.4, 8.8, step=0.1)
    b["turbidity"] = fluctuate(b["turbidity"], 0.5, 12.0, step=0.3)
    b["tds"] = round(fluctuate(b["tds"], 50, 700, step=10), 1)

    # Inject occasional warning/unsafe values
    inject_warning_or_unsafe(b)

    # Prepare payload
    data = {
        "village": v["name"],
        "state": v["state"],
        "ph": b["ph"],
        "turbidity": b["turbidity"],
        "tds": b["tds"],
        "lat": v["lat"],
        "lng": v["lng"],
    }

    # Send POST request
    try:
        r = requests.post(URL, json=data, timeout=5)
        print("Sent:", data, "->", r.status_code, r.text)
    except Exception as e:
        print("Error sending data:", e)

    time.sleep(3)
