"""Package project sources/artifacts, excluding Git-ignored credentials, caches and runtime data."""
from pathlib import Path
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
paths=subprocess.check_output(["git","ls-files","-z","--cached","--others","--exclude-standard"],cwd=ROOT).split(b"\0")
output=ROOT/"runtime/smart-classroom-project.zip"
output.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED) as archive:
    for raw in sorted(set(paths)):
        if not raw:
            continue
        path=ROOT/raw.decode()
        if not path.is_file() or path.is_symlink():
            continue
        # Defense in depth: even accidentally tracked secrets are never packaged.
        if path.name in {".env","secrets.h"} or any(p in {".git",".venv","node_modules","runtime",".pio"} for p in path.relative_to(ROOT).parts):
            continue
        archive.write(path,Path("smart-classroom")/path.relative_to(ROOT))
print(f"Packaged project without private settings: {output}")
