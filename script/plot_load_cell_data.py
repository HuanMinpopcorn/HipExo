import serial
import time
import numpy as np
import matplotlib.pyplot as plt
import csv
from tqdm import tqdm
from NeuroLocoMiddleware.SoftRealtimeLoop import SoftRealtimeLoop
import pandas as pd

# Load CSV file
df = pd.read_csv("logs/torque_log.csv")

# Preview
# print(df.head())  # Print the first few rows

# Access columns
time_log = df["Time (s)"]
torque_log = df["Torque (Nm)"]

# === Apply low-pass filter ===
def low_pass_filter(data, alpha=0.2):
    filtered = []
    for i, val in enumerate(data):
        if i == 0:
            filtered.append(val)
        else:
            filtered.append(alpha * val + (1 - alpha) * filtered[i-1])
    return filtered

filtered_torque = low_pass_filter(torque_log, alpha=0.01) 
torque_log_arm = np.array(filtered_torque) * 0.15
# === Static Plot ===
plt.figure(figsize=(10, 4))
plt.plot(time_log, torque_log_arm , lw=1.5)
plt.xlabel("Time (s)")
plt.ylabel("Torque (Nm)")
plt.title("Recorded Torque from Load Cell")
plt.grid(True)
plt.tight_layout()
plt.show()