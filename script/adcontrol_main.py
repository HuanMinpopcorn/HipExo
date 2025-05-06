import sys
import threading
import queue
import signal
from PyQt5 import QtWidgets
from admittance_control import AdmittanceControl, ControlParams
from real_time_plot import RealTimePlotWidget

# Monkey patch signal.signal to allow SoftRealtimeLoop in background thread
_original_signal = signal.signal
def safe_signal(sig, handler):
    if threading.current_thread() is threading.main_thread():
        return _original_signal(sig, handler)
    else:
        print(f"[Warning] Skipped signal {sig} in background thread.")
        return None
signal.signal = safe_signal

# Shared flags and controller setup
should_stop = False
control_thread = None
controller = None  # This will be initialized in main()

def start_controller():
    global should_stop, control_thread, controller
    if control_thread and control_thread.is_alive():
        print("Control loop already running.")
        return
    print("Starting control loop...")
    should_stop = False
    control_thread = threading.Thread(
        target=lambda: controller.run(lambda: should_stop),
        daemon=True
    )
    control_thread.start()

def stop_controller():
    global should_stop
    print("Stopping control loop...")
    should_stop = True

def main():
    global controller

    # Shared data structures
    param_holder = ControlParams()
    data_queue = queue.Queue()

    # Create controller instance (do not start thread yet)
    controller = AdmittanceControl(
        port='/dev/ttyUSB0',
        motor_type='AK70-10',
        motor_id=1,
        param_holder=param_holder,
        plot_enabled=True,
        plot_queue=data_queue,
        frequency=1000,
    )

    # Start GUI
    app = QtWidgets.QApplication(sys.argv)
    plot = RealTimePlotWidget(
        data_queue,
        param_holder,
        start_callback=start_controller,
        stop_callback=stop_controller
    )
    plot.setWindowTitle("Admittance Control GUI")
    plot.resize(1200, 800)
    plot.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
