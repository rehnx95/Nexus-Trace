import os
import json
from functools import lru_cache
from pathlib import Path

EXTRACTION_MODE = os.getenv(
    "EXTRACTION_MODE",
    "pretrained_only",
).strip().lower()
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "")

DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"


def config_dir() -> Path:
    configured = os.getenv("NEXUS_CONFIG_DIR")
    return Path(configured) if configured else DEFAULT_CONFIG_DIR


@lru_cache(maxsize=1)
def load_config(name: str) -> dict:
    path = config_dir() / f"{name}.json"
    if not path.exists():
        raise RuntimeError(f"Missing NexusTrace configuration: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid NexusTrace configuration JSON in {path}: {exc}"
        ) from exc


def pipeline_config() -> dict:
    return load_config("pipeline")


def ontology_config() -> dict:
    return load_config("ontology")


def thresholds_config() -> dict:
    return load_config("thresholds")
