# S7.17 — Injury reason recovery

S7.16 independent crop review found 7 of 20 sampled reason fields missing despite visible PDF reason text. S7.17 performs a conservative reason-lane geometry pass only for blank reasons. It emits proposals, never modifies source records, and never assumes proposals are correct. Compare seven previously flagged samples against the original PDF before approval. Multi-line reason handling uses source word coordinates. Publication-time evidence and missing-row recall remain open gates.
