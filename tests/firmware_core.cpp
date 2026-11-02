#include <cassert>
#include <cmath>
#include <iostream>
#include "automation_manager.h"
#include "energy_manager.h"
int main() {
  State s; s.sensors.valid=true;
  runAutomation(s); assert(!s.outputs.light1&&!s.outputs.fan);
  s.sensors.occupancy=true; s.sensors.light=10; s.sensors.temperature=30;
  runAutomation(s); assert(s.outputs.light1&&s.outputs.light2&&s.outputs.fan&&s.power==100);
  updateEnergyUsage(s,0); updateEnergyUsage(s,3600000); assert(s.energyWh==100&&s.autoWh==100&&s.baselineWh==100);
  s.mode=Mode::MANUAL; s.manual.light1=true; s.manual.servo=25;
  runAutomation(s); assert(s.outputs.light1&&!s.outputs.fan&&s.outputs.servo==25);
  updateEnergyUsage(s,7200000); assert(s.energyWh==120&&s.autoWh==100);
  s.sensors.air=95; runAutomation(s); assert(s.outputs.alarm&&s.outputs.servo==180&&s.alert==2);
  s.sensors.air=20; runAutomation(s); assert(!s.outputs.alarm&&s.outputs.servo==25);
  s.sensors.valid=false; runAutomation(s); assert(s.outputs.servo==180&&s.alert==1);
  State wrap; wrap.power=100; updateEnergyUsage(wrap,0xffffff00u); updateEnergyUsage(wrap,0x000002e8u);
  assert(std::abs(wrap.energyWh-100.0/3600)<1e-9);
  std::cout<<"Firmware core: occupancy, darkness, heat, manual, emergency, fault, elapsed energy and millis rollover passed\n";
}
