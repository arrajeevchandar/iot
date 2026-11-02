"""Train, evaluate, quantize, and export a small dense network. Runs on CPU/Colab."""
import os
os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "2")
os.environ.setdefault("TF_NUM_INTEROP_THREADS", "2")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from generate_dataset import FEATURES, LABELS, ROOT, SCALES


def train(epochs, export_only=False):
    tf.keras.utils.set_random_seed(42)
    data = np.loadtxt(ROOT / "data/classroom_dataset.csv", delimiter=",", skiprows=1)
    data = np.unique(data[np.isfinite(data).all(axis=1)], axis=0)
    x, y = data[:, :6].astype(np.float32) / SCALES, data[:, 6].astype(np.int32)
    train_x, test_x, train_y, test_y = train_test_split(x, y, test_size=.2, random_state=42, stratify=y)
    train_x, val_x, train_y, val_y = train_test_split(train_x, train_y, test_size=.15, random_state=43, stratify=train_y)
    model = tf.keras.Sequential([tf.keras.layers.Input((6,)), tf.keras.layers.Dense(32, activation="relu"),
                                 tf.keras.layers.Dense(24, activation="relu"), tf.keras.layers.Dense(5, activation="softmax")])
    model.compile(optimizer=tf.keras.optimizers.Adam(.003), loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    options = tf.data.Options()
    options.threading.private_threadpool_size = 2
    training = tf.data.Dataset.from_tensor_slices((train_x, train_y)).shuffle(len(train_x), seed=42).batch(64).with_options(options)
    validation = tf.data.Dataset.from_tensor_slices((val_x, val_y)).batch(128).with_options(options)
    out = ROOT / "models"
    out.mkdir(exist_ok=True)
    if export_only:
        model = tf.keras.models.load_model(out / "classroom_model.keras")
    else:
        model.fit(training, validation_data=validation, epochs=epochs, verbose=2,
                  callbacks=[tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=18, restore_best_weights=True)])
    model.save(out / "classroom_model.keras")
    # Export exact trained weights for the lightweight NumPy dashboard simulator.
    np.savez(out / "weights.npz", *model.get_weights())
    model.export(str(out / "saved_model"))
    converter = tf.lite.TFLiteConverter.from_saved_model(str(out / "saved_model"))
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    # The pinned TFLM CMSIS dense kernels require per-tensor weight quantization.
    # TF 2.19 defaults to per-channel dense weights, which desktop Lite accepts
    # but this Micro runtime does not compute correctly.
    converter._experimental_disable_per_channel = True
    converter.representative_dataset = lambda: ([row.reshape(1, 6)] for row in train_x[:500])
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8
    blob = converter.convert()
    (out / "classroom_model.tflite").write_bytes(blob)
    interpreter = tf.lite.Interpreter(model_content=blob, num_threads=1)
    interpreter.allocate_tensors()
    inp, output = interpreter.get_input_details()[0], interpreter.get_output_details()[0]
    scale, zero = inp["quantization"]
    predictions = []
    for row in test_x:
        q = np.clip(np.rint(row / scale + zero), -128, 127).astype(np.int8)
        interpreter.set_tensor(inp["index"], q[None])
        interpreter.invoke()
        predictions.append(int(np.argmax(interpreter.get_tensor(output["index"])[0])))
    report = classification_report(test_y, predictions, target_names=LABELS, output_dict=True, zero_division=0)
    np.savetxt(out / "micro_test_vectors.csv", np.column_stack([test_x*SCALES, test_y, predictions]),
               delimiter=",", header=",".join(FEATURES+["class_label","desktop_class"]), comments="", fmt="%.8f")
    metrics = {"seed":42, "rows":len(data), "train_rows":len(train_x), "validation_rows":len(val_x), "test_rows":len(test_x),
               "float_accuracy":float(accuracy_score(test_y, np.argmax(model(test_x, training=False).numpy(), axis=1))),
               "int8_accuracy":float(accuracy_score(test_y, predictions)), "confusion_matrix":confusion_matrix(test_y, predictions).tolist(),
               "classification_report":report, "tflite_bytes":len(blob), "sha256":hashlib.sha256(blob).hexdigest(),
               "features":FEATURES, "scales":SCALES.tolist(), "labels":LABELS, "weight_quantization":"per-tensor int8",
               "notice":"Held-out synthetic data only; not measured real-world performance."}
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=120)
    p.add_argument("--export-only", action="store_true", help="Reuse the saved Keras model, reconvert and reevaluate")
    args=p.parse_args()
    train(args.epochs, args.export_only)
