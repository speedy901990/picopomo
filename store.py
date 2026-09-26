# Tiny JSON persistence with atomic writes (write temp file, then rename),
# so a power cut mid-save never leaves a half-written file behind.
import gc
import json
import os

SETTINGS_FILE = "settings.json"
STATS_FILE = "stats.json"


def load(path, default=None):
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = default
    gc.collect()
    return data


def save(path, obj):
    tmp = path + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(obj, f)
        try:
            os.rename(tmp, path)
        except OSError:
            # Some filesystems refuse to rename over an existing file.
            try:
                os.remove(path)
            except OSError:
                pass
            os.rename(tmp, path)
    except OSError as e:
        print("save failed:", path, e)
    gc.collect()


def load_settings(defaults):
    s = dict(defaults)
    saved = load(SETTINGS_FILE, {})
    if isinstance(saved, dict):
        for k in s:
            if k in saved and isinstance(saved[k], int):
                s[k] = saved[k]
    return s
