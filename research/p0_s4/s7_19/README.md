# S7.19 historical publication evidence audit

Run from repository root:

```powershell
python .\research\p0_s4\s7_19\run_s7_19.py
python -m pytest -q
```

Outputs `results/s7_19_report.json` and `results/s7_19_pdf_evidence.csv`.

This is **not** an independent timestamp-verification mechanism. It checks the existing local PDF files and explicitly blocks training unless independently verifiable historical public-availability evidence is obtained. The filename, internal metadata, and present-day HTTP headers do not prove historical public availability. Do not override this gate based on a document's printed report time.
