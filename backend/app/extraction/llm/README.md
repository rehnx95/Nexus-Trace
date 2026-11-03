# llm

Purpose: provider-agnostic, contract-compatible optional LLM extraction for Phase 9.

Key files:
- provider.py: OpenAI-compatible HTTP provider
- prompts.py: JSON-only extraction prompt
- parser.py: fenced or plain JSON parsing
- grounding.py: source-text and graph-registry validation
- extractor.py: LLM extraction plus pretrained fallback

Configure `EXTRACTION_MODE=llm_fallback`, `LLM_MODEL`, and optionally
`LLM_BASE_URL` and `LLM_API_KEY`. Use `llm_only` for no fallback.
