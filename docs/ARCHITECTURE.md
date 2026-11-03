# Architecture

NexusTrace uses a contract-first extraction pipeline:

1. Text and tabular documents enter the ingestion API.
2. `PretrainedFirstExtractor` applies deterministic identifiers, gazetteers, NER, and relation rules.
3. Optional LLM extraction produces the same entity and edge contracts.
4. `ExtractionModeExtractor` enforces the selected extraction mode.
5. Phone, vehicle, and bank-account identifiers remain deterministic and authoritative.
6. Resolution merges and clusters person names before review.
7. The graph writer validates registry types and persists approved graph state.
8. Coverage, provenance, diagnostics, and review decisions remain attached to results.

Extraction modes:

- `pretrained_only`: deterministic-first and pretrained NER/relations only.
- `llm_with_fallback`: LLM first, deterministic identifiers authoritative, pretrained fallback on failure.
- `ensemble`: combines both modes, records disagreement, and marks disputed edges for review.
- `llm_only`: optional LLM output for testing; requires grounding and registry validation.

## Deployment topology

Docker Compose runs four persistent/runtime services:

1. Neo4j stores the graph and runs health checks on port `7687`.
2. The FastAPI backend exposes ingestion, extraction, review, and graph APIs on port `8000`.
3. The React/Vite frontend is built into static assets and served by Nginx on port `3000`.
4. Named Docker volumes persist uploaded documents, resolved data, and Neo4j storage.

Production Nginx applies security headers, while the backend restricts allowed origins,
methods, and headers through environment configuration.
