# Open-Source Multifunctional Measurement Platform

## Overview

This repository contains the hardware documentation, ESP32 firmware, desktop software, and validation data associated with the open-source multifunctional measurement platform described in the manuscript:

**"An Open-Source Multifunctional Measurement Platform for High-Impedance Potentiometric Sensors and Electrical Characterization"**

The platform was developed as a low-cost and reproducible system for potentiometric measurements and basic electrical characterization.

The instrument integrates:

- ESP32 microcontroller
- ADS1115 16-bit analog-to-digital converter (ADC)
- CA3140 operational amplifier configured as a high-input-impedance voltage follower
- Resistance measurement circuit
- Current measurement circuit
- Python-based graphical user interface (GUI)

Three measurement modes are available:

1. Potentiometric voltage measurement
2. Electrical resistance measurement
3. Electrical current measurement

The system is intended for sensor development, prototyping, educational applications, and exploratory laboratory measurements.

---

## Main Features

- Open-source firmware and desktop software
- Low-cost commercially available components
- High-input-impedance potentiometric input
- 16-bit ADS1115 ADC
- Three independent measurement modes
- Real-time graphical visualization
- Serial communication through USB
- CSV data export
- Python source code for modification and further development
- Standalone desktop application
- Modular hardware architecture

---

## System Architecture

The ESP32 acts as the central control and communication unit of the platform.

The ADS1115 provides analog-to-digital conversion for the three measurement channels.

The channel assignments used in the current hardware and firmware implementation are:

| ADS1115 Channel | Measurement |
|---|---|
| A0 | Potentiometric voltage |
| A1 | Resistance |
| A2 | Current |
| A3 | Not used |

The ADS1115 communicates with the ESP32 through the I2C interface:

| Signal | ESP32 GPIO |
|---|---|
| SDA | GPIO 21 |
| SCL | GPIO 22 |

The ADS1115 and CA3140 are powered from the 3.3 V rail of the ESP32 development board.

All measurement circuits share the ESP32 ground as a common electrical reference.

---

## Potentiometric Measurement

The potentiometric channel was designed for measurements involving high-impedance sensing interfaces.

The sensing signal is connected to the non-inverting input of a CA3140 operational amplifier configured as a voltage follower.

The buffer reduces electrical loading of the sensing interface before the signal is acquired by the ADS1115.

The buffered output is connected to:

```text
ADS1115 A0
```

The reference electrode or electrical reference of the experiment is connected to the common system ground.

### Signal Path

```text
Sensing electrode
      |
      v
CA3140 voltage follower
      |
      v
ADS1115 A0
      |
      v
ESP32
      |
      v
USB / Serial
      |
      v
Desktop GUI
```

---

## Resistance Measurement

Resistance is measured using a voltage-divider configuration.

The present implementation uses:

```text
R_REF = 10 kΩ
V_IN  = 3.3 V
```

The electrical configuration is:

```text
3.3 V
  |
  |
R_REF
10 kΩ
  |
  +------------> ADS1115 A1
  |
 R_x
  |
 GND
```

where `R_x` is the unknown resistance.

The resistance is calculated using:

```text
R_x = R_REF × V_out / (V_IN - V_out)
```

The experimentally tested implementation used a 10 kΩ reference resistor and was functionally evaluated using commercial resistors ranging from 220 Ω to 10 kΩ.

The reference resistor can be changed to adapt the circuit to other resistance regions. If `R_REF` is physically changed, the corresponding value in the firmware must also be updated.

---

## Current Measurement

Current is determined from the voltage developed across a known shunt resistor.

The present implementation uses:

```text
R_SHUNT = 10 kΩ
```

The shunt voltage is acquired through:

```text
ADS1115 A2
```

Current is calculated using Ohm's law:

```text
I = V_shunt / R_SHUNT
```

The current channel was experimentally evaluated over an approximate range of:

```text
24 µA to 230 µA
```

The 10 kΩ shunt resistor introduces a voltage drop proportional to the measured current. The expected current and resulting shunt voltage should therefore be evaluated before connecting an unknown device.

---

## Hardware Requirements

The main components used in the prototype include:

| Quantity | Component |
|---:|---|
| 1 | ESP32 development board |
| 1 | ADS1115 ADC module |
| 1 | CA3140A operational amplifier |
| 2 | 10 kΩ fixed resistors |
| 2 | Solderless breadboards |
| 1 set | Jumper wires |
| 1 | USB cable |
| 1 | Plastic support/base |
| 1 | Aluminum structure/base for shielding |

The prototype does not require a custom printed circuit board (PCB).

The original implementation had an estimated component cost of approximately **BRL 148 (USD 28.79)** based on component prices used during development.

---

## Firmware

The ESP32 firmware is located in:

```text
src/main.cpp
```

The firmware was developed using the PlatformIO environment.

The PlatformIO configuration file is:

```text
platformio.ini
```

### Firmware Configuration

The default hardware parameters are:

```cpp
const float R_SHUNT = 10000.0;
const float R_REF   = 10000.0;
const float V_IN    = 3.3;
```

The ADS1115 channel assignments are:

```text
A0 -> Potentiometric voltage
A1 -> Resistance
A2 -> Current
```

The I2C connections are:

```text
SDA -> GPIO 21
SCL -> GPIO 22
```

### Uploading the Firmware

1. Install Visual Studio Code.
2. Install the PlatformIO extension.
3. Clone or download this repository.
4. Open the project folder in PlatformIO.
5. Connect the ESP32 to the computer through USB.
6. Select the appropriate ESP32 board and serial port.
7. Compile the project.
8. Upload the firmware to the ESP32.

After uploading, the ESP32 will acquire the three measurement channels and transmit the resulting values through the serial interface.

The serial output format is:

```text
POTENTIOMETRIC_VOLTAGE,CURRENT,RESISTANCE
```

---

## Desktop Software

The graphical user interface was developed in Python.

The main source file is:

```text
interface.py
```

The application provides:

- Serial-port selection
- Measurement-mode selection
- Acquisition control
- Real-time numerical display
- Real-time plotting
- Measurement timing
- CSV data export
- Graph export

---

## Python Installation

Python 3 is required to execute the application from source.

Install the required dependencies using:

```bash
pip install -r requirements.txt
```

The main Python dependencies are:

- PyQt6
- pyqtgraph
- pandas
- pyserial

After installing the dependencies, run:

```bash
python interface.py
```

---

## Standalone Application

A packaged standalone version of the desktop application is provided in:

```text
standalone/
```

The executable can be used by users who do not wish to execute or modify the Python source code.

Before starting a measurement:

1. Connect the ESP32 to the computer.
2. Start the desktop application.
3. Select the appropriate serial port.
4. Select the desired measurement mode.
5. Connect the device or sensor to the corresponding measurement input.
6. Start the acquisition.

---

## Data Acquisition

During acquisition, the ESP32 reads the ADS1115 channels and transmits the processed measurements to the desktop application through USB serial communication.

The GUI displays the selected quantity in real time and allows the acquired data to be exported for subsequent analysis.

The experimentally determined effective acquisition rate of the complete system under the tested operating conditions was approximately:

```text
10.15 samples/s
```

This value represents the effective acquisition rate of the complete measurement chain and should not be interpreted as the maximum conversion rate of the ADS1115.

---

## Data Export

Measurements can be exported in comma-separated values (CSV) format.

The exported data can subsequently be analyzed using software such as:

- Python
- MATLAB
- Origin
- R
- Spreadsheet software

---

## Experimental Validation

The platform was experimentally evaluated at different levels.

### Voltage Measurement

The potentiometric channel was evaluated using known DC voltage conditions independently measured using a benchtop digital multimeter.

The investigated reference voltages were:

```text
0.24 V
0.81 V
1.23 V
1.78 V
2.28 V
```

The experiments were used to evaluate the complete potentiometric acquisition chain, including the CA3140 buffer, ADS1115, ESP32, serial communication, and desktop software.

### Resistance Measurement

Commercial resistors with nominal values of:

```text
220 Ω
1 kΩ
4.7 kΩ
10 kΩ
```

were evaluated using the resistance measurement channel.

The experiment demonstrated the functional operation of the voltage-divider measurement architecture.

### Current Measurement

The current measurement channel was experimentally evaluated using a 10 kΩ shunt resistor.

The comparison current conditions were approximately:

```text
24 µA
77 µA
126 µA
178 µA
230 µA
```

### Potentiometric Sensor Application

Application-level validation was performed using polyaniline (PANI)-based potentiometric sensing interfaces.

Measurements were performed at:

```text
pH 2.4
pH 3.3
pH 4.0
pH 5.4
pH 6.2
pH 7.3
pH 8.2
```

The measured response showed a systematic decrease in potential with increasing pH.

Linear regression of the mean potentiometric response produced approximately:

```text
Sensitivity = -44.37 mV/pH
R² = 0.992
```

This experiment demonstrated the ability of the platform to acquire chemically meaningful signals from a high-impedance potentiometric sensing interface.

---

## Validation Data

Experimental datasets associated with the characterization of the platform are provided in this repository.

The recommended organization is:

```text
validation_data/
|
├── voltage/
├── battery_stability/
├── current/
├── resistance/
└── PANI_pH/
```

The voltage, current, battery-stability, and PANI directories contain the available experimental acquisition files used for analysis.

### Resistance Data

The original raw acquisition files from the early development-stage resistance experiment were not retained.

The available graphical output is provided for transparency and corresponds to the functional resistance validation reported in the manuscript.

The resistance results should therefore be interpreted as functional validation rather than as a complete quantitative accuracy characterization.

---

## Initial System Verification

Before connecting an electrochemical sensor or unknown electrical device, the following checks are recommended:

1. Connect the ESP32 through USB.
2. Verify the 3.3 V supply.
3. Verify the common ground connection.
4. Confirm I2C communication between the ESP32 and ADS1115.
5. Confirm serial communication with the desktop application.
6. Apply a known voltage to the potentiometric input and verify A0.
7. Connect a known resistor and verify the resistance measurement through A1.
8. Apply a known low-current condition and verify the current measurement through A2.
9. Perform a short acquisition and verify real-time visualization and CSV export.

---

## Important Operating Considerations

The potentiometric channel has a high input impedance and is consequently more susceptible to environmental electrical interference than the resistance and current channels.

For potentiometric measurements:

- Keep high-impedance wiring as short as practical.
- Avoid unnecessary parallel ground paths.
- Keep the sensing connections mechanically stable.
- Keep sensitive analog wiring away from digital communication wiring whenever possible.
- Verify the common electrical reference before starting an experiment.
- Electrical shielding may improve measurements in environments with significant electromagnetic interference.

---

## Known Limitations

The platform was developed as a low-cost, modular, and reproducible measurement system.

It is **not intended to replace traceable laboratory-grade metrology equipment or advanced commercial electrochemical workstations**.

The reported resistance and current ranges correspond to the experimentally tested hardware configuration.

The resistance measurement behavior depends on the selected reference resistor (`R_REF`), while the current measurement range depends on the selected shunt resistor (`R_SHUNT`).

Changing these components requires corresponding changes to the firmware configuration and should be independently validated.

The resistance experiment reported in the manuscript represents functional validation because the original raw development-stage acquisition data were not retained.

---

## Repository Structure

The repository is organized around the firmware, desktop software, hardware documentation, and experimental validation data.

A recommended structure is:

```text
Sensor/
|
├── README.md
├── LICENSE
├── CITATION.cff
├── requirements.txt
├── platformio.ini
|
├── src/
|   └── main.cpp
|
├── software/
|   └── interface.py
|
├── standalone/
|   └── interface.exe
|
├── hardware/
|   ├── schematics/
|   └── bill_of_materials.csv
|
├── validation_data/
|   ├── voltage/
|   ├── battery_stability/
|   ├── current/
|   ├── resistance/
|   └── PANI_pH/
|
└── docs/
```

The exact directory structure may evolve as additional documentation and experimental data are added.

---

## Reproducibility

The objective of this repository is to provide the information required to inspect, reproduce, modify, and further develop the proposed measurement platform.

The source code is provided in editable form so that users can modify:

- Measurement routines
- Hardware parameters
- ADC configuration
- Graphical interface
- Data-processing routines
- Measurement ranges

Any hardware modification should be accompanied by the corresponding firmware modification and independent experimental verification.

---

## Citation

If you use this platform in scientific work, please cite the associated manuscript:

**Tiago A. A. Querino and Hugo J. N. P. D. Mello, "An Open-Source Multifunctional Measurement Platform for High-Impedance Potentiometric Sensors and Electrical Characterization."**

Publication information and DOI will be added after publication.

---

## License

License information for the source code, hardware documentation, and associated materials is provided in the `LICENSE` file.

---

## Authors

**Tiago A. A. Querino**  
**Hugo J. N. P. D. Mello**

---

## Project Status

This repository accompanies the scientific manuscript describing the design, construction, operation, and experimental validation of the measurement platform.

Additional documentation, validation files, and improvements may be incorporated as the platform continues to be developed.