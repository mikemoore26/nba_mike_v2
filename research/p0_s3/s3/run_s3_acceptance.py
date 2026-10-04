from pathlib import Path
import json
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from nba_mike.identity import IdentityConflictError, IdentityRegistry


def main() -> int:
    checks = {}
    r = IdentityRegistry()
    nyk = r.create_team("New York Knicks")
    bos = r.create_team("Boston Celtics")
    p1 = r.create_player("Example Player")
    p2 = r.create_player("Example Player")
    g = r.create_game("2026-10-20", nyk, bos)

    checks["canonical_ids"] = (nyk == "T00000001" and bos == "T00000002" and p1 == "P00000001" and g == "G00000001")

    r.add_source_mapping("player", "nba_stats", "123", p1)
    r.add_source_mapping("team", "nba_stats", "1610612752", nyk)
    r.add_source_mapping("game", "nba_stats", "0022600001", g)
    checks["source_resolution"] = r.resolve_source("player", "nba_stats", "123").canonical_id == p1

    try:
        r.add_source_mapping("player", "nba_stats", "123", p2)
        checks["conflict_rejected"] = False
    except IdentityConflictError:
        checks["conflict_rejected"] = True

    r.add_alias(p1, "Example Player")
    r.add_alias(p2, "Example Player")
    checks["ambiguous_alias"] = r.resolve_alias("player", "example player").status == "AMBIGUOUS"

    r.add_membership(p1, nyk, "2025-07-01", "2026-02-01", "acceptance")
    r.add_membership(p1, bos, "2026-02-01", None, "acceptance")
    checks["trade_safe_identity"] = (r.teams_for_player_on(p1, "2026-01-15") == (nyk,) and r.teams_for_player_on(p1, "2026-03-01") == (bos,))

    try:
        IdentityRegistry.assert_unique_player_games([
            {"game_id": g, "player_id": p1},
            {"game_id": g, "player_id": p1},
        ])
        checks["duplicate_player_game_rejected"] = False
    except IdentityConflictError:
        checks["duplicate_player_game_rejected"] = True

    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "registry.json"
        r.save_json(path)
        r2 = IdentityRegistry.load_json(path)
        checks["roundtrip"] = r.to_dict() == r2.to_dict()

    overall = all(checks.values())
    out = ROOT / "research" / "p0_s3" / "s3" / "results"
    out.mkdir(parents=True, exist_ok=True)
    report = {"milestone": "P0-S3 S3", "checks": checks, "overall": "PASS" if overall else "FAIL"}
    (out / "s3_acceptance_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = ["P0-S3 S3 — Canonical Identity Acceptance"] + [f"  {k}: {'PASS' if v else 'FAIL'}" for k, v in checks.items()] + [f"OVERALL: {'PASS' if overall else 'FAIL'}"]
    (out / "s3_acceptance_summary.txt").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if overall else 1

if __name__ == "__main__":
    raise SystemExit(main())
