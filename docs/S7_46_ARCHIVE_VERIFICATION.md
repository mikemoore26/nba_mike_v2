# S7.46 — Independent Historical Archive Discovery

## Purpose
Query Wayback CDX for exact historical captures of nine NBA article URLs from S7.45, preserve capture metadata, and optionally retrieve hash-addressed archived HTML. No inference of historical publication from live article metadata.

## Evidence hierarchy
1. A CDX entry is an **archive-index candidate**, not proof of a specific article claim.
2. A replay saved with SHA-256 is content for manual claim inspection, not an automatically verified historical transaction.
3. A player name in HTML is not proof of direction, origin, destination, or transaction date.
4. Archive capture timestamps are reported by the archive and should be checked against the original URL and content; even a valid capture only establishes availability by capture time.
5. No promotion to roster chronology, as-of training, or independent reporting without separate audit.

## Safety
No model training; no mutation of earlier evidence. CDX requests are sequential and throttled. Failures are retained as unresolved, not silently treated as no evidence. Exact URL path/host matching is required. `--offline` tests plumbing without accessing the network.
