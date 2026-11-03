# Phase 2 Status

## Completed

- Annotation and negative-example guidance was added.
- The synthetic generator creates deterministic family/name split data.
- Gold dev JSONL and locked-test placeholders were added.
- The offline evaluation harness now reports entity and relation precision, recall, and F1.
- The leak checker scans source and synthetic paths against identifiers found in locked/seed areas.

## Not Yet Complete

- Locked tests must be authored independently before the first Phase 3 gate.
- Synthetic/hand-dev gap should be recorded after reproducible hand and synthetic runs.
- SpaCy and pretrained-name resolution remain future extraction work.

## Baseline Results

- Gold dev entity metrics: precision `1.0000`, recall `0.4167`, F1 `0.5882`.
- Gold dev relation metrics: precision/recall/F1 `0.0000`.
- Synthetic dev entity metrics: precision/recall/F1 `0.0000`.
- Synthetic dev relation metrics: precision/recall/F1 `0.0000`.
- The synthetic dev includes 16 records and 32 expected entities; the hand-shaped gold dev includes 6 records and 12 expected entities.
- `spaCy` could not be installed in the Python 3.15 virtual environment because pinned 3.7.5 dependencies do not provide compatible wheels; the legacy loader was made lazy so it does not prevent baseline imports or empty-ingestion tests.
