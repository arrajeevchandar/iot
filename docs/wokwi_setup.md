# Wokwi simulation without physical hardware

## Recommended: free browser + locally compiled firmware

Use the [official ESP32 custom firmware template](https://wokwi.com/projects/305457271083631168). The [Wokwi ESP32 documentation](https://docs.wokwi.com/guides/esp32#custom-application-firmware) describes the F1 upload command. This route avoids requiring Wokwi CLI, private gateway, or a VS Code subscription.

Build with PlatformIO. Then merge the bootloader, partition table, and application:

```bash
.venv/bin/python scripts/merge_firmware.py --environment esp32dev
# For the verified official-source fallback build:
.venv/bin/python scripts/merge_firmware.py --environment source-build
```

The output is `runtime/classroom-<environment>.bin`. In the Wokwi project, paste the provided `wokwi/diagram.json`, focus the editor, press F1, and choose **Upload Firmware and Start Simulation…**. Select this merged binary. Uploads remain local to your browser according to the template workflow; saving a project/account is separate. Never publicly share a binary built with private credentials.

Expected serial output: `SMART CLASSROOM | TinyML ready`, followed by one status block every five simulated seconds. A DHT22 startup read may fail before its first valid sample; the system opens ventilation while invalid. If TinyML cannot allocate/execute, rules stay active and its classification is explicitly unavailable.

## Circuit controls

- Click DHT22 and change temperature/humidity. Temperature above 28°C starts the fan only while occupied; ≥45°C always triggers the emergency override.
- Click the PIR and trigger motion. Its output hold time means occupancy will not disappear immediately after a click. Wait for its pulse to expire to test empty-room behavior.
- Change photoresistor illuminance. The UI shows normalized inverse ADC percentage, not the lux setting. Lower brightness below 40% to test lighting.
- Turn the potentiometer: normalized values ≥60 open the vent; ≥85 activate the buzzer and open it fully. This is a fictional air-quality index, not CO₂ or PM2.5.
- Yellow LEDs are the two light circuits. Blue LED represents a fan; it is not a simulated physical motor. Servo position represents ventilation.

All sensor analog supplies are 3.3 V. The servo/PIR use the simulated VIN rail and all grounds are common. No physical hardware is expected.

## Alternative source import

`python scripts/export_wokwi.py` derives `wokwi/sketch.ino` and an example secrets file from modular firmware. Import the sketch, diagram, library list, and example secrets into a browser project. Add private settings only to your own appropriate environment. The export never reads `secrets.h`. The checked-in PlatformIO build pins Arduino core 2.0.17; Wokwi's current browser compiler may differ. If a browser compiler rejects old LEDC/servo APIs, use the verified merged binary route rather than changing library versions at random.

## Optional local editor

`wokwi/wokwi.toml` points to the standard PlatformIO output. For `source-build`, change its paths to `../.pio/build/source-build/firmware.bin` and `.elf` in your local configuration. Check current Wokwi VS Code/CLI licensing before using it. The free demonstration does not rely on a paid private gateway.

## Online data

`Wokwi-GUEST` has no password. The public gateway supports outbound Internet traffic but cannot reach your workstation's loopback address. Configure a public HTTPS dashboard as described in [cloud setup](cloud_setup.md). Without one, local automation/ML still work and cloud publishing is disabled by the empty default URL. This is intentional and is not a successful cloud connection.
