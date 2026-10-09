"""S8.14 offline pregame evidence feasibility; no network, fitting, or approval."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

SEASONS = ("2019-20", "2023-24", "2025-26")
BUBBLE_START, BUBBLE_END = "2020-07-30", "2020-08-14"
EVIDENCE_FIELDS = ("game_id", "player_id", "evidence_type", "source_name", "source_url", "source_file", "sha256", "published_at", "tipoff_at", "captured_at", "eligibility_assertion", "notes")
SOURCE_TYPES = ("pregame_roster", "injury_status", "lineup", "dnp_reconciliation", "official_schedule")


def parse_time(s):
    if not s:
        raise ValueError("missing timestamp")
    v = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if v.tzinfo is None or v.utcoffset() is None:
        raise ValueError("timestamp must have timezone offset")
    return v.astimezone(timezone.utc)


def classify_evidence(row, project_root):
    """Classify evidence packet readiness, never certify source independence."""
    if row.get("evidence_type") not in SOURCE_TYPES:
        return "REJECT_INVALID_TYPE", "unknown evidence type"
    if not row.get("game_id") or not row.get("source_name") or not row.get("source_url"):
        return "REJECT_MISSING_IDENTITY", "game/source identity incomplete"
    try:
        published = parse_time(row.get("published_at", ""))
        tipoff = parse_time(row.get("tipoff_at", ""))
        captured = parse_time(row.get("captured_at", ""))
    except (ValueError, TypeError) as exc:
        return "REJECT_TIMESTAMP", str(exc)
    if published >= tipoff:
        return "REJECT_NOT_PREGAME", "published_at must be strictly before tipoff_at"
    if captured < published:
        return "REJECT_CAPTURE_CHRONOLOGY", "captured_at precedes published_at"
    supplied = row.get("sha256", "").lower()
    if len(supplied) != 64 or any(c not in "0123456789abcdef" for c in supplied):
        return "REJECT_DIGEST", "missing or malformed sha256"
    raw_path = row.get("source_file", "")
    if not raw_path:
        return "REJECT_MISSING_ARTIFACT", "no independently preserved source artifact"
    path = (project_root / raw_path).resolve()
    try:
        path.relative_to(project_root.resolve())
    except ValueError:
        return "REJECT_PATH", "source artifact must be within project root"
    if not path.is_file():
        return "REJECT_MISSING_ARTIFACT", "source artifact not found"
    if hashlib.sha256(path.read_bytes()).hexdigest() != supplied:
        return "REJECT_DIGEST_MISMATCH", "artifact digest differs"
    return "CANDIDATE_MANUAL_REVIEW", "bytes and supplied timestamps internally consistent; source independence/publication unverified"


def load_games(path):
    games = {}
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if not {"game_id", "event_date", "player_id"}.issubset(reader.fieldnames or []):
            raise ValueError(f"snapshot missing game/date/player fields: {path}")
        for row in reader:
            game_id = row["game_id"].strip()
            date = row["event_date"].strip()[:10]
            datetime.strptime(date, "%Y-%m-%d")
            if not game_id or not row["player_id"].strip():
                raise ValueError("empty game/player id")
            if game_id in games and games[game_id]["event_date"] != date:
                raise ValueError(f"conflicting game dates for {game_id}")
            if game_id not in games:
                games[game_id] = {"game_id": game_id, "event_date": date, "participant_rows": 0}
            games[game_id]["participant_rows"] += 1
    return games


def select_sample(games, season, count=3):
    eligible = sorted((g for g in games.values() if not (season == "2019-20" and BUBBLE_START <= g["event_date"] <= BUBBLE_END)), key=lambda g:(g["event_date"],g["game_id"]))
    if not eligible:
        return []
    n = min(count, len(eligible))
    indexes = sorted(set(round(i*(len(eligible)-1)/max(1,n-1)) for i in range(n)))
    return [dict(eligible[i], season=season, source_universe="POSTGAME_PARTICIPANTS_ONLY", pregame_eligibility="NOT_VERIFIED", publication_provenance="NOT_VERIFIED", decision="RESEARCH_SAMPLE_ONLY") for i in indexes]


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields,extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def run(project_root, evidence_csv=None, sample_count=3):
    root=Path(project_root).resolve()
    output=root/'research/p0_s8/s8_14/results'
    output.mkdir(parents=True,exist_ok=True)
    samples=[]; datasets=[]; missing=[]
    for season in SEASONS:
        path=root/f'research/p0_s4/s5_1/snapshots/player_gamelogs_{season}.csv'
        if not path.is_file():
            missing.append(str(path.relative_to(root)))
            datasets.append({"season":season,"status":"MISSING_SNAPSHOT"})
            continue
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        games=load_games(path)
        sample=select_sample(games,season,sample_count)
        samples.extend(sample)
        datasets.append({"season":season,"status":"OFFLINE_SAMPLE_ONLY","sha256":digest,"games":len(games),"sampled_games":len(sample)})
    write_csv(output/'s8_14_sample_games.csv',samples,("season","game_id","event_date","participant_rows","source_universe","pregame_eligibility","publication_provenance","decision"))
    sources=[
      ("Official NBA injury reports", "injury_status", "Candidate archived reports; must prove report version and posting time, not PDF date alone"),
      ("Official NBA gamebooks", "dnp_reconciliation", "Often postgame; not valid as independent pregame eligibility without separate timestamped version"),
      ("Official NBA schedules", "official_schedule", "Verify game ID and actual tipoff timestamp from independent record"),
      ("Team pregame announcements / archived lineup releases", "lineup", "Require independently preserved pre-tipoff version and identity match"),
      ("Historical roster / transaction records", "pregame_roster", "Effective date alone does not prove pre-tipoff availability or active status"),
    ]
    write_csv(output/'s8_14_source_registry.csv',({"source_candidate":a,"evidence_type":b,"assessment":c,"availability":"NOT_TESTED","asof_proof":"NOT_VERIFIED"} for a,b,c in sources),("source_candidate","evidence_type","assessment","availability","asof_proof"))
    evidence=[]
    if evidence_csv:
        p=Path(evidence_csv)
        if not p.is_absolute():p=root/p
        with p.open(newline="",encoding="utf-8-sig") as fh:
            reader=csv.DictReader(fh)
            if not set(EVIDENCE_FIELDS).issubset(reader.fieldnames or []):
                raise ValueError("evidence CSV missing required fields")
            for row in reader:
                status,reason=classify_evidence(row,root)
                evidence.append({"game_id":row.get("game_id"),"player_id":row.get("player_id"),"evidence_type":row.get("evidence_type"),"status":status,"reason":reason})
    write_csv(output/'s8_14_evidence_review.csv',evidence,("game_id","player_id","evidence_type","status","reason"))
    report={"milestone":"S8.14","mode":"OFFLINE_HISTORICAL_PREGAME_FEASIBILITY","status":"RESEARCH_ONLY","decision":"BLOCK_TRAINING","training_eligible":False,"outcome":"SAMPLE_AND_SOURCE_INVENTORY_NOT_ASOF_CERTIFICATION","sampled_games":len(samples),"datasets":datasets,"missing_snapshots":missing,"evidence_rows_reviewed":len(evidence),"candidate_manual_review":sum(x["status"]=="CANDIDATE_MANUAL_REVIEW" for x in evidence),"independently_verified_games":0,"restart_88":"SEPARATELY_BLOCKED_UNVERIFIED","network_requests":0,"limitations":["Historical game logs contain postgame participants, not independent pregame eligibility","Supplied publication timestamps and artifacts are only internally checked, not independently verified","No DNP reconciliation or source independence certified","Official endpoint retries intentionally disabled","No training, fitting, or market analysis performed"]}
    (output/'s8_14_report.json').write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root',default='.')
    p.add_argument('--evidence-csv',default=None)
    p.add_argument('--sample-count',type=int,default=3)
    a=p.parse_args()
    if not 1<=a.sample_count<=20:p.error('--sample-count must be 1..20')
    print(json.dumps(run(a.project_root,a.evidence_csv,a.sample_count),indent=2))

if __name__=='__main__':main()
