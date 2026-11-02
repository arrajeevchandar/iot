"""Generate application tokens locally. Values are never printed or overwritten."""
import os
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
path = root / ".env"
try:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    print("Existing .env preserved.")
else:
    with os.fdopen(descriptor, "w") as output:
        output.write("# Private credentials for optional public deployment. Never commit this file.\n")
        output.write(f"DASHBOARD_TOKEN={secrets.token_urlsafe(32)}\nDEVICE_TOKEN={secrets.token_urlsafe(32)}\n")
        output.write("PUBLIC_DEPLOYMENT=1\nSIMULATOR_ENABLED=1\n")
    print("Created private .env with distinct random dashboard/device tokens; values not displayed.")
