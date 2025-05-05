# Admittance Control for HipExo 

**Author**: Huan Min  
**Last Updated**: May 2025

## 📋 Description

This project implements real-time admittance control for a motor (e.g., **AK70-10**) using load cell torque feedback. The system computes a desired joint velocity from torque input and logs key motor signals for further analysis.

The system supports:
- Real-time admittance control at 1kHz
- Serial communication with a load cell
- Live plotting of joint position, velocity, torque, and desired velocity
- Logging to CSV for offline analysis
- Static plotting of saved logs

---

## 📁 Project Contents

- `main.py` – Runs the control loop, logging, and real-time plotting
- `plot_log.py` – Plots data from the recorded CSV log
- `admittance_control_log.csv` – Example log file (output from `main.py`)
- `README.md` – This documentation

---

## 🔧 Requirements

- Python 3.8+
- Python packages:
  - `numpy`
  - `pandas`
  - `matplotlib`
  - `pyserial`
- Custom packages:
  - `TMotorCANControl` (for MIT CAN motor interface)
  - `NeuroLocoMiddleware` (for soft real-time loop)

---

## 🛠️ Setup Instructions

1. Connect the **T-Motor AK70-10** to your computer via CAN bus.
2. Connect the **load cell** to a serial port (default: `/dev/ttyUSB0`).
3. Clone or copy the repo files into your Python workspace.
4. Edit `main.py` to match your motor ID and serial port if necessary.
5. Run the control script:

```bash
python main.py
```






