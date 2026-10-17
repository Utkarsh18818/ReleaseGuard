"""Stage only application inputs; avoid NTFS cache xattrs and exclude credentials."""
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root / ".local" / "build-context"
target.mkdir(parents=True, exist_ok=True)
files = [root / "pyproject.toml", root / "requirements-lock.txt", root / "environment" / "Dockerfile"]
for directory in (root / "backend", root / "fixtures"):
    files.extend(p for p in directory.rglob("*") if p.is_file() and
                 (p.suffix in {".py", ".html", ".json", ".css", ".js", ".svg", ".woff2"} or p.name == "LICENSE"))
for source in files:
    destination = target / source.relative_to(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
print("Staged application-only context; no .env, history, caches or outputs included.")
