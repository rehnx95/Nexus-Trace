# Phase 9 Status

## Completed

- Added a provider-neutral OpenAI-compatible HTTP LLM adapter.
- Added JSON-only extraction prompts and parser support.
- Added exact source-span grounding for entities and graph-registry validation for edges.
- Added pretrained fallback for invalid JSON, provider errors, or ungrounded output.
- Added extraction-mode configuration and API reporting.
- Added contract tests for grounded extraction, hallucination rejection, and edge validation.

## Configuration

- `EXTRACTION_MODE=pretrained_only`: pretrained-first default.
- `EXTRACTION_MODE=llm_with_fallback`: use LLM output when grounded; otherwise fall back.
- `EXTRACTION_MODE=ensemble`: combine pretrained and LLM output and record disagreements.
- `EXTRACTION_MODE=llm_only`: use LLM output without provider-error fallback.
- `LLM_MODEL`: required for an LLM request.
- `LLM_BASE_URL`: OpenAI-compatible base URL.
- `LLM_API_KEY`: optional bearer API key.

## Gate Status

- Phase 9 contract suite passes.
- Full backend and repository leak checks pass.
- Mixed-document fallback behavior is covered by contract tests.
- Evaluation harness supports `--mode pretrained|llm|llm_fallback|llm_only`.
- Exact `pretrained_only`, `llm_with_fallback`, `ensemble`, and `llm_only` modes are supported.
- Gold-dev extraction metrics are recorded at `eval/runs/phase9-dev.json`.
