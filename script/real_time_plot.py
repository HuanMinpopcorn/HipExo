from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
from functools import partial

class RealTimePlotWidget(QtWidgets.QWidget):
    def __init__(self, data_queue, param_holder=None, start_callback=None, stop_callback=None):
        super().__init__()
        self.queue = data_queue
        self.params = param_holder
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.plot_enabled = True
        self.max_points = 500

        # Initialize plot buffers
        self.buffers = {k: [] for k in ["time", "torque", "theta", "omega", "dtheta_desired"]}

        # Layout
        main_layout = QtWidgets.QHBoxLayout()
        self.setLayout(main_layout)

        # === Plot Area ===
        plot_container = QtWidgets.QVBoxLayout()
        self.plot_widget = pg.GraphicsLayoutWidget()
        plot_container.addWidget(self.plot_widget)
        self.plots = {}
        self.curves = {}

        for i, name in enumerate(["torque", "theta", "omega", "dtheta_desired"]):
            plot = self.plot_widget.addPlot(title=f"{name} vs Time")
            plot.showGrid(x=True, y=True)
            plot.setLabel('left', name)
            plot.setLabel('bottom', 'Time (s)')
            curve = plot.plot(pen=pg.intColor(i))
            self.plots[name] = plot
            self.curves[name] = curve
            if i < 3:
                self.plot_widget.nextRow()

        main_layout.addLayout(plot_container)

        # === Parameter Controls + Buttons ===
        param_layout = QtWidgets.QFormLayout()
        param_box = QtWidgets.QGroupBox("Control Parameters")
        param_box.setLayout(param_layout)

        self.spins = {}
        for key, minv, maxv, step in [
            ("M", 0.0001, 0.01, 0.0001),
            ("B", 0.0, 5.0, 0.01),
            ("K", 0.0, 100.0, 1.0),
            ("alpha", 0.0, 1.0, 0.01),
        ]:
            spin = QtWidgets.QDoubleSpinBox()
            spin.setRange(minv, maxv)
            spin.setSingleStep(step)
            spin.setDecimals(4)
            spin.setValue(getattr(self.params, key))
            spin.valueChanged.connect(partial(self.set_param_value, key))
            param_layout.addRow(f"{key}:", spin)
            self.spins[key] = spin

        # === Buttons ===
        self.start_button = QtWidgets.QPushButton("Start Control Loop")
        self.start_button.clicked.connect(self.handle_start)
        param_layout.addRow(self.start_button)

        self.stop_button = QtWidgets.QPushButton("Stop Control Loop")
        self.stop_button.clicked.connect(self.handle_stop)
        param_layout.addRow(self.stop_button)

        main_layout.addWidget(param_box)

        # === Timer for Plot Refresh ===
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(50)

    def set_param_value(self, key, val):
        setattr(self.params, key, val)

    def handle_start(self):
        if self.start_callback:
            self.reset_plot_buffers()
            self.plot_enabled = True
            self.start_callback()

    def handle_stop(self):
        if self.stop_callback:
            self.stop_callback()
        self.plot_enabled = False

    def reset_plot_buffers(self):
        self.buffers = {k: [] for k in ["time", "torque", "theta", "omega", "dtheta_desired"]}

    def update_plot(self):
        if not self.plot_enabled:
            return

        while not self.queue.empty():
            t, torque, theta, omega, dtheta_desired = self.queue.get()
            self.buffers["time"].append(t)
            self.buffers["torque"].append(torque)
            self.buffers["theta"].append(theta)
            self.buffers["omega"].append(omega)
            self.buffers["dtheta_desired"].append(dtheta_desired)

        for key in self.buffers:
            if len(self.buffers[key]) > self.max_points:
                self.buffers[key] = self.buffers[key][-self.max_points:]

        for key in self.curves:
            self.curves[key].setData(self.buffers["time"], self.buffers[key])
            if self.buffers["time"]:
                self.plots[key].setXRange(self.buffers["time"][0], self.buffers["time"][-1], padding=0.01)
