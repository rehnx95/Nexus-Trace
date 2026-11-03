# Annotation Guide

## Entity spans

- Annotate the exact source text, character start offset, end offset, type, and canonical ID.
- Use `Person`, `Location`, `Organization`, `Vehicle`, and `Phone`.
- Do not annotate pronouns unless a resolution step creates an explicit alias decision.
- Remove honorifics from canonical person names only after preserving the full source mention.
- Never annotate Aadhaar or PAN identifiers.

## Relations

- Record only an explicit directional relationship stated by the sentence.
- Use canonical source and target IDs plus relationship type.
- Attach the evidence sentence and character offsets where available.
- A sentence containing multiple entities without an explicit relationship is a negative.
- Co-occurrence alone must not produce a typed edge.

## Coordinates and files

- Every JSONL record has one report `id`, source text, entities, relations, and split metadata.
- Character offsets are Python-style `[start, end)` offsets.
- The `locked_test` split is read-only except during a documented phase gate.
