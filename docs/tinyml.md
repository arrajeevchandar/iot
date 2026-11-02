# TinyML: an actual deployable model

## Features and purpose

The feature vector is `[temperature, humidity, light, air_quality, occupancy, power_w]`. Divide by `[50,100,100,100,1,100]`, respectively. Power is included because environmental readings alone cannot distinguish a correctly powered empty room from appliances left on in an empty room. Sensors and power are read before inference; the model contributes ventilation/alert information but cannot disable deterministic safety rules.

This small network demonstrates training, quantization, deployment, and edge inference. Since labels come from explicit synthetic rules, it is not evidence that a neural network is superior to those same rules. Its value here is the engineering pipeline and a foundation for later labelled real-world data.

## Labels, with precedence

| ID | Class | Synthetic label definition |
|---|---|---|
| 4 | ABNORMAL_CONDITION | Air ≥85 or temperature ≥45°C |
| 3 | POOR_ENVIRONMENT | Otherwise air ≥60, temperature >32°C, or humidity >75% |
| 2 | HIGH_ENERGY_USAGE | Otherwise unoccupied with nonzero power, or bright (≥60%), cool (≤28°C), and power ≥40 W |
| 1 | OCCUPIED_NORMAL | Otherwise occupied |
| 0 | EMPTY | Otherwise empty |

Safety/environment take precedence over occupancy and waste labels. Thus an empty room with dangerous air is ABNORMAL, not EMPTY. There are no fabricated random ML predictions in the application.

## Data generation and evaluation

`generate_dataset.py` uses a seeded generator, uniformly sampled temperature 16–50°C, humidity 25–95%, brightness/air index 0–100, binary occupancy, and physically possible nominal powers `[0,20,40,60,80,100]`. Rejection sampling creates 2,000 examples per class, yielding 10,000 rows. The data includes hypothetical manual operation and faults rather than only AUTO-consistent conditions. It is deliberately balanced; real-world class frequencies will differ.

Training cleans nonfinite rows and duplicates, normalizes with fixed scales, then uses stratified splits of 6,800 train / 1,200 validation / 2,000 test. Test data is held out from training and early stopping. A dense 6→32 ReLU→24 ReLU→5 Softmax model uses Adam, up to 120 epochs, and validation-loss early stopping with restored best weights.

The checked-in run achieved 98.15% float accuracy and 98.15% fully int8 accuracy. The exported model has 3,848 bytes. Results apply only to held-out samples of the same synthetic process. Borderline readings, sensor calibration, real occupancy patterns, and distribution shift require independent validation. `models/metrics.json` contains a confusion matrix, classification report, counts, scales, labels, and model checksum; regenerate that file rather than manually editing scores.

## Reproduction (also suitable for Colab)

Install `tinyml/requirements.txt` into a Python 3.12 environment, then run generator → trainer → converter. In Colab, upload/clone the repository, install the same requirements, and run the scripts from the project root; use `%pip` or shell commands as appropriate. TensorFlow CPU is sufficient. Training uses two CPU threads and needs no GPU or paid runtime.

Artifacts: CSV data, Keras model and SavedModel (generated/ignored), `classroom_model.tflite`, `weights.npz`, `metrics.json`, and generated `firmware/include/classroom_model.h`. The converter checks the TFL3 flatbuffer signature and emits a 16-byte-aligned C array.

## Quantization and MCU inference

Representative calibration uses 500 training samples only. TFLite conversion restricts operators to built-in int8 implementations and int8 inputs/outputs. **Per-tensor weight quantization is required:** TensorFlow 2.19's default per-channel dense weights were accepted by desktop TFLite but miscomputed by the pinned Micro dense kernels. The converter explicitly disables per-channel quantization, and firmware rejects incompatible exports. Firmware registers FullyConnected and Softmax, invokes the model every five seconds, and converts the highest output score to a class and confidence. The 24 KiB tensor arena is static; allocation errors disable ML gracefully.

`models/micro_test_vectors.csv` contains the same 2,000 held-out test inputs, ground-truth synthetic labels, and desktop int8 predictions. The host Micro-runtime test executes the actual firmware wrapper and embedded model on these vectors to check both accuracy and agreement with desktop TFLite. It also explicitly tests all five representative classes. This catches conversion/runtime incompatibilities that compiling alone cannot establish.

The dashboard's software simulator uses the very same trained float weights with NumPy, keeping the server lightweight. It is a separate runtime and can disagree with the quantized model near decision boundaries. Do not label a NumPy prediction as execution on the ESP32. `tests/test_model_artifacts.py` evaluates the actual int8 binary on all five representative classes and checks the embedded bytes against the model checksum.

## Fault handling and limitations

Invalid DHT input marks inference unavailable. Missing desktop weights return UNAVAILABLE. Microcontroller allocation/schema/invocation failure also marks inference unavailable; temperature/air emergency thresholds still work. A model-predicted ABNORMAL class can trigger a conservative alarm; false positives are possible. Optional future confidence gating must not weaken rule-based emergency behavior. Classifier inputs outside the synthetic training range are not validated evidence of model reliability.
