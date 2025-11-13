import hashlib
import logging
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List

logger = logging.getLogger(__name__)

@dataclass
class WhatsAppProfile:
    number: str
    is_registered: bool
    profile_picture: str
    about: str
    about_last_updated: str
    account_type: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

ABOUT_TEMPLATES = [
    "Living my best life!",
    "Available on WhatsApp only.",
    "Work hard, dream big.",
    "Stay positive, work hard, make it happen.",
    "✨ Hustle in silence. ✨",
    "Just another human on the internet.",
    "Business inquiries only.",
    "Blessed and grateful.",
]

def _validate_number(raw: str) -> str:
    cleaned = raw.strip()
    if not cleaned:
        raise ValueError("Phone number is empty.")
    if not re.fullmatch(r"\d+", cleaned):
        raise ValueError(f"Invalid phone number '{raw}'. Only digits are allowed.")
    if len(cleaned) < 6:
        raise ValueError(f"Phone number '{raw}' is too short to be valid.")
    if len(cleaned) > 20:
        raise ValueError(f"Phone number '{raw}' is too long to be valid.")
    return cleaned

def _hash_number(number: str) -> str:
    return hashlib.sha256(number.encode("utf-8")).hexdigest()

def _deterministic_datetime(hash_hex: str) -> datetime:
    """
    Produce a deterministic datetime in the past based on the hash.
    """
    # Use parts of the hash as integers to build a timedelta
    days_ago = int(hash_hex[0:4], 16) % 365
    hours = int(hash_hex[4:6], 16) % 24
    minutes = int(hash_hex[6:8], 16) % 60

    now = datetime.now(timezone.utc)
    dt = now - timedelta(days=days_ago, hours=hours, minutes=minutes)
    return dt.replace(microsecond=0)

def _deterministic_choice(hash_hex: str, templates: List[str]) -> str:
    idx = int(hash_hex[8:12], 16) % len(templates)
    return templates[idx]

def _build_profile(number: str, media_base_url: str) -> WhatsAppProfile:
    """
    Build a deterministic but realistic-looking profile object from a phone number.

    This implementation does NOT connect to WhatsApp. It uses a hash of the number
    to generate stable pseudo-random fields suitable for testing and demos.
    """
    number_validated = _validate_number(number)
    h = _hash_number(number_validated)

    # Determine registration status: ~2/3 registered
    is_registered = int(h[12:14], 16) % 3 != 0

    # Account type: ~1/5 business
    account_type = "business" if int(h[14:16], 16) % 5 == 0 else "personal"

    # About text and last updated
    about = _deterministic_choice(h, ABOUT_TEMPLATES) if is_registered else ""
    about_dt = _deterministic_datetime(h)
    about_last_updated = about_dt.isoformat().replace("+00:00", "Z")

    # Profile picture URL
    profile_picture = (
        f"{media_base_url.rstrip('/')}/{h[:16]}.jpg" if is_registered else ""
    )

    profile = WhatsAppProfile(
        number=number_validated,
        is_registered=is_registered,
        profile_picture=profile_picture,
        about=about,
        about_last_updated=about_last_updated,
        account_type=account_type,
    )
    return profile

def build_profiles(
    numbers: Iterable[str],
    media_base_url: str = "https://cdn.example.com/whatsapp/avatars",
) -> List[Dict[str, Any]]:
    """
    Build WhatsAppProfile objects for an iterable of phone numbers.

    Invalid numbers are logged and skipped instead of aborting the entire batch.
    """
    profiles: List[Dict[str, Any]] = []
    for raw in numbers:
        try:
            profile = _build_profile(raw, media_base_url=media_base_url)
            profiles.append(profile.to_dict())
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skipping number '%s': %s", raw, exc)
            continue
    return profiles