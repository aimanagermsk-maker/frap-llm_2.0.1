from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_LOCAL = PROJECT_ROOT / ".env.local"
ENV_FILE = ENV_LOCAL if ENV_LOCAL.exists() else None
