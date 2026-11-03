import os
from pathlib import Path
from typing import Any


def load_pretrained_model() -> tuple[Any | None, dict]:
    try:
        import spacy
    except ImportError:
        return None, {
            "model_status": "fallback",
            "model_warning": "spaCy is unavailable; gazetteer-only NER is active",
            "model_path": None,
        }

    configured = os.getenv("MODEL_PATH")
    if configured:
        model_path = Path(configured)
        if not model_path.exists():
            return None, {
                "model_status": "fallback",
                "model_warning": (
                    f"MODEL_PATH does not exist: {configured}; using gazetteer-only NER"
                ),
                "model_path": configured,
            }

    model_name = configured or os.getenv("SPACY_MODEL", "en_core_web_sm")
    try:
        model = spacy.load(str(model_name))
    except (OSError, ImportError) as exc:
        return None, {
            "model_status": "fallback",
            "model_warning": f"Unable to load {model_name}; gazetteer-only NER is active: {exc}",
            "model_path": configured,
        }

    return model, {
        "model_status": "loaded",
        "model_warning": None,
        "model_path": str(model_name),
    }
