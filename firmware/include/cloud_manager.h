#pragma once
#include "system_state.h"
void initializeCloud();
void sendTelemetry(const State& s);
void receiveCommands(State& s);
