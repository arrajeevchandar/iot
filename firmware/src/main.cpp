#include <Arduino.h>
#include "config.h"
#include "system_state.h"
#include "sensor_manager.h"
#include "actuator_manager.h"
#include "automation_manager.h"
#include "energy_manager.h"
#include "tinyml_manager.h"
#include "cloud_manager.h"
static State state;
static uint32_t sensorAt=0, mlAt=0, cloudAt=0, printAt=0;
void setup() {
  Serial.begin(115200); initializeSensors(); initializeActuators();
  Serial.printf("SMART CLASSROOM | TinyML %s\n",initializeML()?"ready":"unavailable; rules active");
  initializeCloud(); updateEnergyUsage(state,millis());
}
void loop() {
  uint32_t now=millis();
  // Integrate the previous actuator state before applying any new command.
  updateEnergyUsage(state,now); receiveCommands(state);
  if(now-sensorAt>=config::SENSOR_MS) { sensorAt=now; readSensors(state.sensors); }
  runAutomation(state);
  if(now-mlAt>=config::ML_MS) { mlAt=now; if(!state.sensors.valid || !runInference(state)) { state.mlClass=-1; state.confidence=0; } runAutomation(state); }
  applyActuators(state.outputs);
  if(now-cloudAt>=config::CLOUD_MS) { cloudAt=now; sendTelemetry(state); }
  if(now-printAt>=config::SERIAL_MS) {
    printAt=now;
    Serial.printf("\n=== SMART CLASSROOM ===\nT %.1f C | RH %.1f%% | Light %.1f%% | Air %.1f (%s)\n%s | %s | sensor %s\nL1 %d L2 %d Fan %d Vent %d Alarm %d\nPower %.1f W | Energy %.5f kWh | Saved %.3f Wh\nTinyML %s (%.2f) | Alert %s\n",
      state.sensors.temperature,state.sensors.humidity,state.sensors.light,state.sensors.air,airName(state.sensors.air),
      state.sensors.occupancy?"OCCUPIED":"EMPTY",state.mode==Mode::AUTO?"AUTO":"MANUAL",state.sensors.valid?"OK":"FAULT",
      state.outputs.light1,state.outputs.light2,state.outputs.fan,state.outputs.servo,state.outputs.alarm,
      state.power,state.energyWh/1000,state.baselineWh-state.energyWh,className(state.mlClass),state.confidence,state.alert==2?"CRITICAL":state.alert==1?"WARNING":"INFO");
  }
  vTaskDelay(pdMS_TO_TICKS(10));
}
