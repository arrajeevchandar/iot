import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_diagram_pin_mapping_and_supplies():
    d=json.loads((ROOT/"wokwi/diagram.json").read_text())
    ids=[p["id"] for p in d["parts"]]
    assert len(ids)==len(set(ids))
    edges={frozenset(c[:2]) for c in d["connections"]}
    for part,pin in [("dht:SDA","D15"),("pir:OUT","D13"),("ldr:AO","D34"),("air:SIG","D35"),
                     ("r1:1","D18"),("r2:1","D19"),("r3:1","D21"),("vent:PWM","D23"),("buzzer:2","D25")]:
        assert frozenset([part,"esp:"+pin]) in edges
    for part in ["dht","ldr","air"]:
        assert frozenset([part+":VCC","esp:3V3"]) in edges
    for connection in d["connections"]:
        for endpoint in connection[:2]:
            assert endpoint.split(":")[0] in ids+["$serialMonitor"]


def test_export_has_model_and_no_private_settings():
    sketch=(ROOT/"wokwi/sketch.ino").read_text()
    assert "interpreter->Invoke()" in sketch
    assert "void loop()" in sketch and "void setup()" in sketch
    assert '#include "config.h"' not in sketch
    assert (ROOT/"wokwi/secrets.example.h").read_text()==(ROOT/"firmware/include/secrets.example.h").read_text()
