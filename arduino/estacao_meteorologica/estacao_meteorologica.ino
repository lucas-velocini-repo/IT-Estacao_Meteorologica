#include <Wire.h>

//WIFI ================================================================================================
#include <WiFi.h>
#include <ESPmDNS.h>
#include <NetworkClient.h>

const char* ssid = "WiFi Notebook"; //Define o nome do ponto de acesso
const char* pass = "senha123"; //Define a senha

WiFiServer sv(80); //Cria um servidor na porta 80

//SENSOR DE PARTICULADOS SPS30 ========================================================================
#include <sps30.h>

//SENSOR BH1750 =======================================================================================
#include <BH1750.h>

//SENSOR AHT20 + BMP280 ===============================================================================
#include <Adafruit_AHTX0.h> // Library for AHT20
#include <Adafruit_BMP280.h> // Library for BMP280

//SENSOR DE PARTICULADOS SPS30 ========================================================================
int16_t ret;
uint8_t auto_clean_days = 4;
uint32_t auto_clean;
struct sps30_measurement m;
char serial[SPS30_MAX_SERIAL_LEN];
uint16_t data_ready;

//SENSOR BH1750 =======================================================================================
BH1750 lightMeter;

//SENSOR AHT20 + BMP280 ===============================================================================
Adafruit_AHTX0 aht;
Adafruit_BMP280 bmp;

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);

  //WIFI ================================================================================================
  //WiFi.softAP(ssid, pass); //Inicia o ponto de acesso
  //IPAddress ip = WiFi.softAPIP(); //Endereço de IP
  //sv.begin(); //Inicia o servidor

  //if (!MDNS.begin("estacao")) {
  //  Serial.println("Error setting up MDNS responder!");  //Configura o DNS
  //  while (1) {
  //    delay(1000);
  //  }
  //}

  //MDNS.addService("http", "tcp", 80); //Adiciona o servico ao DNS

  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Conectando...");
  }
  Serial.println("Conectado à rede Wi-Fi");

  IPAddress ip = WiFi.softAPIP(); //Endereço de IP
  sv.begin(); //Inicia o servidor

  if (!MDNS.begin("estacao")) {
    Serial.println("Error setting up MDNS responder!");  //Configura o DNS
    while (1) {
      delay(1000);
    }
  }

  MDNS.addService("http", "tcp", 80); //Adiciona o servico ao DNS

  //SENSOR DE PARTICULADOS SPS30 ========================================================================
  sensirion_i2c_init();
  while (sps30_probe() != 0) {
    delay(500);
  }
  ret = sps30_set_fan_auto_cleaning_interval_days(auto_clean_days);
  ret = sps30_start_measurement();

  //SENSOR BH1750 =======================================================================================
  lightMeter.begin();

  //SENSOR AHT20 + BMP280 ===============================================================================
  if (!aht.begin()) {
    while (1);
  }
  if (!bmp.begin(0x77)) {
    while (1);
  }
}

void loop() {
  //SENSOR DE PARTICULADOS SPS30 ========================================================================
  sps30_start_measurement();
  delay(4000);

  do {
    ret = sps30_read_data_ready(&data_ready);
    if (ret < 0) {
      // erro, ignora e tenta novamente
    } else if (!data_ready) {
      delay(100);
    } else {
      break;
    }
  } while (1);

  ret = sps30_read_measurement(&m);
  sps30_stop_measurement();

  //SENSOR BH1750 =======================================================================================
  float lux = lightMeter.readLightLevel();

  //SENSOR AHT20 + BMP280 ===============================================================================
  sensors_event_t humidity, temp;
  aht.getEvent(&humidity, &temp);
  float pressure = bmp.readPressure() / 100.0F;

  // Criação do JSON ===============================================================================
  String jsonData = "{";
  jsonData += "\"pm\":{";
  jsonData += "\"1.0\":" + String(m.mc_1p0, 2) + ",";
  jsonData += "\"2.5\":" + String(m.mc_2p5, 2) + ",";
  jsonData += "\"4.0\":" + String(m.mc_4p0, 2) + ",";
  jsonData += "\"10.0\":" + String(m.mc_10p0, 2) + "},";
  
  jsonData += "\"nc\":{";
  jsonData += "\"0.5\":" + String(m.nc_0p5, 2) + ",";
  jsonData += "\"1.0\":" + String(m.nc_1p0, 2) + ",";
  jsonData += "\"2.5\":" + String(m.nc_2p5, 2) + ",";
  jsonData += "\"4.0\":" + String(m.nc_4p0, 2) + ",";
  jsonData += "\"10.0\":" + String(m.nc_10p0, 2) + "},";
  
  jsonData += "\"typical_size\":" + String(m.typical_particle_size, 2) + ",";
  jsonData += "\"light\":" + String(lux, 2) + ",";
  jsonData += "\"temperature\":" + String(temp.temperature, 2) + ",";
  jsonData += "\"humidity\":" + String(humidity.relative_humidity, 2) + ",";
  jsonData += "\"pressure\":" + String(pressure, 2);
  jsonData += "}";

  Serial.println(jsonData);
  

  for (int i = 0; i < 110; i++) {
    delay(100);
    yield();
  }

  //WIFI ================================================================================================

  WiFiClient client = sv.available(); //Cria o objeto cliente

  if (client) { //Se este objeto estiver disponível
    String line = ""; //Variável para armazenar os dados recebidos
    while (client.connected()) { //Enquanto estiver conectado
        if (client.available()) { //Se estiver disponível
          char c = client.read(); //Lê os caracteres recebidos
          if (c == '\n') { //Se houver uma quebra de linha
            if (line.length() == 0) { //Se a nova linha tiver 0 de tamanho
              client.println("HTTP/1.1 200 OK"); //Envio padrão de início de comunicação
              client.println("Content-type:text/html");
              client.println();

              client.println();
              break;
            } else {   
              line = "";
            }
          } else if (c != '\r') { 
            line += c; //Adiciona o caractere recebido à linha de leitura
          }
            
          if (line.endsWith("GET /sensores")) {  
            client.println("HTTP/1.1 200 OK"); //Envio padrão de início de comunicação
            client.println("Content-type:application/json");
            client.println();
            client.print(jsonData);
            break;                
          }
        }
      }

    client.stop(); //Para o cliente
  }
}
