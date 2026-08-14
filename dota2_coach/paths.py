from pathlib import Path
import os


def resolve_data_dir(override: str | None = None) -> Path:
    raw = override or os.environ.get("DOTA2_COACH_DATA")
    if raw:
        path = Path(raw).expanduser()
    elif os.name == "nt":
        path = Path(os.environ.get("APPDATA", Path.home())) / "Dota2Coach"
    else:
        path = Path.home() / ".local/share/dota2-coach"
    path.mkdir(parents=True, exist_ok=True)
    return path
