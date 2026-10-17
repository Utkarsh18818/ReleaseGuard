"""Stage only application inputs; avoid NTFS cache xattrs and exclude credentials."""
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root / ".local" / "build-context"
target.mkdir(parents=True, exist_ok=True)
files = [root / "pyproject.toml", root / "requirements-lock.txt"]
files.extend(root / "environment" / name for name in ("Dockerfile", "hosted.Dockerfile", "hosted.py"))
files.extend(root / "demo" / name for name in (
    "ReleaseGuard-demo.mp4", "demo-preview.mp4", "demo-poster.jpg", "captions.vtt"
))
for directory in (root / "backend", root / "fixtures"):
    files.extend(p for p in directory.rglob("*") if p.is_file() and
                 (p.suffix in {".py", ".html", ".json", ".css", ".js", ".svg", ".woff2", ".webp"} or p.name == "LICENSE" or p.name.endswith("-LICENSE.txt")))
for source in files:
    destination = target / source.relative_to(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
print("Staged application-only context; no .env, history, caches or outputs included.")
