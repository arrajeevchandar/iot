#include <Arduino.h>
#include <DHT.h>
#include <cmath>
#include "config.h"
#include "sensor_manager.h"
static DHT dht(config::DHT_PIN,DHT22);
void initializeSensors() { dht.begin(); pinMode(config::PIR_PIN,INPUT); analogReadResolution(12); }
void readSensors(Sensors& s) {
  float t=dht.readTemperature(), h=dht.readHumidity();
  s.valid=std::isfinite(t)&&std::isfinite(h)&&t>=-40&&t<=80&&h>=0&&h<=100;
  if(s.valid) { s.temperature=t; s.humidity=h; }
  else Serial.println("WARNING: DHT22 invalid; retaining last reading, opening vent");
  // Wokwi LDR module AO rises in darkness. Brightness, not lux, is displayed.
  s.light=100.0f*(4095-analogRead(config::LDR_PIN))/4095;
  s.air=100.0f*analogRead(config::AIR_PIN)/4095;
  s.occupancy=digitalRead(config::PIR_PIN)==HIGH;
}
