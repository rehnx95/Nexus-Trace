import json
import re
from pathlib import Path

DEFAULT_RULES_PATH = (
    Path(__file__).resolve().parents[5] / "datasets" / "rules" / "relationships.yaml"
)


def load_relation_rules(path: Path | str | None = None) -> list[dict]:
    rules_path = Path(path) if path else DEFAULT_RULES_PATH
    if not rules_path.exists():
        return []
    rules = []
    current = None
    current_list = None
    for raw_line in rules_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if line == "rules:":
            continue
        if line.startswith("  - id: "):
            current = {"id": line.split(": ", 1)[1].strip()}
            rules.append(current)
            current_list = None
            continue
        if current is None or not line.startswith("    "):
            continue
        stripped = line.strip()
        if stripped.startswith("- ") and current_list in {
            "patterns",
            "positive",
            "negative",
            "allowed_types",
        }:
            value = stripped[2:].strip()
            if value.startswith('"') or value.startswith("'"):
                if value.startswith('"'):
                    value = json.loads(value)
                else:
                    value = value.strip("'")
            elif current_list == "allowed_types":
                value = json.loads(value)
            current[current_list].append(value)
            continue
        if stripped in {"patterns:", "positive:", "negative:"}:
            key = stripped[:-1]
            current[key] = []
            current_list = key
            continue
        if ": " not in stripped:
            continue
        key, value = stripped.split(": ", 1)
        value = value.strip()
        if key in {"allowed_types"}:
            current[key] = json.loads(value)
            current_list = None
        elif key in {"patterns", "positive", "negative"}:
            current[key] = []
            current_list = key
        elif key == "confidence":
            current[key] = float(value)
        else:
            current[key] = value.strip('"').strip("'")
            current_list = None
    for rule in rules:
        rule["_patterns"] = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in rule.get("patterns", [])
        ]
    return rules
