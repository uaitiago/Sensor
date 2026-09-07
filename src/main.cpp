#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_ADS1X15.h>

// Create an instance of the ADS1115 ADC
Adafruit_ADS1115 ads;

// ==========================================
// HARDWARE CONFIGURATION
// ==========================================

// Modify these values if different physical resistors
// or excitation voltages are used.
const float R_SHUNT = 10000.0;  // Shunt resistor in ohms
const float R_REF   = 10000.0;  // Reference resistor in ohms
const float V_IN    = 3.3;      // Resistance-divider excitation voltage (V)

void setup() {

    // Initialize serial communication
    Serial.begin(115200);

    // Initialize I2C communication using the ESP32 default pins:
    // SDA = GPIO 21
    // SCL = GPIO 22
    Wire.begin(21, 22);

    // Initialize the ADS1115
    if (!ads.begin()) {
        Serial.println(
            "ERROR: ADS1115 not found. Check the I2C wiring."
        );

        // Stop execution if communication with the ADC fails
        while (1) {
            delay(1000);
        }
    }

    // Configure the ADS1115 programmable gain amplifier.
    //
    // GAIN_ONE corresponds to a full-scale range of +/-4.096 V.
    // For the ADS1115, this corresponds to approximately
    // 0.125 mV per ADC count.
    //
    // This range is suitable for the 0-3.3 V signals used
    // in the present hardware configuration.
    ads.setGain(GAIN_ONE);
}

void loop() {

    // ==========================================================
    // ADS1115 A0 - POTENTIOMETRIC VOLTAGE
    // ==========================================================
    //
    // The potentiometric signal is first buffered by the
    // CA3140 high-input-impedance voltage follower and then
    // acquired through ADS1115 channel A0.

    int16_t adc0 = ads.readADC_SingleEnded(0);
    float potentiometric_voltage = ads.computeVolts(adc0);


    // ==========================================================
    // ADS1115 A1 - RESISTANCE MEASUREMENT
    // ==========================================================
    //
    // The resistance measurement is based on a voltage divider:
    //
    // 3.3 V ---- R_REF ---- measurement node ---- R_x ---- GND
    //
    // The measurement node is connected to ADS1115 channel A1.
    //
    // The unknown resistance is calculated as:
    //
    // R_x = R_REF * V_out / (V_IN - V_out)

    int16_t adc1 = ads.readADC_SingleEnded(1);
    float resistance_voltage = ads.computeVolts(adc1);

    float resistance = 0.0;

    // Prevent division by zero when the measured voltage
    // approaches the excitation voltage.
    if (resistance_voltage < (V_IN - 0.001)) {

        resistance =
            R_REF *
            (resistance_voltage /
            (V_IN - resistance_voltage));

    } else {

        // Symbolic value indicating that the divider output
        // is too close to the upper voltage limit.
        resistance = 888888.0;
    }


    // ==========================================================
    // ADS1115 A2 - CURRENT MEASUREMENT
    // ==========================================================
    //
    // The voltage developed across the shunt resistor is
    // measured through ADS1115 channel A2.
    //
    // Current is calculated using Ohm's law:
    //
    // I = V_shunt / R_SHUNT

    int16_t adc2 = ads.readADC_SingleEnded(2);
    float shunt_voltage = ads.computeVolts(adc2);

    float current = shunt_voltage / R_SHUNT;


    // ==========================================================
    // SERIAL DATA TRANSMISSION
    // ==========================================================
    //
    // The three measured quantities are transmitted on the
    // same line and separated by commas.
    //
    // Output format:
    //
    // POTENTIOMETRIC_VOLTAGE,CURRENT,RESISTANCE
    //
    // The Python desktop application separates these values
    // and displays the selected measurement mode.

    Serial.print(potentiometric_voltage, 4);
    Serial.print(",");

    Serial.print(current, 6);
    Serial.print(",");

    Serial.println(resistance, 2);


    // Wait before starting the next acquisition cycle.
    //
    // The effective acquisition rate of the complete system
    // also depends on ADC conversion, ESP32 processing,
    // serial communication, and desktop-software processing.
    delay(50);
}