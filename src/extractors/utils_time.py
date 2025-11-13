from datetime import datetime, timezone
from typing import Optional

def current_utc_iso() -> str:
    """
    Return the current UTC time as an ISO-8601 string with 'Z' suffix.
    """
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def parse_iso_datetime(value: str) -> Optional[datetime]:
    """
    Parse an ISO-8601 datetime string into a timezone-aware datetime.
    Returns None if parsing fails.
    """
    try:
        # Python 3.11+ has fromisoformat that understands 'Z' when replaced
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:  # noqa: BLE001
        return None