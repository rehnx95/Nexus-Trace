# Phase 4 Status

## Completed

- Added lazy spaCy `MODEL_PATH` loading with a visible gazetteer-only fallback.
- Added a gazetteer/ruler NER layer for persons, locations, and organization suffixes.
- Added overlapping-span merge behavior and provenance-bearing `Mention` records.
- Integrated NER entities into the pretrained walking-skeleton extractor.
- Added strict NER-span scoring support to the evaluation harness.
- Added training data preparation and public-text/gazetteer folder guidance.

## Validation

- Phase 4 NER contract tests pass.
- Full Phase 1-4 tests pass; targeted Phase 4 verification passed.
- Leak check passes.
- Gold-dev strict NER span F1: `1.0000`; entity P/R/F1: `1.0000`.
- Synthetic-dev strict NER span F1: `1.0000`; entity P/R/F1: `0.8889`.
- Synthetic-versus-hand-dev NER span gap: `0.0000` F1 in this small rule-only baseline.
- Relations remain `0.0000` F1 and are deferred to Phase 6.
- SpaCy itself is not installed in the Python 3.15 environment because pinned spaCy 3.7.5
  lacks compatible wheels for this runtime.

## Gate Status

The base-model/fine-tuned NER comparison and independent locked-test run remain pending.
The locked test is not populated and has not been opened. No result is claimed as a
Phase 4 target until strict PERSON, LOC, and ORG metrics meet the plan thresholds.
