"""Small reusable helpers shared by project scripts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .config import TIMEZONE_NAME


BOT_TOKEN = "DSC2107-UCU-Group-2"


def build_user_agent(contact_email: str) -> str:
    """Build the descriptive user agent required by Jumia's robots file."""

    clean_email = contact_email.strip()
    if "@" not in clean_email or " " in clean_email:
        raise ValueError("A valid contact email must be supplied at runtime.")
    return f"{BOT_TOKEN}/1.0 (academic research; contact: {clean_email})"


def nairobi_now() -> datetime:
    """Return the genuine current time in the assignment timezone."""

    return datetime.now(ZoneInfo(TIMEZONE_NAME))


def sha256_file(path: Path) -> str:
    """Calculate a SHA-256 checksum without changing the file."""

    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    """Write readable UTF-8 JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def safe_filename(value: str) -> str:
    """Convert a label into a predictable lowercase filename component."""

    return "_".join(value.lower().replace("&", "and").split())

