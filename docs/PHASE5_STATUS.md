# Phase 5 Status

## Completed

- Blocking by phonetic key, first-token prefix, and surname
- Name normalization for Indian aliases, casing, honorifics, and punctuation
- Lightweight phonetic key generation without runtime dependencies
- Auto-review separation based on score thresholds and identifier constraints
- Explicit alias extraction for alias, urf, aka, and "also known as" markers
- Thread-safe in-memory merge review queue with API endpoints
- Cached cross-case resolution scaffold
- Ingestion diagnostics for clusters, candidate decisions, and explicit aliases
- Canonical cluster labels for auto-merged and explicitly aliased names
- Persistent resolution decisions under `datasets/feedback/resolution-decisions.jsonl`
- Dev resolution metrics recorded in `eval/runs/phase5-dev.json`

## Validation

- Phase 5 resolution contract tests pass.
- Identifier conflicts remain separate.
- Shared identifiers enter review instead of auto-merging.
- Review decisions are never feedback-trained or auto-applied.
- Synthetic/dev resolution pairs: 8 pairs, 5 true same-entity pairs.
- False-auto-merge rate: `0.0000` (0 false merges / 2 auto-merges).
- Auto-plus-review same-entity recall: `1.0000`, meeting the planned 85% target.

## Gate Status

The locked resolution test has not been opened. False-merge and same-entity recovery
numbers remain unmeasured until the independently authored locked set is available.
