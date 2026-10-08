# S7.29 — NBA player directory identity candidates

Run `python research/p0_s4/s7_29/run_s7_29.py` from the project root after S7.28. Live NBA Stats CommonAllPlayers requests can fail; failures are not interpreted as zero players. Optional offline mode: `--directory-json path/to/original.json`. Original directory response is saved under `results/objects/<sha>.json`. Exact normalized names only; ambiguous identities stay unresolved. Output is research-only, with no S7.26 or S7.23 auto-export. Do not commit generated snapshots or results without a separate governance decision.
