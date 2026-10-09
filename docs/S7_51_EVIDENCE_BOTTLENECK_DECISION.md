# S7.51 — Evidence Bottleneck and Stop/Go Decision

## Objective
Stop repetitive historical archive extraction when it is no longer producing independently verified as-of transaction chronology. Preserve all S7.50 evidence without weakening training gates.

## Scope and controls
- **Input:** existing S7.50 review CSV only; no network requests.
- **Audit units:** review rows, canonical article URLs, and distinct upstream SHA-256 identifiers are counted separately.
- **Bottlenecks:** mapping gap; missing/unverified capture; direction candidate still unverified; mere co-occurrence; player not recovered; other extraction failure.
- **Outputs:** review, article inventory, machine-readable decision report.
- **Integrity:** S7.51 relies on upstream SHA status and does not independently rehash the HTML. It cannot attest archive timestamp authenticity.
- **Safety:** no roster promotion, chronology promotion, or as-of model training.

## Decision rule
Pause repeated extraction on the same archived HTML. Reopen historical transaction chronology only upon new independently timestamped transaction/roster evidence, or a specific reproducible mapping fix that changes evidence quality. In parallel, independently validated components (e.g., baseline stat distributions or data-quality infrastructure) may proceed **without** the blocked historical roster/transaction inputs. Do not assert any such component is already validated without tests.

## Interpretation
Counts reflect the provided S7.50 review population, not the entire NBA season. Multiple players from one article are not independent sources. An archive index time, replay page, metadata field, or URL slug cannot by itself prove historical availability. Historical cutoff suitability must be established per prediction time and source.
