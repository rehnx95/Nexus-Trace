# Phase 6 Status

## Completed

- Data-driven relationship rules loaded from YAML.
- Active and passive financial relation direction handling.
- Person-location, person-vehicle, person-phone, person-person, and person-organization rules.
- Negative examples embedded with every relationship rule.
- Table-derived CDR edges retain confidence `1.0` and call counts.
- Financial table transactions are aggregated into `FINANCIAL_TRAIL` account edges.
- Co-occurrence remains excluded from typed relation output.

## Validation

- Phase 6 contract tests cover positive and negative relation extraction.
- Gold dev relation precision/recall/F1 each reached `1.0000`.
- Financial table aggregation is covered by a contract test.
- Full backend tests and leak checks pass.
- Phase 6 locked-test results remain pending as the locked set may not be tuned or opened.

## Gate Status

Phase 6 dev relation metrics must be recorded before this phase is considered complete.
