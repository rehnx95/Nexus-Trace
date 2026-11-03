# Evaluation

Purpose: offline evaluation harness and result history.

Key files: `harness.py` and `runs/`.

The locked test is never passed to the harness unless an explicit phase gate records
the commit hash, configuration, and timestamp.

Run an extraction-mode comparison with:

```powershell
python eval/harness.py --dev datasets/gold/dev --output eval/runs --phase 9 --mode pretrained_only
```
