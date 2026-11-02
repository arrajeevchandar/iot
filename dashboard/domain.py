"""Local classroom simulator. Firmware remains authoritative for real ESP32 nodes."""
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np

LABELS = ["EMPTY", "OCCUPIED_NORMAL", "HIGH_ENERGY_USAGE", "POOR_ENVIRONMENT", "ABNORMAL_CONDITION"]


class Classifier:
    def __init__(self, path=None):
        path = path or Path(__file__).resolve().parents[1] / "tinyml/models/weights.npz"
        self.weights = None
        if Path(path).is_file():
            with np.load(path, allow_pickle=False) as data:
                self.weights = [data[f"arr_{i}"] for i in range(6)]

    def predict(self, sensors, power):
        if self.weights is None:
            return "UNAVAILABLE", 0.0
        x = np.array([sensors[k] for k in ["temperature", "humidity", "light", "air_quality", "occupancy"]] + [power], dtype=np.float32)
        x /= np.array([50, 100, 100, 100, 1, 100], dtype=np.float32)
        for i in (0, 2):
            x = np.maximum(0, x @ self.weights[i] + self.weights[i+1])
        x = x @ self.weights[4] + self.weights[5]
        p = np.exp(x - x.max())
        p /= p.sum()
        return LABELS[int(p.argmax())], float(p.max())


@dataclass
class Controller:
    sensors: dict = field(default_factory=lambda: dict(temperature=24., humidity=50., light=65., air_quality=20., occupancy=False, sensor_valid=True))
    mode: str = "AUTO"
    manual: dict = field(default_factory=lambda: dict(light1=False, light2=False, fan=False, servo=0))
    power: float = 0
    energy: float = 0
    baseline: float = 0
    auto: float = 0
    last: float | None = None
    version: int = 0
    classifier: Classifier = field(default_factory=Classifier)

    def integrate(self, now):
        if self.last is not None:
            hours = max(0, now-self.last)/3600
            self.energy += self.power*hours
            self.baseline += 100*hours
            if self.mode == "AUTO":
                self.auto += self.power*hours
        self.last = now

    def command(self, command, now):
        self.integrate(now)
        self.mode = command["mode"]
        self.manual = {k: command[k] for k in self.manual}
        self.version = command["version"]

    def tick(self, now):
        self.integrate(now)
        s = self.sensors
        a = dict(self.manual) if self.mode == "MANUAL" else dict(
            light1=s["occupancy"] and s["light"] < 40,
            light2=s["occupancy"] and s["light"] < 40,
            fan=s["occupancy"] and s["temperature"] > 28,
            servo=90 if s["air_quality"] >= 60 or s["temperature"] > 32 else 0)
        self.power = 20*a["light1"] + 20*a["light2"] + 60*a["fan"]
        ml, confidence = self.classifier.predict(s, self.power) if s["sensor_valid"] else ("UNAVAILABLE", 0.)
        critical = s["air_quality"] >= 85 or s["temperature"] >= 45 or ml == "ABNORMAL_CONDITION"
        warning = not s["sensor_valid"] or s["air_quality"] >= 60 or s["temperature"] > 32 or s["humidity"] > 75 or ml == "POOR_ENVIRONMENT"
        if self.mode == "AUTO" and ml == "POOR_ENVIRONMENT":
            a["servo"] = max(90, a["servo"])
        if critical or not s["sensor_valid"]:
            a["servo"] = 180
        return dict(s, **a, alarm=critical, source="simulator", mode=self.mode, power_w=self.power,
                    energy_wh=self.energy, auto_wh=self.auto, baseline_wh=self.baseline,
                    ml_class=ml, confidence=confidence, alert="CRITICAL" if critical else "WARNING" if warning else "INFO",
                    applied_version=self.version)
