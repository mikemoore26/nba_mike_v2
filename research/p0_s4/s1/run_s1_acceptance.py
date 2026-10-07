from pathlib import Path

ROOT = Path.cwd()
PLAN = ROOT / "docs/P0_S4_FEATURE_TARGET_RESEARCH_PLAN.md"

def main() -> int:
    text = PLAN.read_text(encoding="utf-8") if PLAN.exists() else ""
    checks = {
        "plan_exists": PLAN.exists(),
        "architecture_defined": "availability -> minutes -> role/usage/opportunity -> stat distribution -> market -> decision" in text,
        "target_hierarchy": all(x in text for x in ["minutes played", "points", "rebounds", "assists", "made three-pointers"]),
        "feature_families": all(x in text for x in ["Player historical production", "Minutes and role", "Usage/opportunity", "Team context", "Opponent context", "Schedule/environment", "Advanced/tracking"]),
        "d1_preserved": "D-1" in text,
        "intraday_quarantine_preserved": "No unproven historical injury/lineup/news/market features." in text,
        "baseline_policy": "season-to-date mean" in text and "recent rolling mean" in text,
        "chronological_policy": "No random split as primary validation." in text,
        "model_training_gate": "S10 — P0-S4 Closeout / Model-Training Gate" in text,
    }
    overall = all(checks.values())
    print("P0-S4 S1 — Feature & Target Research Plan Acceptance")
    for k, v in checks.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")
    print(f"OVERALL: {'PASS' if overall else 'FAIL'}")
    return 0 if overall else 1

if __name__ == "__main__":
    raise SystemExit(main())
