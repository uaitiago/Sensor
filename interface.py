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
        self.setWindowTitle("Hugo jose's lab - NEOS Multifunção")
        self.resize(1250, 750)

        # Dados e Controle
        self.serial_port = None
        self.is_measuring = False
        self.measurements = {}
        self.current_x = []
        self.current_y = []
        self.start_time = 0
        self.count = 1

        # --- UI SETUP ---
        main_layout = QHBoxLayout()
        left_panel = QVBoxLayout()

        title = QLabel("CONTROLE")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        left_panel.addWidget(title)

        self.status_label = QLabel("Status: Procurando Hardware...")
        self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        left_panel.addWidget(self.status_label)

        config_group = QGroupBox("Configurações")
        config_layout = QFormLayout()

        # MENU DE SELEÇÃO DE MEDIÇÃO
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Voltagem (V)", "Corrente (A)", "Resistência (Ω)"])
        self.combo_mode.currentIndexChanged.connect(self.update_graph_labels)
        config_layout.addRow("Modo de Medição:", self.combo_mode)

        self.input_duration = QSpinBox()
        self.input_duration.setRange(0, 3600)
        self.input_duration.setValue(0)
        self.input_duration.setSuffix(" seg (0=Manual)")
        config_layout.addRow("Duração:", self.input_duration)

        self.input_graph_title = QLineEdit("Monitoramento pH / PANI")
        self.input_graph_title.textChanged.connect(self.update_graph_labels)
        config_layout.addRow("Título Gráfico:", self.input_graph_title)

        config_group.setLayout(config_layout)
        left_panel.addWidget(config_group)

        left_panel.addWidget(QLabel("Medições Realizadas:"))
        self.list_widget = QListWidget()
        left_panel.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.btn_rename = QPushButton("Renomear")
        self.btn_rename.clicked.connect(self.rename_measurement)
        self.btn_delete = QPushButton("Excluir")
        self.btn_delete.clicked.connect(self.delete_measurement)
        btn_row.addWidget(self.btn_rename)
        btn_row.addWidget(self.btn_delete)
        left_panel.addLayout(btn_row)

        self.btn_start = QPushButton("INICIAR")
        self.btn_start.clicked.connect(self.toggle_measurement)
        self.btn_start.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; height: 50px;")
        left_panel.addWidget(self.btn_start)

        self.btn_save = QPushButton("SALVAR CSV (Selecionada)")
        self.btn_save.clicked.connect(self.save_data)
        left_panel.addWidget(self.btn_save)

        self.btn_save_graph = QPushButton("SALVAR IMAGEM (Gráfico)")
        self.btn_save_graph.clicked.connect(self.save_graph_image)
        self.btn_save_graph.setStyleSheet("background-color: #34495e; color: white; font-weight: bold;")
        left_panel.addWidget(self.btn_save_graph)

        # --- GRÁFICO ---
        graph_container = QVBoxLayout()
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('w')
        self.graph_widget.addLegend()
        self.graph_widget.showGrid(x=True, y=True)
        self.curve = self.graph_widget.plot(pen=pg.mkPen('b', width=2), name="Medida Atual")
        graph_container.addWidget(self.graph_widget)

        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(graph_container, 3)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.update_graph_labels()

        # Timer para busca automática e leitura em tempo real
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_logic)
        self.timer.start(30)

    def update_graph_labels(self):
        mode = self.combo_mode.currentText()
        unit = mode.split("(")[1].replace(")", "")
        label = mode.split("(")[0].strip()

        self.graph_widget.setTitle(self.input_graph_title.text(), color="k", size="15pt")
        self.graph_widget.setLabel('left', label, units=unit)
        self.graph_widget.setLabel('bottom', 'Tempo', units='s')

    def find_esp32(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            # Converte as propriedades para minúsculas para evitar problemas de correspondência
            desc = port.description.lower()
            hwid = port.hwid.lower()
            
            # Filtra especificamente pelo chip CH341/CH340 ou pelo Vendor ID padrão da WCH (1a86)
            if "ch34" in desc or "usb-serial" in desc or "1a86" in hwid:
                try:
                    s = serial.Serial(port.device, 115200, timeout=0.5)
                    self.serial_port = s
                    self.status_label.setText(f"Status: Conectado ({port.device})")
                    self.status_label.setStyleSheet("color: green; font-weight: bold;")
                    return True
                except:
                    continue
                    
        # Se percorrer todas as portas e não encontrar o CH341
        self.serial_port = None
        self.status_label.setText("Status: ESP32 (CH341) não encontrado")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        return False

    def toggle_measurement(self):
        if not self.is_measuring:
            if self.serial_port is None and not self.find_esp32():
                QMessageBox.critical(self, "Erro", "ESP32 (CH341) não encontrado! Verifique o cabo USB.")
                return

            try:
                self.serial_port.reset_input_buffer()
            except:
                # Caso a porta tenha caído no intervalo, tenta reatar
                if not self.find_esp32():
                    QMessageBox.critical(self, "Erro", "Conexão com o ESP32 perdida!")
                    return

            self.current_x, self.current_y = [], []
            self.start_time = time.time()
            self.is_measuring = True
            self.btn_start.setText("PARAR")
            self.btn_start.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold; height: 50px;")
        else:
            self.stop_measurement()

    def stop_measurement(self):
        self.is_measuring = False
        self.btn_start.setText("INICIAR")
        self.btn_start.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; height: 50px;")

        mode_prefix = self.combo_mode.currentText().split("(")[0].strip()
        name = f"{mode_prefix} {self.count}"

        self.measurements[name] = {
            'x': self.current_x[:],
            'y': self.current_y[:],
            'type': self.combo_mode.currentText()
        }
        self.list_widget.addItem(name)
        self.count += 1
        self.update_all_curves()

    def update_logic(self):
        if self.serial_port is None:
            self.find_esp32()
            return

        if self.is_measuring:
            elapsed = time.time() - self.start_time
            limit = self.input_duration.value()

            if limit > 0 and elapsed >= limit:
                self.stop_measurement()
                return

            new_data = False
            try:
                while self.serial_port.in_waiting > 0:
                    try:
                        line = self.serial_port.readline().decode().strip()
                        if line and "," in line:
                            parts = line.split(",")
                            if len(parts) >= 3:
                                idx = self.combo_mode.currentIndex()
                                val = float(parts[idx])

                                self.current_x.append(time.time() - self.start_time)
                                self.current_y.append(val)
                                new_data = True
                    except:
                        break
            except (serial.SerialException, OSError):
                # Trata desconexões repentinas do cabo durante a medição
                self.serial_port = None
                self.stop_measurement()
                self.status_label.setText("Status: Hardware Desconectado!")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
                return

            if new_data:
                self.curve.setData(self.current_x, self.current_y)

    def update_all_curves(self):
        self.graph_widget.clear()
        self.graph_widget.addLegend()
        self.curve = self.graph_widget.plot(pen=pg.mkPen('b', width=2), name="Medida Atual")

        colors = ['r', 'g', 'm', 'c', 'k']
        for i, (name, data) in enumerate(self.measurements.items()):
            color = colors[i % len(colors)]
            self.graph_widget.plot(data['x'], data['y'], pen=pg.mkPen(color, width=1.5), name=name)

    def rename_measurement(self):
        current_item = self.list_widget.currentItem()
        if not current_item: return
        old_name = current_item.text()
        new_name, ok = QInputDialog.getText(self, "Renomear", "Novo nome:", text=old_name)
        if ok and new_name:
            self.measurements[new_name] = self.measurements.pop(old_name)
            current_item.setText(new_name)
            self.update_all_curves()

    def delete_measurement(self):
        current_item = self.list_widget.currentItem()
        if not current_item: return
        name = current_item.text()
        del self.measurements[name]
        self.list_widget.takeItem(self.list_widget.row(current_item))
        self.update_all_curves()

    def save_data(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Aviso", "Selecione uma medida na lista!")
            return
        name = current_item.text()
        data = self.measurements[name]

        mode_text = data.get('type', self.combo_mode.currentText())
        if "Voltagem" in mode_text:
            value_label = "Voltagem_V"
        elif "Corrente" in mode_text:
            value_label = "Corrente_A"
        else:
            value_label = "Resistencia_Ohm"

        path, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", f"{name}.csv", "CSV Files (*.csv)")
        if path:
            pd.DataFrame({'Tempo_s': data['x'], value_label: data['y']}).to_csv(path, index=False)
            QMessageBox.information(self, "Sucesso", "Dados exportados com sucesso!")

    def save_graph_image(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Gráfico", "experimento_pani.png",
            "PNG Image (*.png);;JPEG Image (*.jpg);;Scalable Vector Graphics (*.svg)"
        )
        if path:
            try:
                exporter = exporters.ImageExporter(self.graph_widget.plotItem)
                exporter.export(path)
                QMessageBox.information(self, "Sucesso", "Imagem do gráfico salva!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao salvar imagem: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())