import time
import numpy as np
import pandas as pd
from tqdm import tqdm
import serial
from queue import Queue
from PyQt5 import QtWidgets

from real_time_plot import RealTimePlotWidget
from TMotorCANControl.mit_can import TMotorManager_mit_can
from NeuroLocoMiddleware.SoftRealtimeLoop import SoftRealtimeLoop
from dataclasses import dataclass

@dataclass
class ControlParams:
    M: float = 0.001
    B: float = 0.2
    K: float = 20.0
    alpha: float = 0.1

class AdmittanceControl:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200, motor_type='AK70-10', motor_id=1,
                 param_holder=ControlParams(), arm_length=0.15, frequency=1000, plot_enabled=True, plot_queue=None):
        self.port = port
        self.baudrate = baudrate
        self.motor_type = motor_type
        self.motor_id = motor_id
        self.M = param_holder.M
        self.B = param_holder.B
        self.K = param_holder.K
        self.ARM_LENGTH = arm_length
        self.ALPHA = param_holder.alpha
        self.FREQUENCY = frequency
        self.plot_enabled = plot_enabled
        self.plot_queue = plot_queue if plot_enabled else None
        self.ser = None

        self.time_log = []
        self.theta_log = []
        self.omega_log = []
        self.torque_log = []
        self.dtheta_desired_log = []

        self.load_cell_offset = 0.0


    def read_load_cell(self):
        while True:
            if self.ser.in_waiting > 0:
                try:
                    line = self.ser.readline().decode('utf-8', errors='replace').strip()
                    weight = float(line)
                    torque = weight * self.ARM_LENGTH
                    if self.load_cell_offset:
                        torque -= self.load_cell_offset
                    return torque
                except:
                    continue

    def tare_load_cell(self):
        print("Taring load cell...")
        readings = []
        for _ in tqdm(range(100)):
            torque = self.read_load_cell()
            readings.append(torque)
            time.sleep(0.005)
        self.load_cell_offset = np.mean(readings)
        print(f"Done taring. Offset: {self.load_cell_offset:.3f} Nm")

    def save_log(self):
        data = pd.DataFrame({
            'time_s': self.time_log,
            'theta_rad': self.theta_log,
            'omega_rad_s': self.omega_log,
            'torque_Nm': self.torque_log,
            'desired_velocity_rad_s': self.dtheta_desired_log
        })
        data.to_csv("admittance_control_log.csv", index=False)
        print("Saved data to admittance_control_log.csv")

    def run(self, stop_flag_func=None):
        self.ser = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=1)
        self.tare_load_cell()

        with TMotorManager_mit_can(motor_type=self.motor_type, motor_ID=self.motor_id, max_mosfett_temp=80) as motor:
            if motor.check_can_connection():
                motor.set_zero_position()
                time.sleep(3)
                print("Motor connected and zeroed.")
            else:
                print("Motor not connected.")
                return

            motor.set_speed_gains(kd=3.0)

            theta_ref = 0.0
            omega_ref = 0.0
            torque_filtered = 0.0

            loop = SoftRealtimeLoop(dt=1/self.FREQUENCY, report=True, fade=0)
            tic = time.time()

            try:
                for t in loop:
                    if stop_flag_func and stop_flag_func():
                        print("\nStopping loop as requested.")
                        motor.velocity = 0.0
                        break
                    motor.update()
                    theta = motor._motor_state.position
                    omega = motor._motor_state.velocity
                    current = motor._motor_state.current

                    torque = self.read_load_cell()
                    torque_filtered = self.ALPHA * torque + (1 - self.ALPHA) * torque_filtered

                    theta_ddot = torque_filtered / self.M - self.B * (omega - omega_ref) / self.M - self.K * (theta - theta_ref) / self.M
                    dtheta_desired = theta_ddot * loop.dt + omega
                    dtheta_desired = np.clip(dtheta_desired, -1.0, 1.0)
                    motor.velocity = dtheta_desired

                    self.time_log.append(t)
                    self.theta_log.append(theta)
                    self.omega_log.append(omega)
                    self.torque_log.append(torque_filtered)
                    self.dtheta_desired_log.append(dtheta_desired)

                    toc = time.time()
                    print(f"\u03b8: {theta:.3f} rad, \u03c9: {omega:.3f} rad/s, \u03c4: {torque_filtered:.3f} Nm, \u03c9*: {dtheta_desired:.3f} rad/s, t={toc - tic:.3f}s", end='\r')

                    if self.plot_enabled:
                        self.plot_queue.put((t, torque_filtered, theta, omega, dtheta_desired))

            except KeyboardInterrupt:
                print("\nAdmittance control interrupted by user.")

            finally:
                self.save_log()
                self.ser.close()
                print("Serial port closed.")


if __name__ == "__main__":
    control = AdmittanceControl()
    control.run()