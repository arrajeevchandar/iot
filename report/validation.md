# Execution evidence and remaining acceptance steps

Validated in the cloud workspace on 9 October 2026. Results describe this working instance, not a published cloud service or restoration in another task.

| Check | Observed result |
|---|---|
| Dependency installation | Python 3.12 virtual environment installed; `pip check` reports no broken requirements |
| Standard ESP32 build | PlatformIO `esp32dev` completed successfully; 70,628 bytes static RAM and 836,381 bytes flash |
| Official-source fallback build | Completed successfully with SHA-256-verified Espressif framework/compiler archives |
| Firmware packaging | Bootloader + partition table + application merged into a Wokwi-uploadable binary |
| Dataset | 10,000 seeded, balanced synthetic rows generated |
| Model training | 6,800 training / 1,200 validation / 2,000 test examples; real trained weights exported |
| TFLite int8 | 3,848 bytes; held-out synthetic accuracy 98.15%; five representative classes tested |
| Actual Micro runtime on host | Allocated the same 24 KiB arena and passed all five classes; 1,964/2,000 held-out labels correct (98.20%), 1,999/2,000 predictions agree with desktop int8 |
| Python suite | 24 tests passed, no skipped tests with TensorFlow installed; two dependency deprecation warnings |
| Native firmware controller | Passed occupancy, light, heat, manual, emergency, sensor-fault, elapsed-energy, and timer-rollover assertions |
| Browser tests | Passed actual UI interactions, acknowledgements, emergency reset behavior, charts, desktop/mobile layout; no page JavaScript errors |
| HTTP service | Started with `scripts/run.sh`; health, telemetry, history, commands, validation, and authentication exercised |
| Credentials | Distinct random application tokens generated locally in ignored `.env`, permission mode 0600; values not printed |
| Setup repeatability | `bash scripts/setup.sh --full` rerun successfully, preserving existing credentials |
| Wokwi ESP32 execution | Actual merged firmware boots with `TinyML ready`; valid DHT/LDR/air readings, empty-room shutdown, dark/hot occupancy at 100 W, 46°C emergency and 94.8 air-index emergency verified |

Real dashboard screenshots are in `screenshots/`. Exact model metrics and checksum are in `tinyml/models/metrics.json`. Firmware artifacts are generated under `.pio/build/esp32dev/`; the merged image is `runtime/classroom-esp32dev.bin`.

The Micro-runtime check exposed an incompatibility in TensorFlow 2.19's default per-channel dense quantization with the pinned embedded kernels. Export was changed to per-tensor int8, the firmware now rejects incompatible quantization, and the corrected model was re-evaluated and rebuilt. The one desktop/Micro prediction difference among 2,000 test examples reflects numerical differences near a class boundary, not perfect parity. These are actual host Micro-kernel tests, not Wokwi execution.

## What has not been established

- Wokwi-to-public-HTTPS-dashboard operation: no user-owned hosting endpoint/certificate configuration was supplied or provisioned. The local UI/API workflow is separately verified.
- Account creation: no Wokwi, Blynk, or hosting account was created. The local demo does not need one; generated project tokens are not third-party account credentials.
- An actual PCAP, physical sensor measurement, or real-world energy saving: none is claimed. Capture instructions are supplied for an honest experiment.
- Blynk transport and Cooja execution: documented as optional extensions, not implemented runtime integrations.
- Docker execution, hosted GitHub Actions, environment publication, or fresh-task restoration: configuration files exist, but those external operations have not been performed.

## Wokwi evidence

After the user authorized continuing the certificate-store correction, the environment proxy CA was installed in Chromium's trust store. TLS verification remained enabled. The real browser simulator ran the repository's compiled ESP32 firmware and diagram, without saving or publishing the public template.

`report/wokwi_serial.log` and `screenshots/wokwi-*.png` record the actual simulator output. `node scripts/test_wokwi.cjs` reproduces the external sensor tests. The pollution index is a potentiometer-derived simulation value, not ppm. The 100 W reading is the configured load estimate, not measured electrical consumption.

A free Cloudflare Quick Tunnel was attempted using a checksum-verified official client. Direct DNS failed in this environment and the proxied API check returned HTTP 403; no public endpoint was created. The temporary extra backend was stopped. To finish external acceptance, configure an accessible public HTTPS service and device credentials, then test telemetry, command acknowledgements, reconnection and manual safety override over that path. These cloud cases remain unverified on Wokwi, despite passing local API/controller tests.
