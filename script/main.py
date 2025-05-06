import time
import numpy as np
import pandas as pd
from tqdm import tqdm
import serial
from real_time_plot import RealTimePlot
from TMotorCANControl.mit_can import TMotorManager_mit_can
from NeuroLocoMiddleware.SoftRealtimeLoop import SoftRealtimeLoop

# === Parameters for admittance control ===
M = 0.001  # virtual mass
B = 0.2     # virtual damping
K = 20.0    # stiffness
ARM_LENGTH = 0.15  # m
ALPHA = 0.1       # for low-pass filter

# === Global buffer logs ===
time_log = []
theta_log = []
omega_log = []
torque_log = []
dtheta_desired_log = []

# === Global offset ===
load_cell_offset = 0.0

def read_load_cell(ser, apply_offset=True):
    """Reads and converts load cell data from serial to torque."""
    while True:
        if ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                weight = float(line)
                torque = weight * ARM_LENGTH
                if apply_offset:
                    torque -= load_cell_offset
                return torque
            except:
                continue

def tare_load_cell(ser):
    """Collects samples and calculates load cell zero-offset."""
    global load_cell_offset
    print("Taring load cell...")
    readings = []
    for _ in tqdm(range(1000)):
        torque = read_load_cell(ser, apply_offset=False)
        readings.append(torque)
        time.sleep(0.005)
    load_cell_offset = np.mean(readings)
    print(f"Done taring. Offset: {load_cell_offset:.3f} Nm")

def run_admittance_control(motor, ser):
    """Main admittance control loop."""
    global time_log, theta_log, omega_log, torque_log, dtheta_desired_log
    print("Starting admittance demo. Press Ctrl+C to quit.")
    plotter = RealTimePlot()  # ← initialize PyQtGraph plot
    motor.set_speed_gains(kd=3.0)

    theta_ref = 0.0
    omega_ref = 0.0
    torque_filtered = 0.0

    loop = SoftRealtimeLoop(dt=0.001, report=True, fade=0)
    tic = time.time()

    try:
        for t in loop:
            motor.update()
            theta = motor._motor_state.position
            omega = motor._motor_state.velocity
            current = motor._motor_state.current

            torque = read_load_cell(ser)
            torque_filtered = ALPHA * torque + (1 - ALPHA) * torque_filtered

            theta_ddot = torque_filtered / M - B * (omega - omega_ref) / M - K * (theta - theta_ref) / M
            dtheta_desired = theta_ddot * loop.dt + omega

            # Command desired velocity
            # motor.velocity = 0.2  # You can change to dtheta_desired if needed
            motor.velocity = dtheta_desired

            # Log data
            time_log.append(t)
            theta_log.append(theta)
            omega_log.append(omega)
            torque_log.append(torque_filtered)
            dtheta_desired_log.append(dtheta_desired)

            toc = time.time()
            print(f"θ: {theta:.3f} rad, ω: {omega:.3f} rad/s, τ: {torque_filtered:.3f} Nm, ω*: {dtheta_desired:.3f} rad/s, t={toc - tic:.3f}s", end='\r')

            plotter.append(t, torque_filtered)

    except KeyboardInterrupt:
        print("\nAdmittance control interrupted by user.")

    finally:
        save_log()
        ser.close()
        print("Serial port closed.")

def save_log():
    """Saves the control data to CSV."""
    data = pd.DataFrame({
        'time_s': time_log,
        'theta_rad': theta_log,
        'omega_rad_s': omega_log,
        'torque_Nm': torque_log,
        'desired_velocity_rad_s': dtheta_desired_log
    })
    data.to_csv("admittance_control_log.csv", index=False)
    print("Saved data to admittance_control_log.csv")

def main():
    """Entry point for the admittance control script."""
    ser = serial.Serial(port='/dev/ttyUSB0', baudrate=115200, timeout=1)
    tare_load_cell(ser)

    Type = 'AK70-10'
    ID = 1
    with TMotorManager_mit_can(motor_type=Type, motor_ID=ID, max_mosfett_temp=80) as motor:
        if motor.check_can_connection():
            motor.set_zero_position()
            time.sleep(1.5)
            print("Motor connected and zeroed.")
        else:
            print("Motor not connected.")
            return

        run_admittance_control(motor, ser)

if __name__ == "__main__":
    main()
