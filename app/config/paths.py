from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SETTINGS_DIR = PROJECT_ROOT / "settings"
CONTOURS_DIR = SETTINGS_DIR / "contours"
SERVER_CONFIG_DIR = SETTINGS_DIR / "server"
ENV_LOCAL = PROJECT_ROOT / ".env.local"
ENV_FILE = ENV_LOCAL if ENV_LOCAL.exists() else None
