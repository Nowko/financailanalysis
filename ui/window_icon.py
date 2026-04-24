from pathlib import Path
from typing import Iterable, Optional


ICON_CANDIDATES = (
    Path(__file__).resolve().parents[1] / "Financial-analisys.ico",
    Path(__file__).resolve().parents[1] / "assets" / "Financial-analisys.ico",
    Path(r"Z:\NetBackup\File_move\Financial-analisys.ico"),
)

APP_USER_MODEL_ID = "financialplanning.household.analysis"


def resolve_icon_path(candidates: Optional[Iterable[Path]] = None) -> Optional[Path]:
    for candidate in candidates or ICON_CANDIDATES:
        path = Path(candidate)
        if path.exists():
            return path
    return None


def apply_window_icon(root, candidates: Optional[Iterable[Path]] = None) -> Optional[Path]:
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        pass

    icon_path = resolve_icon_path(candidates)
    if icon_path is None:
        return None

    try:
        root.iconbitmap(default=str(icon_path))
    except Exception:
        try:
            root.wm_iconbitmap(str(icon_path))
        except Exception:
            return None
    return icon_path
