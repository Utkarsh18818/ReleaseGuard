"""Idempotent local infrastructure credentials; never print their values."""
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / ".local" / ".env"
path.parent.mkdir(parents=True, exist_ok=True)
content = path.read_text(encoding="utf-8-sig") if path.exists() else ""
keys = {line.split("=", 1)[0].strip() for line in content.splitlines() if "=" in line}
for name in ("FALKORDB_PASSWORD", "QUEUE_PASSWORD"):
    if name not in keys:
        content = content.rstrip() + "\n" + name + "=" + secrets.token_hex(24) + "\n"
path.write_text(content, encoding="utf-8")
print("Local infrastructure credentials ready; values withheld.")
