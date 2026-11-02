# Optional Blynk extension and virtual-pin design

The shipped cloud transport is the included free HTTP dashboard. **No Blynk transport is enabled or claimed to work in this version.** This guide defines a concrete replacement interface for an optional follow-on integration. Free-tier quotas and datastream limits change, so check the current Blynk console before choosing it. The supplied dashboard already supports every required data/control field without those quotas.

## Account and template setup

1. Visit the official Blynk website, create your own account, and complete its verification privately.
2. In the console's developer/template area create a template named `Smart Classroom`, hardware `ESP32`, connection `WiFi`.
3. Add the datastreams below where your plan permits them. Use the numeric bounds shown; enum text can be supplied through value mappings or labels.
4. Create a device from the template. The console supplies Template ID, Template Name, and device Auth Token. Put them in a local ignored secrets file or secure environment settings, never in a shared Wokwi sketch or Git.
5. Add gauge/value widgets for sensors, a selector for mode, switches for lights/fan, a slider for servo, charts for sensor history, and a warning display.
6. To implement the optional transport, replace only the cloud manager with Blynk initialization, timed virtual writes, and virtual-pin callbacks that fill the same validated desired-state struct. Keep networking off the main control task, preserve acknowledgement semantics, and retain independent safety rules.
7. After implementing, verify a virtual write appears in the dashboard, a MANUAL switch changes a Wokwi LED, and unplugged network connectivity leaves local automation running. These Blynk-specific checks have **not** been performed for the shipped HTTP implementation.

## Proposed exact mapping for that extension

| Pin | Meaning | Type/range | Direction |
|---|---|---|---|
| V0 | Temperature °C | double −40..80 | Device → cloud |
| V1 | Humidity % | double 0..100 | Device → cloud |
| V2 | Light % | double 0..100 | Device → cloud |
| V3 | Simulated air index | double 0..100 | Device → cloud |
| V4 | Occupancy | integer 0/1 | Device → cloud |
| V5 | Mode | integer 0=AUTO, 1=MANUAL | Both |
| V6 | Light 1 | integer 0/1 | Both |
| V7 | Light 2 | integer 0/1 | Both |
| V8 | Fan | integer 0/1 | Both |
| V9 | Servo degrees | integer 0..180 | Both |
| V10 | TinyML class | integer −1 unavailable, 0..4 classes | Device → cloud |
| V11 | Power W | double 0..100 | Device → cloud |
| V12 | Total energy Wh | double ≥0 | Device → cloud |
| V13 | Saved energy Wh | double, signed | Device → cloud |
| V14 | Alert | integer 0=INFO, 1=WARNING, 2=CRITICAL | Device → cloud |
| V15 | Alarm reset request | integer pulse 1 | Cloud → device |

Receiving actuator pins in AUTO must not bypass normal rules. Reset cannot suppress a continuing critical hazard. Blynk tokens are credentials issued by Blynk; locally generated dashboard tokens are not substitutes.
