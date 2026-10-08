"""S7.25: NBA Stats season roster acquisition; never asserts date-specific membership."""
import argparse
import csv
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ENDPOINT = "https://stats.nba.com/stats/commonteamroster"
TEAM_IDS = {
 "ATL":1610612737,"BOS":1610612738,"BKN":1610612751,"CHA":1610612766,
 "CHI":1610612741,"CLE":1610612739,"DAL":1610612742,"DEN":1610612743,
 "DET":1610612765,"GSW":1610612744,"HOU":1610612745,"IND":1610612754,
 "LAC":1610612746,"LAL":1610612747,"MEM":1610612763,"MIA":1610612748,
 "MIL":1610612749,"MIN":1610612750,"NOP":1610612740,"NYK":1610612752,
 "OKC":1610612760,"ORL":1610612753,"PHI":1610612755,"PHX":1610612756,
 "POR":1610612757,"SAC":1610612758,"SAS":1610612759,"TOR":1610612761,
 "UTA":1610612762,"WAS":1610612764}
FIELDS=("season","team_abbreviation","team_id","player_id","player_name","source_endpoint","source_sha256","retrieved_utc","evidence_class","date_specific_verified")

def decode_roster(payload):
    for item in payload.get("resultSets",[]):
        if item.get("name","").lower()=="commonteamroster":
            headers=item.get("headers",[])
            if not isinstance(headers,list) or not isinstance(item.get("rowSet"),list):
                raise ValueError("Invalid roster table")
            for row in item["rowSet"]:
                if len(row)!=len(headers): raise ValueError("Mismatched roster table columns")
                obj=dict(zip(headers,row))
                if obj.get("PLAYER_ID") is None or not obj.get("PLAYER"): raise ValueError("Missing stable player ID/name")
                yield str(obj["PLAYER_ID"]),str(obj["PLAYER"])
            return
    raise ValueError("No CommonTeamRoster result set")

def fetch(team_id, season, timeout=20, opener=urlopen):
    url=ENDPOINT+"?"+urlencode({"LeagueID":"00","Season":season,"TeamID":team_id})
    req=Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; NBA_MIKE_research/1.0)","Referer":"https://www.nba.com/","Origin":"https://www.nba.com","Accept":"application/json"})
    with opener(req,timeout=timeout) as response:
        raw=response.read(5_000_001)
    if len(raw)>5_000_000: raise ValueError("Source response too large")
    return raw,url

def collect(team, season, out, raw=None, source_url=None):
    if team not in TEAM_IDS: raise ValueError("Unknown team")
    if not (len(season)==7 and season[:4].isdigit() and season[4]=='-' and season[5:].isdigit() and int(season[5:])==(int(season[:4])+1)%100):
        raise ValueError("Invalid season; expected YYYY-YY")
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    if raw is None: raw,source_url=fetch(TEAM_IDS[team],season)
    source_url=source_url or ENDPOINT
    digest=hashlib.sha256(raw).hexdigest()
    # Validate before persisting; never interpret source as historical snapshot.
    payload=json.loads(raw)
    players=list(decode_roster(payload))
    if not players: raise ValueError("Empty roster response; refusing to claim coverage")
    if len(set(p[0] for p in players))!=len(players): raise ValueError("Duplicate player IDs")
    observed=datetime.now(timezone.utc).isoformat()
    rawdir=out/'raw';rawdir.mkdir(exist_ok=True)
    (rawdir/(digest+'.json')).write_bytes(raw)
    rows=[dict(season=season,team_abbreviation=team,team_id=str(TEAM_IDS[team]),player_id=pid,player_name=name,source_endpoint=source_url,source_sha256=digest,retrieved_utc=observed,evidence_class='SEASON_ROSTER_CANDIDATE_ONLY',date_specific_verified='false') for pid,name in players]
    with (out/'s7_25_season_roster_candidates.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    report=dict(milestone='S7.25',status='RESEARCH_ONLY',decision='BLOCK_TRAINING',team=team,season=season,player_rows=len(rows),source_sha256=digest,source_url=source_url,retrieved_utc=observed,evidence_class='SEASON_ROSTER_CANDIDATE_ONLY',date_specific_verified=False,verified_injury_assignments=0,eligible_for_asof_training=False,notes=['Current retrieval cannot establish historical roster membership on any past date','Do not merge into S7.23 or S7.24 date-specific evidence','NBA Stats endpoint may throttle or deny automated requests; source failure must not be treated as zero players','Historical injury-report publication time remains unverified'])
    (out/'s7_25_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

def main():
    p=argparse.ArgumentParser(description='Acquire NBA Stats season roster as unverified candidate evidence')
    p.add_argument('--team',default='NYK',choices=sorted(TEAM_IDS));p.add_argument('--season',default='2025-26');p.add_argument('--output-dir',default='research/p0_s4/s7_25/results');p.add_argument('--input-json',help='Optional offline NBA Stats response; no network call')
    a=p.parse_args()
    try:
        raw=Path(a.input_json).read_bytes() if a.input_json else None
        result=collect(a.team,a.season,a.output_dir,raw=raw,source_url=('offline:'+str(a.input_json)) if a.input_json else None)
        print(json.dumps(result,indent=2))
    except Exception as exc:
        print(json.dumps({'milestone':'S7.25','status':'ACQUISITION_FAILED','decision':'BLOCK_TRAINING','error_type':type(exc).__name__,'error':str(exc),'eligible_for_asof_training':False},indent=2))
        raise SystemExit(1)
if __name__=='__main__':main()
