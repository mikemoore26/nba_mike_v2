"""S7.24: conservative independent roster source staging, no invented effective dates."""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone, date
from pathlib import Path

FIELDS = ('player_id','player_name','team','valid_from','valid_through','source_name','source_url','retrieved_utc','source_asof_utc','evidence_id','independent_of_injury_pdf')
REQUIRED = ('player_id','player_name','team','valid_from','valid_through','source_name','source_url','source_asof_utc')

def ingest(source, output):
    source, output = Path(source), Path(output)
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    with source.open(newline='',encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or [])
        if not set(REQUIRED).issubset(headers):
            raise ValueError('Missing required input columns: ' + ','.join(sorted(set(REQUIRED)-headers)))
        rows = list(reader)
    accepted, rejected = [], []
    retrieval = datetime.now(timezone.utc).isoformat()
    for index, row in enumerate(rows,1):
        reasons = []
        if any(not (row.get(k) or '').strip() for k in REQUIRED): reasons.append('MISSING_REQUIRED_FIELD')
        try:
            start=date.fromisoformat(row.get('valid_from',''))
            end=date.fromisoformat(row.get('valid_through',''))
            if start>end: reasons.append('REVERSED_DATE_INTERVAL')
        except ValueError: reasons.append('INVALID_DATE')
        if not (row.get('source_url') or '').startswith('https://'): reasons.append('NON_HTTPS_SOURCE')
        if (row.get('independent_of_injury_pdf') or '').strip().lower()!='true': reasons.append('INDEPENDENCE_NOT_ATTESTED')
        if (row.get('interval_basis') or '').strip()!='DATED_PRIMARY_EVIDENCE': reasons.append('NO_DATED_PRIMARY_INTERVAL')
        if (row.get('identity_basis') or '').strip()!='STABLE_PLAYER_ID': reasons.append('NO_STABLE_ID_CONFIRMATION')
        try: datetime.fromisoformat(row.get('source_asof_utc','').replace('Z','+00:00'))
        except ValueError: reasons.append('INVALID_SOURCE_ASOF')
        if reasons:
            rejected.append({'input_row':index,'player_name':row.get('player_name',''),'reasons':'|'.join(reasons)})
            continue
        accepted.append({k:(row.get(k,'') if k not in ('retrieved_utc','evidence_id','independent_of_injury_pdf') else (retrieval if k=='retrieved_utc' else f'S724-{digest[:12]}-{index}' if k=='evidence_id' else 'true')) for k in FIELDS})
    output.mkdir(parents=True,exist_ok=True)
    evidence_file=output/'s7_24_qualified_evidence.csv'
    with evidence_file.open('w',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle,fieldnames=FIELDS);writer.writeheader();writer.writerows(accepted)
    with (output/'s7_24_rejected.csv').open('w',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle,fieldnames=('input_row','player_name','reasons'));writer.writeheader();writer.writerows(rejected)
    report={'milestone':'S7.24','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','source_sha256':digest,'input_rows':len(rows),'qualified_evidence_rows':len(accepted),'rejected_rows':len(rejected),'historical_publication_verified':False,'eligible_for_asof_training':False,'note':'Qualified evidence is provisional pending independent source authentication and stable player-ID linkage; do not auto-merge into S7.23 or train.'}
    (output/'s7_24_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',default='research/p0_s4/s7_24/source_roster_intervals.csv');p.add_argument('--output-dir',default='research/p0_s4/s7_24/results');a=p.parse_args()
    print(json.dumps(ingest(a.source,a.output_dir),indent=2))
if __name__=='__main__':main()
