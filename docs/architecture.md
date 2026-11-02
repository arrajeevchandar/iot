# Architecture and state ownership

## Sensor and embedded layers

`sensor_manager.cpp` samples every 2 seconds. DHT22 values must be finite and physically within its range. Invalid values retain the last valid temperature/humidity, flag the state invalid, and open ventilation. Startup defaults are never reported as valid measurements. PIR reports motion-based occupancy; the PIR simulation's hold time governs the occupied interval. LDR AO is inverted into brightness percent. The potentiometer scales linearly into a fictional pollution index.

`State` groups sensors, mode, manual desired outputs, applied outputs, TinyML result, warnings, and energy. `automation_manager.h` is independent of Arduino and is compiled into the host unit tests unchanged.

## Decision priority

1. Integrate energy using the previous output power and previous mode.
2. Receive any newer validated manual/AUTO command.
3. Read sensors at the scheduled interval.
4. Compute normal AUTO outputs, or copy manual desired outputs.
5. Run TinyML every 5 seconds; unavailable inference leaves rule-based control active.
6. Critical thresholds or an ABNORMAL prediction force the vent to 180° and activate the alarm in either mode. DHT failure also opens the vent.
7. Apply GPIO/PWM outputs. Publish telemetry and serial status at their independent intervals.

AUTO lights turn on only when occupied and brightness <40%. Fan turns on only when occupied and temperature >28°C. Poor air ≥60, temperature >32°C, or a POOR_ENVIRONMENT prediction opens ventilation to 90°. Dangerous air ≥85 or temperature ≥45°C is critical. Humidity >75% produces a warning. Manual normal operation is not overridden by noncritical thresholds. The alarm is not latched: it clears when the critical condition clears; reset requests cannot suppress an active hazard.

## Intelligence layer

Six features include current power so energy waste is observable. An int8 model occupies 3,848 flash bytes; a fixed 24 KiB aligned tensor arena is allocated in RAM. Only FullyConnected and Softmax operators are registered. Input quantization uses the model's scale/zero-point and clamps to int8 range. Firmware checks schema, per-tensor quantization, and tensor sizes, invokes TFLM, and dequantizes output confidence. The software simulator executes the corresponding float dense layers using exported NumPy weights; it is labelled separately in the UI.

## Cloud and dashboard layers

A FreeRTOS worker handles Wi-Fi, NTP, TLS, and HTTP outside the main loop. Two one-element queues exchange snapshots and responses, bounding memory and dropping superseded telemetry rather than blocking controls. HTTPS uses a supplied root CA and valid NTP time; there is no `setInsecure()` path. Explicit lab-only HTTP is available for a controlled protocol exercise.

`POST /api/devices/{id}/telemetry` persists a snapshot and returns the latest desired command. Command versions are persistent, monotonically increasing integer microseconds. Repeated versions are ignored by the device. `applied_version` in subsequent telemetry acknowledges application. A pending command is never displayed as completed. Rebooted devices receive the latest persisted desired state. A device offline for more than 12 seconds is marked offline.

The browser polls every 2 seconds, renders the selected room's history, and uses authenticated HTTP requests for commands. SQLite retains at most 1,000 snapshots per room; charts show the latest 120. One server worker owns the local simulator and database writes. No frontend framework or external asset CDN is required.

## Energy calculation

`P = 20*light1 + 20*light2 + 60*fan` in watts. Servo standing power is 0 W by default and configurable in firmware. `ΔWh = previousP * elapsedMs / 3,600,000`; the unsigned millisecond subtraction handles wraparound. AUTO accumulation counts only intervals actually spent in AUTO. Baseline is 100 W over the same running time; saved Wh = baseline − actual; percentage = 100 × saved / baseline, with zero-baseline protection. This comparison does not prove causal savings in a real building.

## Expansion and boundaries

Give each additional device a unique `DEVICE_ID` such as classroom-102 and classroom-103; the API and room picker discover them from telemetry. IDs beginning `demo-` are reserved. The initial shared device token is for an academic installation; replace it with per-device credentials and authorization for a larger deployment. SQLite history is server-persistent, while ESP32 session counters reset on reboot. The local simulator restores counters but does not count server downtime as energy usage.
