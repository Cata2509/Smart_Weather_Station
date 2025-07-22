#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"
#include <Wire.h>
#include <BH1750.h>
#include <Adafruit_BMP280.h>
#include <TFT_eSPI.h>
#include <SPI.h>

// === Configurare senzori ===
#define DHTPIN 27
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

#define UVPIN 35
#define RAIN_DIGITAL 26
#define RAIN_ANALOG 36

BH1750 lightMeter;
Adafruit_BMP280 bmp;
TFT_eSPI tft = TFT_eSPI();

// === WiFi și server ===
const char* ssid = "TP-Link_515C";
const char* password = "hera2000";
const char* serverName = "http://192.168.1.130:5000/data";

void setup() {
  Serial.begin(115200);
  dht.begin();
  pinMode(RAIN_DIGITAL, INPUT);
  Wire.begin();

  if (lightMeter.begin()) Serial.println("BH1750 OK");
  else Serial.println("Eroare BH1750");

  if (bmp.begin(0x76)) Serial.println("BMP280 OK");
  else Serial.println("Eroare BMP280");

  WiFi.begin(ssid, password);
  Serial.print("Conectare la Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConectat!");

  // === Inițializare LCD ===
  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(2);
}

void loop() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  int uvValue = analogRead(UVPIN);
  float uvVoltage = uvValue * (3.3 / 4095.0);

  int rainDigital = digitalRead(RAIN_DIGITAL);
  String rainStatus = (rainDigital == HIGH) ? "Nu plouă" : "Plouă";
  int rainAnalog = analogRead(RAIN_ANALOG);

  float lightLevel = lightMeter.readLightLevel();
  float pressure = bmp.readPressure() / 100.0;

  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Eroare citire DHT22");
    delay(7000);
    return;
  }

  if (isnan(lightLevel)) lightLevel = 0.0;
  if (isnan(pressure)) pressure = 0.0;

  // === Afișare pe LCD ===
  tft.fillScreen(TFT_BLACK);
  tft.setCursor(0, 0);
  tft.printf("Temp: %.1f C\n", temperature);
  tft.printf("Umid: %.1f %%\n", humidity);
  tft.printf("Pres: %.1f hPa\n", pressure);
  tft.printf("Lumina: %.1f lx\n", lightLevel);
  tft.printf("UV: %d\n", uvValue);
  tft.printf("Ploua: %s\n", rainStatus.c_str());

  // === Serial Monitor ===
  Serial.println("===== Date meteo =====");
  Serial.printf("Temperatură: %.1f °C\n", temperature);
  Serial.printf("Umiditate: %.1f %%\n", humidity);
  Serial.printf("UV: %d (%.2f V)\n", uvValue, uvVoltage);
  Serial.printf("Status ploaie: %s\n", rainStatus.c_str());
  Serial.printf("Valoare analogică ploaie: %d\n", rainAnalog);
  Serial.printf("Luminozitate: %.1f lx\n", lightLevel);
  Serial.printf("Presiune: %.2f hPa\n", pressure);
  Serial.println("========================");

  // === Trimitere date spre Flask ===
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");

    String json = "{";
    json += "\"temperature\":" + String(temperature) + ",";
    json += "\"humidity\":" + String(humidity) + ",";
    json += "\"uvValue\":" + String(uvValue) + ",";
    json += "\"uvVoltage\":" + String(uvVoltage, 2) + ",";
    json += "\"rainStatus\":\"" + rainStatus + "\",";
    json += "\"rainAnalog\":" + String(rainAnalog) + ",";
    json += "\"lightLevel\":" + String(lightLevel) + ",";
    json += "\"pressure\":" + String(pressure);
    json += "}";

    int httpCode = http.POST(json);
    if (httpCode > 0) {
      String response = http.getString();
      Serial.println("Răspuns server: " + response);
    } else {
      Serial.println("Eroare trimitere: " + String(httpCode));
    }
    http.end();
  } else {
    Serial.println("Wi-Fi deconectat.");
  }

  delay(7000);
}
