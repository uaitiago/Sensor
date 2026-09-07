import sys
import serial
import serial.tools.list_ports
import time
import pandas as pd

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import pyqtgraph as pg
import pyqtgraph.exporters as exporters


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Hugo José's Lab - NEOS Multifunction")
        self.resize(1250, 750)

        # ============================================================
        # DATA AND CONTROL
        # ============================================================

        self.serial_port = None
        self.is_measuring = False
        self.measurements = {}

        self.current_x = []
        self.current_y = []

        self.start_time = 0
        self.count = 1

        # ============================================================
        # USER INTERFACE SETUP
        # ============================================================

        main_layout = QHBoxLayout()
        left_panel = QVBoxLayout()

        # ------------------------------------------------------------
        # CONTROL PANEL TITLE
        # ------------------------------------------------------------

        title = QLabel("CONTROL PANEL")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 18px; "
            "font-weight: bold; "
            "color: #2c3e50;"
        )

        left_panel.addWidget(title)

        # ------------------------------------------------------------
        # HARDWARE STATUS
        # ------------------------------------------------------------

        self.status_label = QLabel("Status: Searching for hardware...")
        self.status_label.setStyleSheet(
            "color: orange; "
            "font-weight: bold;"
        )

        left_panel.addWidget(self.status_label)

        # ============================================================
        # SETTINGS
        # ============================================================

        config_group = QGroupBox("Settings")
        config_layout = QFormLayout()

        # ------------------------------------------------------------
        # MEASUREMENT MODE SELECTION
        # ------------------------------------------------------------

        self.combo_mode = QComboBox()

        self.combo_mode.addItems([
            "Voltage (V)",
            "Current (A)",
            "Resistance (Ω)"
        ])

        self.combo_mode.currentIndexChanged.connect(
            self.update_graph_labels
        )

        config_layout.addRow(
            "Measurement Mode:",
            self.combo_mode
        )

        # ------------------------------------------------------------
        # MEASUREMENT DURATION
        # ------------------------------------------------------------

        self.input_duration = QSpinBox()

        self.input_duration.setRange(0, 3600)
        self.input_duration.setValue(0)

        self.input_duration.setSuffix(
            " s (0 = Manual)"
        )

        config_layout.addRow(
            "Duration:",
            self.input_duration
        )

        # ------------------------------------------------------------
        # PLOT TITLE
        # ------------------------------------------------------------

        self.input_graph_title = QLineEdit(
            "pH / PANI Monitoring"
        )

        self.input_graph_title.textChanged.connect(
            self.update_graph_labels
        )

        config_layout.addRow(
            "Plot Title:",
            self.input_graph_title
        )

        config_group.setLayout(config_layout)

        left_panel.addWidget(config_group)

        # ============================================================
        # RECORDED MEASUREMENTS
        # ============================================================

        left_panel.addWidget(
            QLabel("Recorded Measurements:")
        )

        self.list_widget = QListWidget()

        left_panel.addWidget(
            self.list_widget
        )

        # ------------------------------------------------------------
        # RENAME AND DELETE BUTTONS
        # ------------------------------------------------------------

        btn_row = QHBoxLayout()

        self.btn_rename = QPushButton("Rename")

        self.btn_rename.clicked.connect(
            self.rename_measurement
        )

        self.btn_delete = QPushButton("Delete")

        self.btn_delete.clicked.connect(
            self.delete_measurement
        )

        btn_row.addWidget(
            self.btn_rename
        )

        btn_row.addWidget(
            self.btn_delete
        )

        left_panel.addLayout(
            btn_row
        )

        # ============================================================
        # START / STOP BUTTON
        # ============================================================

        self.btn_start = QPushButton("START")

        self.btn_start.clicked.connect(
            self.toggle_measurement
        )

        self.btn_start.setStyleSheet(
            "background-color: #27ae60; "
            "color: white; "
            "font-weight: bold; "
            "height: 50px;"
        )

        left_panel.addWidget(
            self.btn_start
        )

        # ============================================================
        # SAVE CSV BUTTON
        # ============================================================

        self.btn_save = QPushButton(
            "SAVE SELECTED DATA (CSV)"
        )

        self.btn_save.clicked.connect(
            self.save_data
        )

        left_panel.addWidget(
            self.btn_save
        )

        # ============================================================
        # SAVE PLOT IMAGE BUTTON
        # ============================================================

        self.btn_save_graph = QPushButton(
            "SAVE PLOT IMAGE"
        )

        self.btn_save_graph.clicked.connect(
            self.save_graph_image
        )

        self.btn_save_graph.setStyleSheet(
            "background-color: #34495e; "
            "color: white; "
            "font-weight: bold;"
        )

        left_panel.addWidget(
            self.btn_save_graph
        )

        # ============================================================
        # PLOT AREA
        # ============================================================

        graph_container = QVBoxLayout()

        self.graph_widget = pg.PlotWidget()

        self.graph_widget.setBackground('w')

        self.graph_widget.addLegend()

        self.graph_widget.showGrid(
            x=True,
            y=True
        )

        self.curve = self.graph_widget.plot(
            pen=pg.mkPen(
                'b',
                width=2
            ),
            name="Current Measurement"
        )

        graph_container.addWidget(
            self.graph_widget
        )

        # ============================================================
        # MAIN WINDOW LAYOUT
        # ============================================================

        main_layout.addLayout(
            left_panel,
            1
        )

        main_layout.addLayout(
            graph_container,
            3
        )

        container = QWidget()

        container.setLayout(
            main_layout
        )

        self.setCentralWidget(
            container
        )

        self.update_graph_labels()

        # ============================================================
        # TIMER FOR AUTOMATIC HARDWARE SEARCH AND REAL-TIME READING
        # ============================================================

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_logic
        )

        self.timer.start(30)

    # ================================================================
    # UPDATE PLOT LABELS
    # ================================================================

    def update_graph_labels(self):

        mode = self.combo_mode.currentText()

        unit = (
            mode
            .split("(")[1]
            .replace(")", "")
        )

        label = (
            mode
            .split("(")[0]
            .strip()
        )

        self.graph_widget.setTitle(
            self.input_graph_title.text(),
            color="k",
            size="15pt"
        )

        self.graph_widget.setLabel(
            'left',
            label,
            units=unit
        )

        self.graph_widget.setLabel(
            'bottom',
            'Time',
            units='s'
        )

    # ================================================================
    # SEARCH FOR ESP32
    # ================================================================

    def find_esp32(self):

        ports = serial.tools.list_ports.comports()

        for port in ports:

            # Convert properties to lowercase to avoid
            # case-sensitive matching problems.
            desc = port.description.lower()
            hwid = port.hwid.lower()

            # Specifically search for CH341/CH340 devices
            # or the standard WCH Vendor ID (1A86).
            if (
                "ch34" in desc
                or "usb-serial" in desc
                or "1a86" in hwid
            ):

                try:

                    s = serial.Serial(
                        port.device,
                        115200,
                        timeout=0.5
                    )

                    self.serial_port = s

                    self.status_label.setText(
                        f"Status: Connected ({port.device})"
                    )

                    self.status_label.setStyleSheet(
                        "color: green; "
                        "font-weight: bold;"
                    )

                    return True

                except:
                    continue

        # If all ports are checked and no compatible
        # CH341/CH340 device is found.
        self.serial_port = None

        self.status_label.setText(
            "Status: ESP32 (CH341) not found"
        )

        self.status_label.setStyleSheet(
            "color: red; "
            "font-weight: bold;"
        )

        return False

    # ================================================================
    # START OR STOP MEASUREMENT
    # ================================================================

    def toggle_measurement(self):

        if not self.is_measuring:

            if (
                self.serial_port is None
                and not self.find_esp32()
            ):

                QMessageBox.critical(
                    self,
                    "Error",
                    "ESP32 (CH341) not found! "
                    "Check the USB cable."
                )

                return

            try:

                self.serial_port.reset_input_buffer()

            except:

                # If the serial connection was lost,
                # attempt to reconnect automatically.
                if not self.find_esp32():

                    QMessageBox.critical(
                        self,
                        "Error",
                        "Connection to the ESP32 was lost!"
                    )

                    return

            self.current_x = []
            self.current_y = []

            self.start_time = time.time()

            self.is_measuring = True

            self.btn_start.setText(
                "STOP"
            )

            self.btn_start.setStyleSheet(
                "background-color: #c0392b; "
                "color: white; "
                "font-weight: bold; "
                "height: 50px;"
            )

        else:

            self.stop_measurement()

    # ================================================================
    # STOP MEASUREMENT
    # ================================================================

    def stop_measurement(self):

        self.is_measuring = False

        self.btn_start.setText(
            "START"
        )

        self.btn_start.setStyleSheet(
            "background-color: #27ae60; "
            "color: white; "
            "font-weight: bold; "
            "height: 50px;"
        )

        mode_prefix = (
            self.combo_mode
            .currentText()
            .split("(")[0]
            .strip()
        )

        name = (
            f"{mode_prefix} {self.count}"
        )

        self.measurements[name] = {

            'x': self.current_x[:],

            'y': self.current_y[:],

            'type': self.combo_mode.currentText()
        }

        self.list_widget.addItem(
            name
        )

        self.count += 1

        self.update_all_curves()

    # ================================================================
    # REAL-TIME ACQUISITION LOGIC
    # ================================================================

    def update_logic(self):

        if self.serial_port is None:

            self.find_esp32()

            return

        if self.is_measuring:

            elapsed = (
                time.time()
                - self.start_time
            )

            limit = (
                self.input_duration.value()
            )

            # Automatically stop the measurement
            # when the selected duration is reached.
            if (
                limit > 0
                and elapsed >= limit
            ):

                self.stop_measurement()

                return

            new_data = False

            try:

                while (
                    self.serial_port.in_waiting > 0
                ):

                    try:

                        line = (
                            self.serial_port
                            .readline()
                            .decode()
                            .strip()
                        )

                        if (
                            line
                            and "," in line
                        ):

                            parts = (
                                line.split(",")
                            )

                            if len(parts) >= 3:

                                idx = (
                                    self.combo_mode
                                    .currentIndex()
                                )

                                val = float(
                                    parts[idx]
                                )

                                self.current_x.append(
                                    time.time()
                                    - self.start_time
                                )

                                self.current_y.append(
                                    val
                                )

                                new_data = True

                    except:
                        break

            except (
                serial.SerialException,
                OSError
            ):

                # Handle unexpected hardware disconnection
                # during a measurement.
                self.serial_port = None

                self.stop_measurement()

                self.status_label.setText(
                    "Status: Hardware Disconnected!"
                )

                self.status_label.setStyleSheet(
                    "color: red; "
                    "font-weight: bold;"
                )

                return

            if new_data:

                self.curve.setData(
                    self.current_x,
                    self.current_y
                )

    # ================================================================
    # UPDATE ALL PLOT CURVES
    # ================================================================

    def update_all_curves(self):

        self.graph_widget.clear()

        self.graph_widget.addLegend()

        self.curve = self.graph_widget.plot(
            pen=pg.mkPen(
                'b',
                width=2
            ),
            name="Current Measurement"
        )

        colors = [
            'r',
            'g',
            'm',
            'c',
            'k'
        ]

        for i, (name, data) in enumerate(
            self.measurements.items()
        ):

            color = (
                colors[
                    i % len(colors)
                ]
            )

            self.graph_widget.plot(
                data['x'],
                data['y'],
                pen=pg.mkPen(
                    color,
                    width=1.5
                ),
                name=name
            )

    # ================================================================
    # RENAME MEASUREMENT
    # ================================================================

    def rename_measurement(self):

        current_item = (
            self.list_widget.currentItem()
        )

        if not current_item:
            return

        old_name = (
            current_item.text()
        )

        new_name, ok = (
            QInputDialog.getText(
                self,
                "Rename Measurement",
                "New name:",
                text=old_name
            )
        )

        if (
            ok
            and new_name
        ):

            self.measurements[new_name] = (
                self.measurements.pop(
                    old_name
                )
            )

            current_item.setText(
                new_name
            )

            self.update_all_curves()

    # ================================================================
    # DELETE MEASUREMENT
    # ================================================================

    def delete_measurement(self):

        current_item = (
            self.list_widget.currentItem()
        )

        if not current_item:
            return

        name = (
            current_item.text()
        )

        del self.measurements[name]

        self.list_widget.takeItem(
            self.list_widget.row(
                current_item
            )
        )

        self.update_all_curves()

    # ================================================================
    # SAVE SELECTED MEASUREMENT AS CSV
    # ================================================================

    def save_data(self):

        current_item = (
            self.list_widget.currentItem()
        )

        if not current_item:

            QMessageBox.warning(
                self,
                "Warning",
                "Select a measurement from the list!"
            )

            return

        name = (
            current_item.text()
        )

        data = (
            self.measurements[name]
        )

        mode_text = data.get(
            'type',
            self.combo_mode.currentText()
        )

        # Define the CSV column name according
        # to the selected measurement mode.
        if "Voltage" in mode_text:

            value_label = "Voltage_V"

        elif "Current" in mode_text:

            value_label = "Current_A"

        else:

            value_label = "Resistance_Ohm"

        path, _ = (
            QFileDialog.getSaveFileName(
                self,
                "Save CSV",
                f"{name}.csv",
                "CSV Files (*.csv)"
            )
        )

        if path:

            pd.DataFrame({

                'Time_s': data['x'],

                value_label: data['y']

            }).to_csv(
                path,
                index=False
            )

            QMessageBox.information(
                self,
                "Success",
                "Data exported successfully!"
            )

    # ================================================================
    # SAVE PLOT AS IMAGE
    # ================================================================

    def save_graph_image(self):

        path, _ = (
            QFileDialog.getSaveFileName(
                self,
                "Save Plot",
                "pani_experiment.png",
                "PNG Image (*.png);;"
                "JPEG Image (*.jpg);;"
                "Scalable Vector Graphics (*.svg)"
            )
        )

        if path:

            try:

                exporter = (
                    exporters.ImageExporter(
                        self.graph_widget.plotItem
                    )
                )

                exporter.export(
                    path
                )

                QMessageBox.information(
                    self,
                    "Success",
                    "Plot image saved successfully!"
                )

            except Exception as e:

                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to save plot image: {e}"
                )


# ====================================================================
# APPLICATION ENTRY POINT
# ====================================================================

if __name__ == "__main__":

    app = QApplication(
        sys.argv
    )

    window = MainWindow()

    window.show()

    sys.exit(
        app.exec()
    )