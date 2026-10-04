from pathlib import Path
from hashlib import sha256
import csv, json, shutil, sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"src"))
from nba_mike.canonical.builder import BuildError, build_player_game_box

WORK=Path(__file__).parent/"work"; RESULTS=Path(__file__).parent/"results"
FIELDS=["GAME_ID","GAME_DATE","PLAYER_ID","TEAM_ID","OPP_TEAM_ID","MIN","PTS","REB","AST","FG3M"]
MAP={"game_id":"GAME_ID","game_date":"GAME_DATE","player_id":"PLAYER_ID","team_id":"TEAM_ID","opponent_team_id":"OPP_TEAM_ID","minutes":"MIN","points":"PTS","rebounds":"REB","assists":"AST","three_pointers_made":"FG3M"}
IDS={("player","nba","1"):"player-1",("player","nba","2"):"player-2",("team","nba","10"):"team-10",("team","nba","20"):"team-20"}
ROWS=[{"GAME_ID":"g1","GAME_DATE":"2026-01-01","PLAYER_ID":"1","TEAM_ID":"10","OPP_TEAM_ID":"20","MIN":"34","PTS":"25","REB":"7","AST":"5","FG3M":"3"},{"GAME_ID":"g1","GAME_DATE":"2026-01-01","PLAYER_ID":"2","TEAM_ID":"20","OPP_TEAM_ID":"10","MIN":"31","PTS":"18","REB":"4","AST":"8","FG3M":"2"}]

def fixture(rows=ROWS,status="PASS"):
    shutil.rmtree(WORK,ignore_errors=True); WORK.mkdir(parents=True)
    raw=WORK/"raw.csv"; man=WORK/"raw.manifest.json"
    with raw.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    man.write_text(json.dumps({"artifact_id":"raw-fixture-1","sha256":sha256(raw.read_bytes()).hexdigest(),"validation_status":status}),encoding="utf-8")
    return raw,man

def attempt(raw,man,ids=IDS):
    return build_player_game_box(project_root=ROOT,raw_path=raw,parent_manifest_path=man,output_path=WORK/"canonical.csv",output_manifest_path=WORK/"canonical.manifest.json",source_name="nba",column_map=MAP,identity_resolver=ids)

def rejected(fn, token):
    try: fn(); return False
    except BuildError as e: return token in str(e)

def main():
    checks={}
    raw,man=fixture(); result=attempt(raw,man); checks["canonical_build"] = result.row_count==2 and result.output_path.exists()
    m=json.loads(result.manifest_path.read_text()); checks["parent_provenance"] = m.get("parent_artifact_ids")==["raw-fixture-1"] and bool(m.get("parent_sha256"))
    raw,man=fixture(status="QUARANTINED"); checks["non_pass_parent_blocked"] = rejected(lambda: attempt(raw,man),"PARENT_NOT_PASS")
    raw,man=fixture(); raw.write_text(raw.read_text()+"tamper",encoding="utf-8"); checks["tamper_rejected"] = rejected(lambda: attempt(raw,man),"PARENT_HASH_MISMATCH")
    bad=[dict(ROWS[0]),dict(ROWS[0])]; raw,man=fixture(bad); checks["duplicate_rejected"] = rejected(lambda: attempt(raw,man),"DUPLICATE_CANONICAL_KEY")
    bad=[dict(ROWS[0])]; bad[0]["PLAYER_ID"]="999"; raw,man=fixture(bad); checks["unresolved_identity_rejected"] = rejected(lambda: attempt(raw,man),"IDENTITY_UNRESOLVED")
    bad=[dict(ROWS[0])]; bad[0]["MIN"]="-2"; raw,man=fixture(bad); checks["impossible_value_rejected"] = rejected(lambda: attempt(raw,man),"IMPOSSIBLE_NEGATIVE_VALUE")
    overall=all(checks.values()); RESULTS.mkdir(parents=True,exist_ok=True)
    report={"milestone":"P0-S3 S5","checks":checks,"overall":"PASS" if overall else "FAIL"}
    (RESULTS/"s5_acceptance_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    lines=["P0-S3 S5 — Canonical Dataset Builder Acceptance"]+[f"  {k}: {'PASS' if v else 'FAIL'}" for k,v in checks.items()]+[f"OVERALL: {'PASS' if overall else 'FAIL'}"]
    text="\n".join(lines); (RESULTS/"s5_acceptance_summary.txt").write_text(text+"\n",encoding="utf-8"); print(text)
    shutil.rmtree(WORK,ignore_errors=True)
    return 0 if overall else 1

if __name__=="__main__": raise SystemExit(main())
