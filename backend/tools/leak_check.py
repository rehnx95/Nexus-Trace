import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED_DIRECTORIES = [ROOT / "seed data", ROOT / "datasets" / "gold" / "locked_test"]
SCAN_ROOTS = [
    ROOT / "backend" / "app",
    ROOT / "backend" / "services",
    ROOT / "datasets" / "synthetic",
    ROOT / "datasets" / "gold" / "dev",
]
EXTENSIONS = {".py", ".jsonl", ".json", ".csv", ".txt", ".yaml", ".yml"}

PHONE_RE = re.compile(r"(?<!\d)(?:\+91[\s-]?|91[\s-]?|0)?[6-9]\d{9}(?!\d)")
PLATE_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z]{1,3}\d{1,4}\b")


def protected_tokens() -> list[str]:
    tokens = set()
    for directory in SEED_DIRECTORIES:
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix.lower() in EXTENSIONS:
                text = path.read_text(encoding="utf-8", errors="ignore")
                tokens.update(match.group(0) for match in PHONE_RE.finditer(text))
                tokens.update(match.group(0) for match in PLATE_RE.finditer(text.upper()))
    return sorted(tokens)


def main() -> int:
    protected = protected_tokens()
    violations = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").upper()
            for token in protected:
                if token.upper().replace(" ", "") in text.replace(" ", ""):
                    violations.append((path.relative_to(ROOT), token))

    if violations:
        for path, token in violations:
            print(f"LEAK {path}: {token}")
        return 1
    print("Leak check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
