#include <Arduino.h>
#include <ESP32Servo.h>
#include "actuator_manager.h"
#include "config.h"
static Servo vent;
void initializeActuators() {
  for(int pin:{config::LIGHT1_PIN,config::LIGHT2_PIN,config::FAN_PIN}) { pinMode(pin,OUTPUT); digitalWrite(pin,LOW); }
  vent.setPeriodHertz(50); vent.attach(config::SERVO_PIN,500,2400); vent.write(0);
  ledcSetup(14,2000,8); ledcAttachPin(config::BUZZER_PIN,14);
}
void applyActuators(const Actuators& a) {
  digitalWrite(config::LIGHT1_PIN,a.light1); digitalWrite(config::LIGHT2_PIN,a.light2);
  digitalWrite(config::FAN_PIN,a.fan); vent.write(a.servo); ledcWriteTone(14,a.alarm?2000:0);
}
