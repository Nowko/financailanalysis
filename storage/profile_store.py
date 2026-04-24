import json
from pathlib import Path


def save_profile(path: Path, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_profile(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
