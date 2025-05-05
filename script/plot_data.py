import matplotlib.pyplot as plt
import pandas as pd

def main():
    # Load CSV
    data = pd.read_csv("admittance_control_log.csv")

    # Extract data
    time_log = data['time_s']
    theta_log = data['theta_rad']
    omega_log = data['omega_rad_s']
    torque_log = data['torque_Nm']
    dtheta_desired_log = data['desired_velocity_rad_s']

    # Plot setup
    fig, axs = plt.subplots(4, 1, figsize=(10, 10))
    labels = ['Theta (rad)', 'Omega (rad/s)', 'Torque (Nm)', 'Desired Velocity (rad/s)']
    logs = [theta_log, omega_log, torque_log, dtheta_desired_log]
    colors = ['blue', 'orange', 'green', 'red']

    frequency = 1 / (time_log[1] - time_log[0])


    # Plot each subplot
    for ax, label, log, color in zip(axs, labels, logs, colors):
        ax.plot(time_log, log, color=color, label=label)
        ax.set_ylabel(label)
        ax.grid(True)
        ax.legend()
        ax.title.set_text(str(frequency) +  "Hz")

    axs[-1].set_xlabel('Time (s)')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()