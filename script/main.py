import time
import numpy as np
from collections import deque
import serial 

from TMotorCANControl.mit_can import TMotorManager_mit_can
from NeuroLocoMiddleware.SoftRealtimeLoop import SoftRealtimeLoop

import matplotlib.pyplot as plt
import pandas as pd
import re

# === Parameters for admittance control ===
M = 0.5    # virtual mass
B = 0.2    # virtual damping
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


# === For plotting ===
plt.ion()  # Turn on interactive mode
fig, axs = plt.subplots(4, 1, figsize=(10, 8))
lines = []

for ax, label, color in zip(
    axs,
    ['Theta (rad)', 'Omega (rad/s)', 'Torque (Nm)', 'Desired Velocity (rad/s)'],
    ['blue', 'orange', 'green', 'red']
):
    line, = ax.plot([], [], color=color, label=label)
    ax.set_ylabel(label)
    ax.legend()
    lines.append(line)

axs[-1].set_xlabel('Time (s)')
# For real-time plotting
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
    for _ in range(1000):
        torque = read_load_cell(ser, apply_offset=False)
        readings.append(torque)
        time.sleep(0.01)
    load_cell_offset = np.mean(readings)
    print(f"Done taring. Offset: {load_cell_offset:.3f} Nm")

def read_load_cell(ser, apply_offset=True):
    arm = 0.15  # 15 cm
    while True:
        if ser.in_waiting > 0:
            # weight = ser.readline().decode('utf-8', errors='replace').strip()
            
            line = ser.readline().decode('utf-8', errors='replace').strip()

            match = re.search(r'[-+]?[0-9]*\.?[0-9]+', line)  # regex for a float
            if match:
                weight = float(match.group())
                torque = weight * arm
                if apply_offset:
                    torque -= load_cell_offset
                return torque
            else:
                print(f"Invalid reading: {line}")
        else:
            print("\r" + "no load cell reading", end='')

ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, timeout=1)
tare_load_cell(ser)

theta_ref = 0.0



# === Run Admittance Control at 1kHz ===
print("Starting read only demo. Press ctrl+C to quit.")
loop = SoftRealtimeLoop(dt=0.001, report=True, fade=0)
try :
    for t in loop:
        motor.update()
        theta = motor.get_motor_angle_radians
        omega = motor.get_motor_velocity_radians_per_second
        torque = read_load_cell(ser)
        print()

        # Append to buffer
        theta_buffer.append(theta)
        omega_buffer.append(omega)
        torque_buffer.append(torque)

        # Wait until we have enough data
        if len(theta_buffer) < window_size:
            continue

        # Estimate θ̇ (velocity) and θ̈ (acceleration)
        theta_dot = np.gradient(theta_buffer, loop.dt)[-1]
        theta_ddot = np.gradient(omega_buffer, loop.dt)[-1]

        # Desired velocity from admittance control:
        # τ = Mθ̈ + Bθ̇ + Kθ

        dtheta_desired = (torque - K * theta - M * theta_ddot) / B

        # send the command 
        # motor.set_speed_gains(kd=3.0)
        # motor.velocity = dtheta_desired
            # Store data for plotting
        time_log.append(t)
        theta_log.append(theta)
        omega_log.append(theta_dot)
        torque_log.append(torque)
        dtheta_desired_log.append(dtheta_desired)

        # Limit plot window to last 5 seconds (optional)
        if len(time_log) > 100:
            time_log = time_log[-5000:]
            theta_log = theta_log[-5000:]
            omega_log = omega_log[-5000:]
            torque_log = torque_log[-5000:]
            dtheta_desired_log = dtheta_desired_log[-5000:]


        # Update plot data
        lines[0].set_data(t, theta)  # the motor position 
        lines[1].set_data(t, omega)  # the motor current velocity 
        lines[2].set_data(t, torque) # the load cell reading 
        lines[3].set_data(t, dtheta_desired) # command velocity

        # Adjust x/y limits dynamically
        for i, data in enumerate([theta, omega, torque, dtheta_desired]):
            axs[i].relim()
            axs[i].autoscale_view()

        plt.pause(0.001)

except KeyboardInterrupt:
    print("Stopping...")
finally:
    # plt.ioff()
    # plt.show()

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