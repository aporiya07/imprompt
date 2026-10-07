from functools import lru_cache
from pathlib import Path

_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "prompts"


@lru_cache(maxsize=None)
def load_template(name: str) -> str:
    path = _TEMPLATES_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")
