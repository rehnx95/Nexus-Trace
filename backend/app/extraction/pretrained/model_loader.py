import os
from pathlib import Path
from typing import Any
import json


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
    if configured:
        report_path = model_path / "training_report.json"
        if report_path.exists():
            try:
                report = json.loads(report_path.read_text(encoding="utf-8"))
                entity_f1 = float(report.get("scores", {}).get("ents_f", 0.0))
                minimum_f1 = float(os.getenv("NER_MINIMUM_F1", "0.75"))
                if entity_f1 < minimum_f1:
                    return None, {
                        "model_status": "rejected",
                        "model_warning": (
                            f"Fine-tuned model rejected: entity F1 {entity_f1:.4f} "
                            f"is below minimum {minimum_f1:.4f}"
                        ),
                        "model_path": configured,
                        "entity_f1": entity_f1,
                    }
            except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
                return None, {
                    "model_status": "rejected",
                    "model_warning": f"Invalid fine-tuning report; model rejected: {exc}",
                    "model_path": configured,
                }
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
