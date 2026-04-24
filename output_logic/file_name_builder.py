import re
from datetime import date


INPUT_SUFFIX = "\uc785\ub825"


def _sanitize_name(value: str) -> str:
    text = (value or "").strip()
    text = re.sub(r'[<>:"/\\\\|?*]', "_", text)
    text = re.sub(r"\s+", "_", text)
    return text or "result"


def _read_field(source, key: str, default=""):
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _to_int_like(value, default=0) -> int:
    if value in (None, ""):
        return default
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().replace(",", "").replace("_", "")
    if not text:
        return default
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return default


def _birth_suffix(source, today) -> str:
    birth_year = _to_int_like(_read_field(source, "birth_year", 0), 0)
    if birth_year <= 0:
        birth_year = today.year - _to_int_like(_read_field(source, "age", 0), 0)
    return f"{birth_year % 100:02d}"


def _base_filename(source, today=None) -> str:
    today = today or date.today()
    safe_name = _sanitize_name(_read_field(source, "name", ""))
    birth_suffix = _birth_suffix(source, today)
    return f"{safe_name}_{birth_suffix}"


def build_report_filename(profile, today=None, extension=".json") -> str:
    return f"{_base_filename(profile, today=today)}{extension}"


def build_input_filename(source, today=None, extension=".json") -> str:
    return f"{_base_filename(source, today=today)}_{INPUT_SUFFIX}{extension}"


def build_word_report_filename(profile, today=None, extension=".docx") -> str:
    today = today or date.today()
    safe_name = _sanitize_name(_read_field(profile, "name", ""))
    birth_suffix = _birth_suffix(profile, today)
    return f"{birth_suffix}_{safe_name}{extension}"
