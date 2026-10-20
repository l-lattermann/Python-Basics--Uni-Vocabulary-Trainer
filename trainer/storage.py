"""Progress file: load, atomic save, backups."""
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

KEEP_BACKUPS = 20


def load(path):
    """Read a progress file; empty progress when it does not exist yet."""
    path = Path(path)
    if not path.exists():
        return {"schema": 1, "session": 0, "cards": {}, "current": None}
    progress = json.loads(path.read_text(encoding="utf-8"))
    if progress.get("schema") != 1:
        raise ValueError(f"{path}: unsupported progress schema {progress.get('schema')!r}")
    return progress


def save(path, progress):
    """Write progress atomically: temp file, fsync, rename over the old one."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as file:
        json.dump(progress, file, indent=1, ensure_ascii=False)
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())
    os.replace(tmp, path)


def backup(path, keep=KEEP_BACKUPS):
    """Copy the progress file to backups/<deck_id>/<timestamp>.json, keeping the newest `keep`."""
    path = Path(path)
    if not path.exists():
        return None
    folder = path.parent / "backups" / path.stem
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{datetime.now():%Y%m%d-%H%M%S-%f}.json"
    shutil.copy2(path, target)
    for old in sorted(folder.glob("*.json"))[:-keep]:
        old.unlink()
    return target
