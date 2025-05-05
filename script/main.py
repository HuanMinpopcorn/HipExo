import time
import numpy as np
from collections import deque
import serial 

from TMotorCANControl.mit_can import TMotorManager_mit_can
from NeuroLocoMiddleware.SoftRealtimeLoop import SoftRealtimeLoop

import matplotlib.pyplot as plt
import pandas as pd
import re
from tqdm import tqdm

# === Parameters for admittance control ===
M = 0.1   # virtual mass
B = 1.0    # virtual damping
K = 10.0    #  stiffness

# === Buffers ===
window_size = 10
theta_buffer = deque(maxlen=window_size)
omega_buffer = deque(maxlen=window_size)
torque_buffer = deque(maxlen=window_size)

# === Initialize Motor ===
Type = 'AK70-10'
ID = 1
# motor = TMotorManager_mit_can(motor_type=Type, motor_ID=ID)
with TMotorManager_mit_can(motor_type=Type, motor_ID=ID, max_mosfett_temp=80) as motor:
    # check motor connection 
    if motor.check_can_connection(): 
        motor.set_zero_position()
        time.sleep(1.5)  # allow motor to zero
        print("Motor can is conencted")
    else:
        print("Motor is disconencted")


# === Initialize Buffers ===
time_log = []
theta_log = []
omega_log = []
torque_log = []
dtheta_desired_log = []

# === Tare Load Cell (custom function depending on your setup) ===
load_cell_offset = 0.0

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
    arm = 0.15  # arm length in meters  
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


ser = serial.Serial(port='/dev/ttyUSB0', baudrate=115200, timeout=1)
tare_load_cell(ser)

# set up reference values
theta_ref = 0.0
omega_ref = 0.0
dtheta_desired = 0.0

# === Apply low-pass filter ===
def low_pass_filter(data, alpha=0.2):
    filtered = []
    for i, val in enumerate(data):
        if i == 0:
            filtered.append(val)
        else:
            filtered.append(alpha * val + (1 - alpha) * filtered[i-1])
    return filtered
# === Run Admittance Control at 1kHz ===
print("Starting read only demo. Press ctrl+C to quit.")
loop = SoftRealtimeLoop(dt=0.001, report=True, fade=0)
tic = time.time()
alpha = 0.01    
torque_filtered = 0.0  # initial filtered value
try :
    for t in loop:
        motor.update()
        # Read motor state
        theta = motor._motor_state.position 
        omega = motor._motor_state.velocity
        current = motor._motor_state.current
        # torque = np.sin(2*3.142*0.5*t)
        torque = read_load_cell(ser)
        torque_filtered = alpha * torque + (1 - alpha) * torque_filtered  # ← updated filter

        # print(theta, omega, torque)


        # Desired velocity from admittance control:
        # τ = Mθ̈ + Bθ̇ + Kθ

        # dtheta_desired = (torque - K * theta - M * theta_ddot) / B
        theta_ddot = torque_filtered / M - B * (omega - omega_ref) / M - K * (theta - theta_ref) / M
        dtheta_desired = theta_ddot * loop.dt  + omega
        # send the command 
        motor.set_speed_gains(kd=10.0)
        motor.velocity = dtheta_desired
        # Store data for plotting
        time_log.append(t)
        theta_log.append(theta)
        omega_log.append(omega)
        torque_log.append(torque_filtered)
        dtheta_desired_log.append(dtheta_desired)
        toc = time.time()
        print(f"theta: {theta:.3f} rad, omega: {omega:.3f} rad/s, torque: {torque:.3f} Nm, dtheta_desired: {dtheta_desired:.3f} rad/s, time = {toc -tic:.3f}", end='\r')


       

except KeyboardInterrupt:
    print("Stopping...")

finally:
    # Save log
    data = pd.DataFrame({
        'time_s': time_log,
        'theta_rad': theta_log,
        'omega_rad_s': omega_log,
        'torque_Nm': torque_log,
        'desired_velocity_rad_s': dtheta_desired_log
    })

    data.to_csv("admittance_control_log.csv", index=False)
    print("Saved data to admittance_control_log.csv")
    # Close serial port
    ser.close()
    print("Serial port closed.")
   
