import threading
import queue
import sys
from PyQt5 import QtWidgets
from admittance_control import AdmittanceControl, ControlParams
from real_time_plot import RealTimePlotWidget

# Dummy second thread task
def background_logger(log_queue):
    while True:
        try:
            msg = log_queue.get(timeout=1)
            print(f"[Logger] {msg}")
        except queue.Empty:
            continue

def main():
    # Monkey-patch signal to avoid thread crash
    import signal
    _orig_signal = signal.signal
    signal.signal = lambda sig, handler: _orig_signal(sig, handler) if threading.current_thread() is threading.main_thread() else print(f"[Warning] signal {sig} skipped in non-main thread")

    # Shared state
    param_holder = ControlParams()
    data_queue = queue.Queue()
    log_queue = queue.Queue()

    # Thread 1: Admittance Control
    controller = AdmittanceControl(param_holder=param_holder, plot_enabled=True, plot_queue=data_queue)
    thread_control = threading.Thread(target=controller.run, daemon=True)
    thread_control.start()

    # Thread 2: Logger
    thread_logger = threading.Thread(target=background_logger, args=(log_queue,), daemon=True)
    thread_logger.start()

    # Qt GUI: must run in main thread
    app = QtWidgets.QApplication(sys.argv)
    plot = RealTimePlotWidget(data_queue)
    plot.setWindowTitle("Real-Time Admittance Plot")
    plot.resize(1000, 800)
    plot.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
