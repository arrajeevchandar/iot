#pragma once
#include "system_state.h"
#include "config.h"
// Kept independent of Arduino so the very same controller can be unit tested on a host.
inline void runAutomation(State& s) {
  const auto& x=s.sensors;
  s.outputs=s.mode==Mode::MANUAL ? s.manual : Actuators{};
  if(s.mode==Mode::AUTO) {
    s.outputs.light1=s.outputs.light2=x.occupancy && x.light<config::LOW_LIGHT;
    s.outputs.fan=x.occupancy && x.temperature>config::FAN_TEMP;
    s.outputs.servo=(x.air>=config::AIR_POOR || x.temperature>32 || s.mlClass==3)?90:0;
  }
  s.alert=(!x.valid || x.air>=config::AIR_POOR || x.temperature>32 || x.humidity>75 || s.mlClass==3)?1:0;
  const bool critical=x.air>=config::AIR_DANGER || x.temperature>=config::TEMP_DANGER || s.mlClass==4;
  // Safety overrides manual mode, and cannot be silenced while the hazard persists.
  if(critical) { s.outputs.servo=180; s.outputs.alarm=true; s.alert=2; }
  if(!x.valid) { s.outputs.servo=180; s.alert=critical?2:1; }
  s.power=(s.outputs.light1?config::LIGHT1_W:0)+(s.outputs.light2?config::LIGHT2_W:0)+(s.outputs.fan?config::FAN_W:0)+(s.outputs.servo?config::SERVO_W:0);
}
