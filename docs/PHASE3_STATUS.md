# Phase 3 Status

## Completed

- Added normalized phone, plate, account, UPI, amount, date, and Indian-name helpers.
- Added column alias mapping and format detection for CSV, TSV, semicolon CSV, and financial tables.
- Added validated financial transaction parsing with rejected rows and duplicate-account protection.
- Added `BankAccount` to the graph entity registry.
- Integrated account extraction and financial transaction diagnostics into `PretrainedFirstExtractor`.
- Added deterministic unit coverage for normalization, names, accounts, and financial tables.

## Validation

- Backend tests: `10 passed`
- Ruff: passed
- Leak check: passed
- Financial parser: one valid row retained and two invalid rows rejected in the contract test.
- Existing CDR and phone/plate walking-skeleton tests remain green.

## Locked Gate

The locked test has not been opened. Phase 3 exits only when independent identifiers and
financial data meet the target thresholds on both dev and locked sets.
