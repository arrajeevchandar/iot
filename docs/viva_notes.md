# Viva notes

**What does the project solve?** It demonstrates monitoring classroom conditions and reducing unnecessary appliance running time with occupancy-aware automation.

**Why ESP32 rather than Uno?** ESP32 includes Wi-Fi, more RAM/flash, multiple cores, ADC, and PWM, making networking and a small neural model feasible on one simulated device.

**What is IoT?** Devices sense/actuate locally and exchange state and commands over a network. The dashboard is one consumer; the device still controls its outputs without it.

**How is occupancy detected?** PIR output approximates occupancy from motion. It cannot count occupants and may miss stationary people; its hold time affects vacancy detection.

**Is the air sensor real?** No. A potentiometer represents a pollution index from 0 to 100. The thresholds are academic simulation settings, not certified exposure limits.

**Why GPIO34 and GPIO35?** They are ADC1 input pins, compatible with Wi-Fi operation, and are correctly used only as inputs.

**What is Blynk?** A hosted IoT dashboard platform. This project instead ships an open self-hosted dashboard to avoid requiring an account or paid datastream capacity. A Blynk mapping is documented as an optional extension.

**Why HTTP rather than MQTT?** HTTPS provides a simple request/response exchange: telemetry upload returns the latest desired command. MQTT would add a broker and push subscriptions, useful for larger fleets but not essential to this demo.

**What is TinyML?** Machine learning inference in a small embedded device with constrained memory and computation. Training happens on a computer; inference uses the exported model on ESP32.

**What is TensorFlow Lite Micro?** A microcontroller-oriented runtime for supported TensorFlow Lite models. This firmware registers only FullyConnected and Softmax and allocates a fixed tensor arena.

**Why use edge inference?** It reduces network dependency and keeps classification available during cloud outages. It does not make the model immune to bad sensor data or distribution shift.

**Why use ML if rules generated the labels?** It demonstrates the entire data/training/quantization/embedded-inference pipeline. On this synthetic dataset there is no established superiority over the rules; real data is necessary to show additional predictive value.

**What are the six inputs?** Temperature, humidity, normalized brightness, simulated air index, occupancy, and current power. Power makes waste observable when a room is empty but appliances remain on.

**What is quantization?** Representing weights/activations as int8 values with scale and zero-point. It reduces model size and supports embedded arithmetic. The exported binary is actually tested after conversion.

**How accurate is it?** The checked-in int8 model achieved 98.15% on 2,000 held-out synthetic examples. This is not field accuracy. Discuss per-class errors, per-tensor quantization compatibility, and distribution shift using `metrics.json`.

**How is energy calculated?** Sum configured active wattages, then integrate previous power over elapsed time: Wh = W × milliseconds / 3,600,000. Divide Wh by 1,000 for kWh.

**What is the savings baseline?** Both 20 W lights plus the 60 W fan continuously on during the same running time. Savings are a modelled comparison, not an electric meter measurement.

**What happens when the network fails?** A separate worker retries Wi-Fi/HTTP. Main-loop sensing, inference, emergency checks, actuators, and energy accounting continue. The dashboard labels stale telemetry offline.

**AUTO versus MANUAL?** AUTO follows occupancy/light/temperature rules. MANUAL uses desired appliance states from the dashboard. Critical danger and sensor-fault ventilation still override unsafe settings.

**Can alarm reset hide danger?** No. The alarm remains on while the critical condition exists and clears when it resolves. Reset is intentionally unable to bypass emergency logic.

**How are remote changes confirmed?** The device echoes the applied command version in later telemetry. Until then the dashboard displays pending rather than assuming success.

**What can Wireshark show?** Addresses, timing, DNS, TCP, UDP/NTP, TLS handshakes/records, and unencrypted HTTP when used. HTTPS JSON payloads are encrypted. Wokwi can export a capture through its Wi-Fi menu.

**What is Cooja/RPL?** Cooja simulates Contiki-NG motes and networks. RPL routes packets in low-power, lossy networks. This is an optional separate extension, not the ESP32 Wi-Fi stack.

**What differs from real deployment?** Simulated sensors are idealized, energy is estimated, PIR is simplistic, model labels are synthetic, and real appliances require electrical drivers, isolation, calibration, authentication, and operational testing.
