#pragma once
#include "system_state.h"
#include "config.h"
inline void updateEnergyUsage(State& s, uint32_t now) {
  if(s.energyStarted) {
    const double hours=static_cast<uint32_t>(now-s.lastEnergyMs)/3600000.0;
    s.energyWh+=s.power*hours;
    if(s.mode==Mode::AUTO) s.autoWh+=s.power*hours;
    s.baselineWh+=(config::LIGHT1_W+config::LIGHT2_W+config::FAN_W)*hours;
  }
  s.lastEnergyMs=now; s.energyStarted=true;
}
