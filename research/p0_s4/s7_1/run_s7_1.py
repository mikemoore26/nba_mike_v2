"""Offline source registry audit; no downloads, scraping, or model fitting."""
import csv, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from nba_mike.data.injury_asof import audit_registry
here=Path(__file__).resolve().parent
path=here/'official_report_registry.csv'
rows=list(csv.DictReader(path.open(newline='',encoding='utf-8'))) if path.exists() else []
report=audit_registry(rows)
report['candidate_source']='https://official.nba.com/nba-injury-report-2025-26-season/'
report['sample_coverage']='Not established; candidate registry is illustrative only'
report['next_gate']='Acquire exact PDF bytes, verify SHA256 and report/publication timing, parse rows, link IDs, define tipoff cutoffs'
out=here/'results'/'s7_1_report.json'
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(f"S7.1 SOURCE REGISTRY AUDIT: {len(rows)} candidates; {report['verified_for_historical_asof']} provenance-complete; no training authorization")
print(out)
