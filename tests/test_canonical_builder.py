from pathlib import Path
from hashlib import sha256
import csv, json, sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nba_mike.canonical.builder import BuildError, build_player_game_box

FIELDS = ["GAME_ID","GAME_DATE","PLAYER_ID","TEAM_ID","OPP_TEAM_ID","MIN","PTS","REB","AST","FG3M"]
MAP = {"game_id":"GAME_ID","game_date":"GAME_DATE","player_id":"PLAYER_ID","team_id":"TEAM_ID","opponent_team_id":"OPP_TEAM_ID","minutes":"MIN","points":"PTS","rebounds":"REB","assists":"AST","three_pointers_made":"FG3M"}
IDS = {("player","nba","1"):"player-1",("player","nba","2"):"player-2",("team","nba","10"):"team-10",("team","nba","20"):"team-20"}

def make(tmp, rows, status="PASS"):
    raw=tmp/"raw.csv"; man=tmp/"raw.manifest.json"
    with raw.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    man.write_text(json.dumps({"artifact_id":"raw-1","sha256":sha256(raw.read_bytes()).hexdigest(),"validation_status":status}),encoding="utf-8")
    return raw,man

def row(player="1", minutes="34"):
    return {"GAME_ID":"g1","GAME_DATE":"2026-01-01","PLAYER_ID":player,"TEAM_ID":"10","OPP_TEAM_ID":"20","MIN":minutes,"PTS":"25","REB":"7","AST":"5","FG3M":"3"}

def build(tmp, raw, man, ids=IDS):
    return build_player_game_box(project_root=tmp,raw_path=raw,parent_manifest_path=man,output_path=tmp/"canonical.csv",output_manifest_path=tmp/"canonical.manifest.json",source_name="nba",column_map=MAP,identity_resolver=ids)

def test_happy_path(tmp_path):
    raw,man=make(tmp_path,[row()]); result=build(tmp_path,raw,man)
    assert result.row_count==1 and result.output_path.exists() and result.manifest_path.exists()

def test_parent_must_pass(tmp_path):
    raw,man=make(tmp_path,[row()],"QUARANTINED")
    with pytest.raises(BuildError,match="PARENT_NOT_PASS"): build(tmp_path,raw,man)

def test_tamper_rejected(tmp_path):
    raw,man=make(tmp_path,[row()]); raw.write_text(raw.read_text()+"tamper",encoding="utf-8")
    with pytest.raises(BuildError,match="PARENT_HASH_MISMATCH"): build(tmp_path,raw,man)

def test_unresolved_identity_rejected(tmp_path):
    raw,man=make(tmp_path,[row(player="999")])
    with pytest.raises(BuildError,match="IDENTITY_UNRESOLVED"): build(tmp_path,raw,man)

def test_duplicate_canonical_key_rejected(tmp_path):
    raw,man=make(tmp_path,[row(),row()])
    with pytest.raises(BuildError,match="DUPLICATE_CANONICAL_KEY"): build(tmp_path,raw,man)

def test_impossible_value_rejected(tmp_path):
    raw,man=make(tmp_path,[row(minutes="-1")])
    with pytest.raises(BuildError,match="IMPOSSIBLE_NEGATIVE_VALUE"): build(tmp_path,raw,man)

def test_missing_source_column_rejected(tmp_path):
    raw,man=make(tmp_path,[row()]); bad=dict(MAP); bad["points"]="MISSING"
    with pytest.raises(BuildError,match="SOURCE_SCHEMA_MISSING"):
        build_player_game_box(project_root=tmp_path,raw_path=raw,parent_manifest_path=man,output_path=tmp_path/"x.csv",output_manifest_path=tmp_path/"x.json",source_name="nba",column_map=bad,identity_resolver=IDS)

def test_manifest_links_parent(tmp_path):
    raw,man=make(tmp_path,[row()]); result=build(tmp_path,raw,man)
    data=json.loads(result.manifest_path.read_text())
    assert data["parent_artifact_ids"]==["raw-1"] and data["validation_status"]=="PASS" and data["row_count"]==1
