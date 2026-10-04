from __future__ import annotations
import hashlib
import json
import tempfile
from pathlib import Path

from nba_mike.snapshots.builder import SnapshotError, build_d1_snapshot, write_snapshot


def main() -> int:
    checks = {}
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        parent = root / "canonical.json"
        parent.write_text('{"canonical":"evidence"}', encoding="utf-8")
        sha = hashlib.sha256(parent.read_bytes()).hexdigest()
        manifest = {"artifact_id":"canonical-001","sha256":sha,"relative_path":"data/canonical/canonical.json","validation_status":"PASS"}
        rows = [
            {"game_id":"g1","event_date":"2026-10-01","player_id":"p1","team_id":"t1","points":10},
            {"game_id":"g2","event_date":"2026-10-02","player_id":"p1","team_id":"t1","points":15},
            {"game_id":"g3","event_date":"2026-10-03","player_id":"p1","team_id":"t1","points":99},
            {"game_id":"g4","event_date":"2026-10-04","player_id":"p1","team_id":"t1","points":100},
        ]

        snap, meta = build_d1_snapshot(rows,target_game_date="2026-10-03",parent_manifest=manifest,parent_artifact_path=parent,expected_entities=[{"player_id":"p1","team_id":"t1"},{"player_id":"rookie","team_id":"t2"}],code_git_commit="acceptance")
        checks["d1_cutoff"] = [r["game_id"] for r in snap] == ["g1","g2"]
        checks["same_day_future_blocked"] = all(r["event_date"] < "2026-10-03" for r in snap)
        checks["parent_provenance"] = meta["parent_artifact_id"] == "canonical-001" and meta["parent_sha256"] == sha
        checks["explicit_as_of_time"] = meta["as_of_time"].startswith("2026-10-02T23:59:59")
        checks["zero_history"] = any(x["player_id"]=="rookie" and x["history_status"]=="ZERO_HISTORY" for x in meta["entity_history"])

        snap2, meta2 = build_d1_snapshot(list(reversed(rows)),target_game_date="2026-10-03",parent_manifest=manifest,parent_artifact_path=parent,expected_entities=[{"player_id":"p1","team_id":"t1"},{"player_id":"rookie","team_id":"t2"}],code_git_commit="acceptance")
        checks["deterministic_rebuild"] = snap == snap2 and meta["logical_sha256"] == meta2["logical_sha256"]

        try:
            bad = dict(manifest); bad["validation_status"]="FAILED"
            build_d1_snapshot(rows,target_game_date="2026-10-03",parent_manifest=bad,parent_artifact_path=parent)
            checks["non_pass_parent_blocked"] = False
        except SnapshotError: checks["non_pass_parent_blocked"] = True

        try:
            dup = rows + [dict(rows[0])]
            build_d1_snapshot(dup,target_game_date="2026-10-03",parent_manifest=manifest,parent_artifact_path=parent)
            checks["duplicate_rejected"] = False
        except SnapshotError: checks["duplicate_rejected"] = True

        original = parent.read_text(encoding="utf-8")
        parent.write_text("tampered",encoding="utf-8")
        try:
            build_d1_snapshot(rows,target_game_date="2026-10-03",parent_manifest=manifest,parent_artifact_path=parent)
            checks["tamper_rejected"] = False
        except SnapshotError: checks["tamper_rejected"] = True
        parent.write_text(original,encoding="utf-8")

        outdir = Path(__file__).parent / "results" / "sample_snapshot"
        csv_path, man_path = write_snapshot(snap, meta, outdir)
        checks["snapshot_written"] = csv_path.exists() and man_path.exists()

    overall = all(checks.values())
    lines = ["P0-S3 S6 — Reproducible D-1 Point-in-Time Snapshot Acceptance"]
    for k,v in checks.items():
        lines.append(f"  {k}: {'PASS' if v else 'FAIL'}")
    lines.append(f"OVERALL: {'PASS' if overall else 'FAIL'}")
    text="\n".join(lines)
    print(text)
    results = Path(__file__).parent / "results"
    results.mkdir(parents=True, exist_ok=True)
    (results/"s6_acceptance_summary.txt").write_text(text+"\n",encoding="utf-8")
    (results/"s6_acceptance_report.json").write_text(json.dumps({"checks":checks,"overall":"PASS" if overall else "FAIL"},indent=2),encoding="utf-8")
    return 0 if overall else 1

if __name__ == "__main__":
    raise SystemExit(main())
