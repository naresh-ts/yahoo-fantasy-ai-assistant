"""Private local storage for Yahoo OAuth refresh tokens."""

import os
import tempfile
from pathlib import Path

TOKEN_DIRECTORY = (
    Path.home() / ".local" / "share" / "yahoo-fantasy-ai-assistant"
)
TOKEN_FILE = TOKEN_DIRECTORY / "refresh_token"


def save_refresh_token(token: str) -> None:
    """Atomically save a refresh token with restricted permissions."""
    if not token:
        raise ValueError("Cannot save an empty refresh token")

    TOKEN_DIRECTORY.mkdir(parents=True, exist_ok=True)
    os.chmod(TOKEN_DIRECTORY, 0o700)

    fd, temporary_path = tempfile.mkstemp(
        prefix=".refresh_token-",
        dir=TOKEN_DIRECTORY,
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(token)
            file.flush()
            os.fsync(file.fileno())

        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, TOKEN_FILE)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)


def load_refresh_token() -> str | None:
    """Load the stored refresh token, if present."""
    if not TOKEN_FILE.exists():
        return None

    if TOKEN_FILE.stat().st_mode & 0o077:
        raise PermissionError("Refresh token file permissions are too broad")

    return TOKEN_FILE.read_text(encoding="utf-8").strip() or None
