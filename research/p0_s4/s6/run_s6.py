"""Offline-first S6 evaluation from S5.1 snapshots; no new data downloads."""
import argparse,json,hashlib
from pathlib import Path
import pandas as pd
from nba_mike.features.adaptive_form import make_form_frame
from nba_mike.features.minutes_uncertainty import uncertainty_frame,summarize

HERE=Path(__file__).resolve().parent
S5=HERE.parent/"s5_1"
SEASONS=("2019-20","2023-24","2025-26")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--alpha",type=float,default=.1)
    args=ap.parse_args()
    manifest_path=S5/"results"/"s5_1_manifest.json"
    if not manifest_path.exists():raise SystemExit("Missing S5.1 manifest. Run S5.1 first.")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    report={"status":"RESEARCH_ONLY","alpha":args.alpha,"calibration":"expanding prior-date absolute errors, pooled across players",
        "seasons":{},"source_manifest":str(manifest_path),
        "cautions":["Marginal pooled intervals do not guarantee per-player or role-group coverage",
        "2025-26 previously inspected; not a pristine holdout",
        "No DNP/injury/lineup/market integration",
        "No betting recommendation or model promotion"]}
    for season in SEASONS:
        p=S5/"snapshots"/f"player_gamelogs_{season}.csv"
        if not p.exists():raise SystemExit(f"Missing snapshot: {p}")
        digest=hashlib.sha256(p.read_bytes()).hexdigest()
        if digest!=manifest[season]["sha256"]:raise SystemExit(f"Snapshot checksum mismatch: {season}")
        raw=pd.read_csv(p,dtype={"game_id":str,"player_id":str,"team_id":str})
        form=make_form_frame(raw)
        pred=uncertainty_frame(form,alpha=args.alpha)
        groups={"overall":pred,"stable":pred[pred.role_change_flag==0],
                "role_change":pred[pred.role_change_flag==1]}
        report["seasons"][season]={name:summarize(data) for name,data in groups.items()}
        out=HERE/"results";out.mkdir(parents=True,exist_ok=True)
        pred.to_csv(out/f"s6_predictions_{season}.csv",index=False)
        print(season,report["seasons"][season]["overall"])
    (HERE/"results"/"s6_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("S6 RESEARCH COMPLETE — no promotion")
if __name__=="__main__":main()
