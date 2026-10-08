# S7.14 — Multi-report parser generalization

Goal: challenge S7.11 stateful parsing and S7.13 team validation across **distinct source PDFs**, rather than optimize only for the March 27 report.

The runner reads local PDFs, hashes and deduplicates them, executes the existing stateful parser and structural validator, writes per-report results, and retains failing documents in the denominator. An empty report is not considered structurally consistent. Review sample is risk-prioritized; it is not human ground truth.

Gate: at least three distinct successfully processed PDFs to advance to **manual ground-truth evaluation**. This never opens the as-of training gate. No historical publication verification occurs. Preserve the original PDFs locally and keep `input_pdfs/` and `results/` out of Git.

Limitations: fixed coordinate lanes may fail on different page geometries; parser/validator share assumptions; an internally consistent report may still be wrong; PDF creation and download times do not prove first publication.
