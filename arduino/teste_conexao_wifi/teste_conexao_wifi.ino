#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "Lucy-WiFi";
const char* password = "Lucydog10@";

// IP do PC rodando o FastAPI
const char* serverUrl = "http://192.168.15.9:8000/esp";

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("Conectando ao WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi conectado");
  Serial.print("IP do ESP32: ");
  Serial.println(WiFi.localIP());

  HTTPClient http;
  http.begin(serverUrl);

  int httpCode = http.GET();

  if (httpCode > 0) {
    Serial.print("HTTP Code: ");
    Serial.println(httpCode);

    String payload = http.getString();
    Serial.println("Resposta:");
    Serial.println(payload);
  } else {
    Serial.print("Erro HTTP: ");
    Serial.println(httpCode);
  }

  http.end();
}

void loop() {
  // vazio por enquanto
}

