import hashlib
import json
from pathlib import Path
import re
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]


def test_embedded_binary_matches_metrics():
    blob=(ROOT/"tinyml/models/classroom_model.tflite").read_bytes()
    text=(ROOT/"firmware/include/classroom_model.h").read_text()
    embedded=bytes(int(v,16) for v in re.findall(r"0x([0-9a-f]{2})",text))
    metrics=json.loads((ROOT/"tinyml/models/metrics.json").read_text())
    assert blob==embedded and blob[4:8]==b"TFL3"
    assert hashlib.sha256(blob).hexdigest()==metrics["sha256"]


def test_int8_binary_five_classes():
    tf=pytest.importorskip("tensorflow")
    interpreter=tf.lite.Interpreter(model_path=str(ROOT/"tinyml/models/classroom_model.tflite"),num_threads=1)
    interpreter.allocate_tensors()
    inp,out=interpreter.get_input_details()[0],interpreter.get_output_details()[0]
    assert inp["dtype"]==np.int8 and out["dtype"]==np.int8
    assert all(len(t["quantization_parameters"]["scales"])<=1 for t in interpreter.get_tensor_details()), "Pinned Micro kernels require per-tensor quantization"
    samples=[[24,50,50,20,0,0],[24,50,50,20,1,0],[24,50,80,20,0,100],[35,50,50,70,1,60],[48,50,50,95,1,60]]
    scale,zero=inp["quantization"]
    for expected,sample in enumerate(samples):
        x=np.array(sample,dtype=np.float32)/np.array([50,100,100,100,1,100],dtype=np.float32)
        interpreter.set_tensor(inp["index"],np.clip(np.rint(x/scale+zero),-128,127).astype(np.int8)[None])
        interpreter.invoke()
        assert int(np.argmax(interpreter.get_tensor(out["index"])[0]))==expected
