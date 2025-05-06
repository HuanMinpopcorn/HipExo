import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore

class RealTimePlot:
    def __init__(self):
        self.app = QtWidgets.QApplication([])
        self.win = pg.GraphicsLayoutWidget(title="Admittance Control Monitor")
        self.win.resize(1000, 600)

        self.plot = self.win.addPlot(title="Torque vs Time")
        self.plot.showGrid(x=True, y=True)
        self.curve = self.plot.plot(pen='y')

        self.data_x = []  # time
        self.data_y = []  # torque

        self.ptr = 0
        self.max_points = 1000  # sliding window

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(20)  # update every 20ms

        self.win.show()

    def append(self, t, y):
        self.data_x.append(t)
        self.data_y.append(y)
        if len(self.data_x) > self.max_points:
            self.data_x = self.data_x[-self.max_points:]
            self.data_y = self.data_y[-self.max_points:]

    def update(self):
        self.curve.setData(self.data_x, self.data_y)
        if self.data_x:
            self.plot.setXRange(self.data_x[0], self.data_x[-1], padding=0.01)

    def start(self):
        self.app.exec_()
