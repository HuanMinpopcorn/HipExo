import serial
import time
import numpy as np
import matplotlib.pyplot as plt
import csv
from tqdm import tqdm
from NeuroLocoMiddleware.SoftRealtimeLoop import SoftRealtimeLoop

# === Global setup ===
load_cell_offset = 0.0
torque_log = []
time_log = []

# === Tare function ===
def tare_load_cell(ser):
    global load_cell_offset
    print("Taring load cell...")
    readings = []
    for _ in tqdm(range(1000)):
        torque = read_load_cell(ser, apply_offset=False)
        readings.append(torque)
        time.sleep(0.005)
    load_cell_offset = np.mean(readings)
    print(f"Done taring. Offset: {load_cell_offset:.3f} Nm")

# === Read torque from serial ===
def read_load_cell(ser, apply_offset=True):
    arm = 1.0
    while True:
        if ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                weight = float(line)
                torque = weight * arm
                if apply_offset:
                    torque -= load_cell_offset

                return torque
            except:
                continue
        else:
            continue

# === Setup serial ===
ser = serial.Serial('/dev/ttyUSB0', baudrate=115200, timeout=1)
tare_load_cell(ser)

# === CSV logger ===
import os

# Ensure the folder exists
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)

# Create the full path
csv_filename = os.path.join(log_folder, "torque_log.csv")
csv_file = open(csv_filename, mode='w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["Time (s)", "Torque (Nm)"])

# === Start real-time logging ===
start_time = time.time()
print("Recording... press Ctrl+C to stop.")
loop = SoftRealtimeLoop(dt=0.001)

try:
    for t in loop:
        torque = read_load_cell(ser)
        now = time.time() - start_time

        time_log.append(now)
        torque_log.append(torque)
        csv_writer.writerow([f"{now:.3f}", f"{torque:.3f}"])
except KeyboardInterrupt:
    print("\nRecording stopped.")
finally:
    csv_file.close()
    print(f"Saved to {csv_filename}")


