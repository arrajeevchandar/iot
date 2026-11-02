"""Make a bootable 4 MiB image for Wokwi's custom-firmware upload command."""
import argparse
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument("--environment", choices=["esp32dev", "source-build"], default="esp32dev")
args = p.parse_args()
build = ROOT / ".pio/build" / args.environment
for name in ["bootloader.bin", "partitions.bin", "firmware.bin"]:
    if not (build / name).is_file():
        p.error(f"Build {args.environment} first: missing {name}")
(ROOT / "runtime").mkdir(exist_ok=True)
output = ROOT / f"runtime/classroom-{args.environment}.bin"
subprocess.run([sys.executable, "-m", "esptool", "--chip", "esp32", "merge_bin", "-o", str(output),
                "--flash_mode", "dio", "--flash_freq", "40m", "--flash_size", "4MB",
                "0x1000", str(build / "bootloader.bin"), "0x8000", str(build / "partitions.bin"),
                "0x10000", str(build / "firmware.bin")], check=True)
print(f"Wokwi firmware: {output}")
