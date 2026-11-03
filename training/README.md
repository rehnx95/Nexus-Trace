# Offline NER Training

Purpose: prepare and train versioned spaCy NER artifacts.

Key files: this README and future configs/data scripts.

Training data must exclude seed cases and locked-test names. Run model comparison against
the dev and public-text rehearsal sets. A `MODEL_PATH` artifact must remain optional and
must fall back visibly to the base model when unavailable.
