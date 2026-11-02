#pragma once
#include <cstdint>
enum class Mode { AUTO, MANUAL };
struct Sensors { float temperature=24, humidity=50, light=60, air=20; bool occupancy=false, valid=false; };
struct Actuators { bool light1=false, light2=false, fan=false, alarm=false; int servo=0; };
struct State {
  Sensors sensors;
  Actuators outputs, manual;
  Mode mode=Mode::AUTO;
  int mlClass=-1, alert=1;
  float confidence=0;
  double power=0, energyWh=0, autoWh=0, baselineWh=0;
  uint32_t lastEnergyMs=0;
  bool energyStarted=false;
  uint64_t commandVersion=0;
};
inline const char* className(int c) {
  static const char* names[]={"EMPTY","OCCUPIED_NORMAL","HIGH_ENERGY_USAGE","POOR_ENVIRONMENT","ABNORMAL_CONDITION"};
  return c>=0 && c<5 ? names[c] : "UNAVAILABLE";
}
inline const char* airName(float a) { return a>=85?"DANGEROUS":a>=60?"POOR":a>=35?"MODERATE":"GOOD"; }
