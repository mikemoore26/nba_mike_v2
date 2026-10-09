# S7.36 — Rejected URL classification

## Problem
S7.35 verified 12 RSS snapshots with 114 links; all were excluded by the strict NBA `/news/` URL filter. We must determine whether links are external, official NBA pages outside the path rule, subdomains, or search wrappers.

## Method
Read S7.34 review and SHA-256 object files offline; fail closed on missing/tampered objects or non-RSS content. Record every RSS link, host, title, source tier, filter reason, and possible wrapper target (display only). Aggregate host and reason counts. Do not fetch URLs or treat links as authenticated evidence.

## Decision gates
If most links are external, investigate alternative *source discovery* and separately label secondary sources. If legitimate official NBA paths were excluded, consider a narrowly scoped, tested filter repair. Never relax to arbitrary URLs, infer trade participation, or promote roster assignments from links alone.

## Governance
RESEARCH_ONLY / BLOCK_TRAINING. No S7.31, S7.26, S7.23 writes. Historical publication remains unverified.
