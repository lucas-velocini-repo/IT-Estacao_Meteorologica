//BIBLIOTECAS ==================================================================================================================
//#include <Wire.h> //GERAL

//#include <sps30.h> //SENSOR DE PARTICULADOS SPS30

//#include <BH1750.h> //SENSOR BH1750

//#include <Adafruit_AHTX0.h> //SENSOR AHT20 + BMP280
//#include <Adafruit_BMP280.h> 

#include <WiFi.h>
//#include <ESPmDNS.h>       //WIFI
#include <NetworkClient.h>
#include <HTTPClient.h>
//==============================================================================================================================

//DEFINIÇÕES E VARIÁVEIS =======================================================================================================
unsigned long lastReadTime = 0;
const unsigned long readInterval = 5000; //GERAL (11000 quando com sensores)
String lastJsonData = "{}";

const char* ssid = "Lucy-WiFi";
const char* password = "Lucydog10@";                              //WIFI e comunicação          
const char* serverUrlDados = "http://192.168.15.11:8000/dados"; 


//int16_t ret;
//uint8_t auto_clean_days = 4;
//uint32_t auto_clean;                      //SENSOR DE PARTICULADOS SPS30
//struct sps30_measurement m;
//char serial[SPS30_MAX_SERIAL_LEN];
//uint16_t data_ready;

//BH1750 lightMeter;                        //SENSOR BH1750 

//Adafruit_AHTX0 aht;                       //SENSOR AHT20 + BMP280
//Adafruit_BMP280 bmp;
//============================================================================================================================

void setup() {
  Serial.begin(115200);
  //Wire.begin(21, 22);
  
  //WIFI =================================================================================================
  Serial.println("Conectando ao WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi conectado");
  Serial.print("IP do ESP32: ");
  Serial.println(WiFi.localIP());

  //SENSOR DE PARTICULADOS SPS30 ========================================================================
  //sensirion_i2c_init();
  //while (sps30_probe() != 0) {
    //delay(500);
  //}
  //ret = sps30_set_fan_auto_cleaning_interval_days(auto_clean_days);
  //ret = sps30_start_measurement();

  //SENSOR BH1750 =======================================================================================
  //lightMeter.begin();

  //SENSOR AHT20 + BMP280 ===============================================================================
  //if (!aht.begin()) {
  //  while (1);
  //}
  //if (!bmp.begin(0x77)) {
  //  while (1);
  //}
}

void loop() {
  unsigned long currentTime = millis();

  // Verifica se já é hora de atualizar os sensores e atualiza o lastJsonData
  if (currentTime - lastReadTime >= readInterval) {
    lastReadTime = currentTime;
    //readSensors();  // Atualiza o lastJsonData
    readSensorsSim(); // Atualiza o lastJsonData
    sendPost();         // envia para o FastAPI
  }
}

/*
void readSensors() { // Função para ler sensores (executa a cada 11s no loop)
  //SPS30 
  sps30_start_measurement();
  delay(4000);
  uint16_t data_ready;
  int16_t ret;
  struct sps30_measurement m;

  while (true) {
    ret = sps30_read_data_ready(&data_ready);
    if (ret >= 0 && data_ready) break;
    delay(100);
  }
  ret = sps30_read_measurement(&m);
  sps30_stop_measurement();

  //BH1750
  float lux = lightMeter.readLightLevel();

  //AHT20 + BMP280
  sensors_event_t humidity, temp;
  aht.getEvent(&humidity, &temp);
  float pressure = bmp.readPressure() / 100.0F;

  //JSON
  lastJsonData = "{";
  lastJsonData += "\"pm\":{";
  lastJsonData += "\"1.0\":" + String(m.mc_1p0, 2) + ",";
  lastJsonData += "\"2.5\":" + String(m.mc_2p5, 2) + ",";
  lastJsonData += "\"4.0\":" + String(m.mc_4p0, 2) + ",";
  lastJsonData += "\"10.0\":" + String(m.mc_10p0, 2) + "},";
  
  lastJsonData += "\"nc\":{";
  lastJsonData += "\"0.5\":" + String(m.nc_0p5, 2) + ",";
  lastJsonData += "\"1.0\":" + String(m.nc_1p0, 2) + ",";
  lastJsonData += "\"2.5\":" + String(m.nc_2p5, 2) + ",";
  lastJsonData += "\"4.0\":" + String(m.nc_4p0, 2) + ",";
  lastJsonData += "\"10.0\":" + String(m.nc_10p0, 2) + "},";
  
  lastJsonData += "\"typical_size\":" + String(m.typical_particle_size, 2) + ",";
  lastJsonData += "\"light\":" + String(lux, 2) + ",";
  lastJsonData += "\"temperature\":" + String(temp.temperature, 2) + ",";
  lastJsonData += "\"humidity\":" + String(humidity.relative_humidity, 2) + ",";
  lastJsonData += "\"pressure\":" + String(pressure, 2);
  lastJsonData += "}";

  Serial.println(lastJsonData);
}
*/

void sendPost() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi desconectado");
    return;
  }

  HTTPClient http;

  http.begin(serverUrlDados);
  http.addHeader("Content-Type", "application/json");

  int httpResponseCode = http.POST(lastJsonData);

  Serial.print("POST -> código HTTP: ");
  Serial.println(httpResponseCode);

  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("Resposta do servidor:");
    Serial.println(response);
  } else {
    Serial.println("Erro ao enviar POST");
  }

  http.end();
}

void readSensorsSim() { // Função para ler sensores (executa a cada 5s)
  //JSON
  lastJsonData = "{";
  lastJsonData += "\"pm\":{";
  lastJsonData += "\"1.0\":" + String(random(0, 101)/100.0, 2) + ",";
  lastJsonData += "\"2.5\":" + String(random(0, 101)/100.0, 2) + ",";
  lastJsonData += "\"4.0\":" + String(random(0, 101)/100.0, 2) + ",";
  lastJsonData += "\"10.0\":" + String(random(0, 101)/100.0, 2) + "},";
  
  lastJsonData += "\"nc\":{";
  lastJsonData += "\"0.5\":" + String(random(0, 1001)/100.0, 2) + ",";
  lastJsonData += "\"1.0\":" + String(random(0, 1001)/100.0, 2) + ",";
  lastJsonData += "\"2.5\":" + String(random(0, 1001)/100.0, 2) + ",";
  lastJsonData += "\"4.0\":" + String(random(0, 1001)/100.0, 2) + ",";
  lastJsonData += "\"10.0\":" + String(random(0, 1001)/100.0, 2) + "},";
  
  lastJsonData += "\"typical_size\":" + String(random(0, 1001)/100.0, 2) + ",";
  lastJsonData += "\"light\":" + String(random(10000, 11000)/10.0, 2) + ",";
  lastJsonData += "\"temperature\":" + String(random(2500, 2580)/100.0, 2) + ",";
  lastJsonData += "\"humidity\":" + String(random(500, 1001)/10.0, 2) + ",";
  lastJsonData += "\"pressure\":" + String(random(9000, 10001)/10.0, 2);
  lastJsonData += "}";

  //Serial.println(lastJsonData);
}