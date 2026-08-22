#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_ADS1X15.h>

// Instancia o objeto do módulo ADC ADS1115
Adafruit_ADS1115 ads;

// ==========================================
//   CONFIGURAÇÕES DE CALIBRAÇÃO DO HARDWARE
// ==========================================
// Altere estes valores se os seus resistores físicos forem diferentes:
const float R_SHUNT = 10000.0;    // Resistor de Shunt em Ohms (Linha X ao GND)
const float R_REF = 10000.0;    // Resistor de Referência em Ohms (10k entre 3.3V e Linha Z)
const float V_IN = 3.3;         // Tensão exata de saída do pino 3.3V do seu ESP32

void setup() {
  // Inicializa a comunicação Serial na velocidade estável de 115200 bps
  Serial.begin(115200);

  // Inicializa o protocolo I2C para o ADS1115 nos pinos padrões (SDA=21, SCL=22)
  if (!ads.begin()) {
    Serial.println("ERRO: ADS1115 nao foi encontrado! Verifique a fiação I2C.");
    while (1) {
      delay(1000); // Trava o código aqui caso haja mau contato nos fios do ADS
    }
  }

  // Define o ganho do ADS1115
  // GAIN_ONE define a escala em +/- 4.096V (Cada bit equivale a 0.125mV)
  // Isso é ideal para ler com total segurança os 3.3V do ESP32 sem queimar ou saturar
  ads.setGain(GAIN_ONE);
}

void loop() {
  // -------------------------------------------------------------
  // CANAL A0: Medição de Potencial / pH (Vindo do Amp-Op CA3140)
  // -------------------------------------------------------------
  int16_t adc0 = ads.readADC_SingleEnded(0);
  float voltagem_potencial = ads.computeVolts(adc0);

  // -------------------------------------------------------------
  // CANAL A1: Medição de Corrente (Queda de tensão na Linha X)
  // -------------------------------------------------------------
  int16_t adc1 = ads.readADC_SingleEnded(1);
  float v_shunt = ads.computeVolts(adc1);
  float corrente = v_shunt / R_SHUNT; // Lei de Ohm: I = V / R

// -------------------------------------------------------------
  // CANAL A2: Medição de Resistência (Divisor de tensão na Linha Z)
  // -------------------------------------------------------------
 int16_t adc3 = ads.readADC_SingleEnded(3);
  float v_out_res = ads.computeVolts(adc3);
  float resistencia = 0.0;

  // 2. Aplica a matemática pura do divisor de tensão (Sem filtros!)
  // Impede apenas a divisão por zero se a tensão colar exatamente em V_IN (3.3V)
  if (v_out_res < (V_IN - 0.001)) {
      resistencia = R_REF * (v_out_res / (V_IN - v_out_res));
  } else {
      resistencia = 888888.0; // Valor simbólico só para indicar que colou no teto (3.3V)
  }

  // -------------------------------------------------------------
  // ENVIO DOS DADOS VIA SERIAL
  // -------------------------------------------------------------
  // Envia os três parâmetros na mesma linha separados por vírgula.
  // O Python vai receber exatamente essa estrutura para separar na interface.
  // Formato enviado: POTENCIAL,CORRENTE,RESISTENCIA
  Serial.print(voltagem_potencial, 4); // 4 casas decimais
  Serial.print(",");
  Serial.print(corrente, 6);           // 6 casas decimais para pegar correntes baixas em Ampères
  Serial.print(",");
  Serial.println(resistencia, 2);      // 2 casas decimais para a resistência em Ohms

  // Aguarda 50 milissegundos para a próxima leitura. 
  // Essa taxa garante dados fluidos no Python sem sobrecarregar a porta.
  delay(50); 
}