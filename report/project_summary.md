# IoT-Based Smart Campus Classroom Monitoring and Energy Management System Using ESP32, Wokwi, Cloud Dashboard, and TinyML

## 1. Introduction

Classrooms combine variable occupancy, lighting needs, temperature, and ventilation requirements. This project models an intelligent classroom controller that observes these conditions, controls simulated appliances, and makes its operation visible through a network dashboard. Its simulation-first design is suitable for an MCA semester evaluation without physical hardware.

## 2. Problem statement

Lights and fans may operate in empty rooms, uncomfortable conditions may go unnoticed, and manual observation does not provide consistent telemetry or history. The project investigates how occupancy-aware local rules, remote supervision, and embedded classification can address those problems in a controlled simulation.

## 3. Objectives

Monitor environmental inputs; provide AUTO and MANUAL control; preserve emergency behavior; estimate energy and savings; demonstrate real TinyML training and inference; transmit state and receive commands; and support network-protocol analysis with reproducible documentation.

## 4. Proposed system

A Wokwi ESP32 reads DHT22, PIR, LDR, and potentiometer inputs. It operates two light LEDs, a fan LED, a ventilation servo, and a buzzer. A background HTTP(S) task exchanges state and desired commands with the included FastAPI service. A separate software classroom supports an account-free local demonstration and is clearly identified as such.

## 5. Architecture

Sensors feed structured state. Deterministic automation and a TFLite Micro model determine outputs. Elapsed-time integration tracks nominal energy. The HTTPS worker exchanges bounded messages with the main loop so networking cannot stop control. The server persists snapshots in SQLite and the browser displays telemetry, charts, energy, alerts, and command acknowledgement. See `docs/architecture.md` for data flow and priorities.

## 6. Technologies used

ESP32 Arduino core, PlatformIO, Wokwi, DHT/servo libraries, ArduinoJson, TensorFlow, TensorFlow Lite Micro, Python, NumPy, FastAPI, SQLite, HTML/CSS/JavaScript, pytest, C++, Playwright, and Wireshark. No mandatory paid API or physical component is needed for the local workflow. Blynk and Cooja are optional alternatives/extensions.

## 7. Modules

The firmware separates configuration, sensor management, actuators, automation, energy, cloud exchange, and TinyML inference. The server separates validated API schemas, persistent state, and the local simulator. Training, model conversion, source export, build fallback, credentials, and testing have separate scripts. This modular organization supports incremental evaluation and replacement of individual components.

## 8. TinyML

A seeded 10,000-row synthetic dataset covers five classes: EMPTY, OCCUPIED_NORMAL, HIGH_ENERGY_USAGE, POOR_ENVIRONMENT, and ABNORMAL_CONDITION. Six normalized features feed a small dense network. The actual int8 export is 3,848 bytes and obtained 98.15% accuracy on 2,000 held-out synthetic examples. Per-tensor quantization ensures compatibility with the pinned Micro dense kernels. This validates the synthetic pipeline, not real-world predictive accuracy. Threshold-based safety operates independently of the model.

## 9. Energy management

Nominal loads are 20 W per light and 60 W for the fan. Previous active power is integrated over measured elapsed time, producing Wh and kWh. A continuously on 100 W reference produces baseline energy, and its difference from actual modeled consumption produces estimated savings. AUTO consumption is separately accumulated. These are estimates with explicit assumptions, not metered consumption or measured building savings.

## 10. Cloud integration

The chosen free alternative to Blynk is a self-hosted dashboard/API. Devices send telemetry via HTTP(S) and receive persistent versioned commands in the response. Subsequent telemetry acknowledges application. Distinct bearer tokens protect device and dashboard operations in public mode. The free Wokwi public gateway requires an Internet-accessible HTTPS endpoint; hosting configuration and access must be provided for that external acceptance run. The repository does not claim an account or public deployment was created.

## 11. Network analysis

Wireshark can inspect Wokwi-exported PCAPs or actual local browser/server captures. Relevant protocols include 802.11, DNS, TCP, UDP/NTP, HTTP, and TLS. Encrypted JSON cannot be read without legitimate decryption material. The report must include only real captures from the performed experiment. The optional Cooja design represents multiple Contiki-NG classrooms and an RPL border router; it is not the primary firmware.

## 12. Testing

The test plan covers empty/dark/hot conditions, poor/dangerous air, manual operation, emergency overrides, sensor/ML faults, elapsed energy, command delivery, authentication, persisted state, actual int8 model predictions, desktop/mobile browser behavior, and firmware compilation. Wokwi sensor interaction and hosted network behavior must be evidenced independently of unit tests. Actual execution results and limitations are in `validation.md`.

## 13. Results

The implemented local demonstration shows live monitoring, responsive controls, estimated energy, alerts, neural classification, and stored history. Native controller tests and browser workflows verify those capabilities; the ESP32 firmware compiles with its actual TFLM dependency. Synthetic model evaluation and generated screenshots are included. Do not replace these bounded results with unsupported claims about real energy savings, physical hardware, or an unperformed public-cloud run.

## 14. Limitations

The air-quality input is fictional, occupancy is motion-based, and energy uses nominal wattages. Model training uses rule-labelled synthetic data; boundary cases and domain shift remain concerns. The device's counters reset on reboot. Public free hosting may sleep or lose ephemeral storage. The academic server uses a shared device token and one worker. Full Wokwi-to-cloud acceptance remains dependent on a trusted browser environment and configured endpoint.

## 15. Future scope

Introduce calibrated physical sensors, real energy metering, people-counting or schedule-aware occupancy, per-device authorization, cloud database storage, MQTT push commands, robust offline buffering, real labelled datasets, model monitoring, and a measured multi-node Cooja experiment.

## 16. Conclusion

The project provides a reproducible engineering foundation spanning embedded control, networking, dashboard development, energy estimation, and model deployment. Its demonstrations explicitly distinguish implemented behavior, validated behavior, simulated assumptions, and external verification still required.
