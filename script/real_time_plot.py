from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

class RealTimePlotWidget(QtWidgets.QWidget):
    def __init__(self, data_queue):
        super().__init__()
        self.queue = data_queue
        self.max_points = 500
        self.buffers = {
            "time": [],
            "torque": [],
            "theta": [],
            "omega": [],
            "dtheta_desired": []
        }

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.plot_widget = pg.GraphicsLayoutWidget()
        layout.addWidget(self.plot_widget)

        self.plots = {}
        self.curves = {}
        for i, name in enumerate(["torque", "theta", "omega", "dtheta_desired"]):
            plot = self.plot_widget.addPlot(title=f"{name} vs Time")
            plot.showGrid(x=True, y=True)
            curve = plot.plot(pen=pg.intColor(i))
            plot.setLabel('left', name)
            plot.setLabel('bottom', 'Time', units='s')
            self.plots[name] = plot
            self.curves[name] = curve
            if i < 3:
                self.plot_widget.nextRow()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(50)

    def update_plot(self):
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
