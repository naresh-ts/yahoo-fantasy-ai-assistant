"""Private local storage for Yahoo OAuth refresh tokens."""

import os
import tempfile
from pathlib import Path

def _token_file() -> Path:
    """Resolve private token path at call time for managed persistent disks."""
    override = os.environ.get("YAHOO_TOKEN_DIR")
    directory = (
        Path(override).expanduser()
        if override
        else Path.home() / ".local" / "share" / "yahoo-fantasy-ai-assistant"
    )
    return directory / "refresh_token"


def save_refresh_token(token: str) -> None:
    """Atomically save a refresh token with restricted permissions."""
    if not token:
        raise ValueError("Cannot save an empty refresh token")

    token_file = _token_file()
    token_directory = token_file.parent
    token_directory.mkdir(parents=True, exist_ok=True)
    os.chmod(token_directory, 0o700)

    fd, temporary_path = tempfile.mkstemp(
        prefix=".refresh_token-",
        dir=token_directory,
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(token)
            file.flush()
            os.fsync(file.fileno())

        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, token_file)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)


def load_refresh_token() -> str | None:
    """Load the stored refresh token, if present."""
    token_file = _token_file()
    if not token_file.exists():
        return None

    if token_file.is_symlink():
        raise PermissionError("Refusing to read a symlinked refresh token file")
    if token_file.stat().st_mode & 0o077:
        raise PermissionError("Refresh token file permissions are too broad")

    return token_file.read_text(encoding="utf-8").strip() or None
