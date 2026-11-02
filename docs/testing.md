# Testing and acceptance

## Automated checks

Run from the repository root with dependencies installed:

```bash
.venv/bin/python -m pytest -q
g++ -std=c++17 -Wall -Wextra -Werror -Ifirmware/include tests/firmware_core.cpp -o /tmp/classroom-core-test
/tmp/classroom-core-test
export PLATFORMIO_CORE_DIR=/workspace/.platformio
.venv/bin/pio run -e esp32dev -j 4
.venv/bin/python scripts/merge_firmware.py --environment esp32dev
```

The Python suite tests automatic/manual logic, emergencies, faults, real model outputs, quantized artifact identity, API credentials and validation, command delivery/acknowledgement, persistence, and diagram structure. TensorFlow-dependent inference tests explicitly skip if TensorFlow is absent; install `tinyml/requirements.txt` for the full suite. A skipped test is not a pass.

The native C++ test compiles the actual `automation_manager.h` and `energy_manager.h`, covering empty/occupied/dark/hot behavior, manual state, emergency override, sensor fault, energy by mode, and millisecond rollover. It does not emulate sensor electronics or Wi-Fi.

`python scripts/test_tflm_native.py` builds the pinned TFLM runtime on the host, links the actual firmware inference wrapper/model, and tests allocation plus all five classes. This verifies the Micro interpreter/kernel combination, but is not a claim of execution on an ESP32 or in Wokwi.

## Browser acceptance

Start `bash scripts/run.sh`, then in another terminal:

```bash
npm ci
npm run test:browser
```

The Linux browser test uses a pinned Chromium package from npm. It operates real controls and waits for state transitions/acknowledgements. It covers empty/dark/hot/danger presets, critical alarm reset behavior, MANUAL lights/servo, return to AUTO, energy charts, and mobile overflow. Actual screenshots are saved under `screenshots/`. This changes the software simulator, not a physical device. Any failed API call or browser JavaScript exception must be investigated.

## Scenario matrix

| Test | Inputs/action | Expected behavior |
|---|---|---|
| Empty | AUTO, occupancy=false, safe air/temp | Both lights and fan off; baseline continues |
| Dark and occupied | occupancy=true, light=10%, 24°C | Both lights on, 40 W |
| Hot and occupied | occupancy=true, 35°C, normal light | Fan on, 60 W, ventilation open, warning |
| Poor air | air=70 | AUTO ventilation 90°, warning |
| Dangerous air | air=95 in either mode | Ventilation 180°, alarm, critical |
| Manual | Safe sensors; MANUAL; light1 on, servo75 | Desired values applied after acknowledgement |
| Active reset | Reset while air=95 | Alarm remains on |
| Return AUTO | AUTO after manual-on in empty room | Normal AUTO rules resume; lights/fan off |
| DHT fault | Mark local sensor invalid / invalid DHT read | Last valid values retained on ESP32, fault flag, vent open, ML unavailable |
| ML unavailable | Missing weights / failed allocation | Rules still control appliances, prediction explicitly unavailable |
| Internet failure | Stop server/disconnect network | ESP32 sensing/automation/energy continue; cloud retries |
| Reconnection | Restore server/network | New telemetry appears; pending command is delivered |
| Multiple rooms | Two unique device IDs | Separate latest states, commands, and histories |
| Energy math | 100 W for one hour | 100 Wh actual and baseline; 0 saved |
| Quantized classes | Five samples in model test | Actual int8 output matches all five representative classes |

## Wokwi acceptance

Successful compilation is not a completed Wokwi run. The diagram test checks intended wiring structurally; it does not prove simulator pin models or interactions. Run the merged image in the free browser simulator following `wokwi_setup.md`, then execute the scenario matrix and save real serial logs/screenshots. A public HTTPS endpoint is required to complete the Wokwi-to-dashboard portion with the free public gateway. A local loopback browser test is not equivalent to that path.

The actual ESP32 image has now run in Wokwi: empty shutdown, DHT temperature emergency, dark/hot motion-triggered lights and fan, and potentiometer air emergency passed. Run `node scripts/test_wokwi.cjs` after building/merging to repeat these checks; it uses an unsaved template and writes actual serial logs/screenshots. It needs trusted HTTPS access to Wokwi. The environment CA-store correction was authorized and applied; TLS verification was not disabled. This test does not supply cloud credentials, publish a Wokwi project, or verify remote commands.

For delivered build/test evidence see `report/validation.md`. Blynk and Cooja are optional extension designs, not passing runtime checks. No packet capture or hardware measurement is fabricated.
