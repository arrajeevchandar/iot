"""Linux x86-64 fallback: build with official GitHub releases when PIO registry is unavailable.

Compiler/framework archives are verified against Espressif's published SHA-256.
Local package manifests adapt upstream layouts; no verification is disabled.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT.parent / "esp32-build"
CORE = ROOT.parent / ".platformio"
os.environ["PLATFORMIO_CORE_DIR"] = str(CORE)
os.environ["PLATFORMIO_SETTING_ENABLE_TELEMETRY"] = "no"


def run(*args):
    subprocess.run(args, check=True, cwd=ROOT)


def manifest(path, name, version):
    path.mkdir(parents=True, exist_ok=True)
    (path / "package.json").write_text(json.dumps({"name": name, "version": version, "description": "Local adapter for verified upstream source distribution"}))


def archive(name, url, digest):
    path = Path("/tmp") / name
    if not path.exists():
        run("curl", "-fL", "--retry", "2", url, "-o", str(path))
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise RuntimeError(f"Checksum mismatch: {path}; refusing to use archive")
    return path


def clone(name, url, ref):
    path = BUILD / name
    if not path.exists():
        run("git", "clone", "--depth", "1", "--branch", ref, url, str(path))
    return path


def main():
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise RuntimeError("This source-build fallback supports Linux x86-64. Use PlatformIO normally elsewhere.")
    BUILD.mkdir(exist_ok=True)
    framework_zip = archive("esp32-2.0.17.zip", "https://github.com/espressif/arduino-esp32/releases/download/2.0.17/esp32-2.0.17.zip", "1f8658d4b18a8001ce782142ad08164af2991d70b83a147c3437a6ee30a9b225")
    compiler_tar = archive("xtensa-esp32.tar.gz", "https://github.com/espressif/crosstool-NG/releases/download/esp-2021r2-patch5/xtensa-esp32-elf-gcc8_4_0-esp-2021r2-patch5-linux-amd64.tar.gz", "8ef14e0409c2011b41e504a30f70d3e35287313a795d1f2462ad2cd0e2052d37")
    framework = BUILD / "esp32-2.0.17"
    if not framework.exists():
        with zipfile.ZipFile(framework_zip) as z:
            z.extractall(BUILD)
    compiler = BUILD / "xtensa-esp32-elf"
    if not compiler.exists():
        with tarfile.open(compiler_tar) as t:
            t.extractall(BUILD, filter="data")
    manifest(compiler, "toolchain-xtensa-esp32", "8.4.0+2021r2-patch5")
    run(sys.executable, "-m", "pip", "install", "scons==4.8.1", "esptool==4.5.1")
    scons = BUILD / "scons"
    manifest(scons, "tool-scons", "4.40801.0")
    (scons / "scons.py").write_text("import SCons.Script\nSCons.Script.main()\n")
    esptool = BUILD / "esptool"
    manifest(esptool, "tool-esptoolpy", "1.40501.0")
    (esptool / "esptool.py").write_text("# Avoid shadowing the installed esptool package.\nimport sys\nsys.path.pop(0)\nimport esptool\nesptool._main()\n")
    from platformio.package.manager.tool import ToolPackageManager
    from platformio.package.meta import PackageSpec
    manager = ToolPackageManager()
    manager.install(PackageSpec(owner="platformio", name="tool-scons", uri="file://"+str(scons)))
    platform_path = clone("platform", "https://github.com/platformio/platform-espressif32.git", "v6.10.0")
    libs = [clone("DHT", "https://github.com/adafruit/DHT-sensor-library.git", "1.4.6"),
            clone("Unified", "https://github.com/adafruit/Adafruit_Sensor.git", "1.1.15"),
            clone("Servo", "https://github.com/madhephaestus/ESP32Servo.git", "1.1.2"),
            clone("Json", "https://github.com/bblanchon/ArduinoJson.git", "v7.4.1")]
    ml = BUILD / "Chirale"
    if not ml.exists():
        run("git", "clone", "https://github.com/spaziochirale/Chirale_TensorFlowLite.git", str(ml))
        run("git", "-C", str(ml), "checkout", "46da2f989205a9216229d38cd3d1c657d79d6781")
    libs.append(ml)
    # Inherit the checked-in board and flags, replacing only dependency locations.
    cfg = "[platformio]\nextra_configs = platformio.ini\n\n[env:source-build]\nextends = env:esp32dev\n"
    cfg += "platform = file://"+str(platform_path)+"\nplatform_packages =\n"
    for name, path in [("toolchain-xtensa-esp32",compiler),("framework-arduinoespressif32",framework),("tool-esptoolpy",esptool)]:
        cfg += f"  {name} @ file://{path}\n"
    cfg += "lib_deps =\n"+"".join("  file://"+str(p)+"\n" for p in libs)
    config_path = ROOT / ".pio/source-build.ini"
    config_path.parent.mkdir(exist_ok=True)
    config_path.write_text(cfg)
    run(str(ROOT / ".venv/bin/pio"), "run", "-c", str(config_path), "-e", "source-build", "-j", "4")


if __name__ == "__main__":
    main()
