#pragma once
#include <cstdint>
namespace config {
constexpr int DHT_PIN=15, PIR_PIN=13, LDR_PIN=34, AIR_PIN=35;
constexpr int LIGHT1_PIN=18, LIGHT2_PIN=19, FAN_PIN=21, SERVO_PIN=23, BUZZER_PIN=25;
constexpr uint32_t SENSOR_MS=2000, CLOUD_MS=3000, ML_MS=5000, SERIAL_MS=5000;
constexpr float FAN_TEMP=28, LOW_LIGHT=40, AIR_POOR=60, AIR_DANGER=85, TEMP_DANGER=45;
constexpr double LIGHT1_W=20, LIGHT2_W=20, FAN_W=60, SERVO_W=0;
constexpr uint32_t WIFI_RETRY_MS=15000;
}
