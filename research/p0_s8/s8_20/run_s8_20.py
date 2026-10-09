"""S8.20: research-only hybrid historical/forward collection strategy audit.
No network requests, training, odds scraping or source certification.
"""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

SOURCES = [
    ('schedule', 'NBA official schedule', 'game_id,scheduled_tipoff_utc,home,away', 'official schedule endpoint or saved official schedule'),
    ('injury_report', 'NBA official injury report', 'edition_label,game_id,team,player,status', 'official published PDF'),
    ('roster', 'NBA team roster', 'team,player,roster_status', 'official roster page'),
    ('starting_lineup', 'official lineup announcement', 'game_id,team,player,lineup_status', 'timestamped official release'),
    ('market', 'licensed sportsbook lines', 'book,market,selection,line,odds', 'authorized data provider; no scraping'),
]
CHECKPOINTS = [('T-24H', -1440), ('T-6H', -360), ('T-90M', -90), ('T-30M', -30)]
STRATEGIES = [
    ('historical_reconstruction', 'RESEARCH_ONLY', 'Potential long history', 'Historical as-of/eligibility unverified', 'DO_NOT_PROMOTE'),
    ('forward_only', 'FUTURE_CAPTURE_DESIGN', 'Independently logged retrievals', 'Needs prospective accumulation and source validation', 'DESIGN_ONLY'),
    ('hybrid', 'RECOMMENDED_DESIGN', 'Separates exploratory history from prospective evidence', 'Requires strict dataset partition and gate review', 'DESIGN_ONLY'),
]

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def inspect(root):
    targets = [
        'research/p0_s8/s8_13/results/s8_13_report.json',
        'research/p0_s8/s8_14/results/s8_14_report.json',
        'research/p0_s8/s8_19/results/s8_19_report.json',
    ]
    found=[]
    for rel in targets:
        p=root/rel
        record={'path':rel,'exists':p.is_file(),'sha256':sha256(p) if p.is_file() else '', 'reported_decision':'', 'parse_status':'NOT_PRESENT'}
        if p.is_file():
            try:
                obj=json.loads(p.read_text(encoding='utf-8-sig'))
                record['reported_decision']=str(obj.get('decision',''))
                record['parse_status']='JSON_PARSED'
            except (ValueError,UnicodeError,OSError) as exc:
                record['parse_status']='PARSE_FAILED:'+type(exc).__name__
        found.append(record)
    return found

def write_csv(path, headers, rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(headers);w.writerows(rows)

def run(root):
    root=root.resolve()
    out=root/'research/p0_s8/s8_20/results'
    out.mkdir(parents=True,exist_ok=True)
    prior=inspect(root)
    write_csv(out/'s8_20_strategy_comparison.csv', ['strategy','mode','advantage','limitation','eligibility'],STRATEGIES)
    write_csv(out/'s8_20_capture_design.csv', ['source_kind','source','minimum_fields','acquisition_policy'],SOURCES)
    write_csv(out/'s8_20_checkpoint_design.csv', ['checkpoint','minutes_relative_to_tipoff','capture_mode','required_provenance'],
              [(label,mins,'FUTURE_ONLY_NOT_SCHEDULED','retrieved_utc,source_url,http_status,sha256,immutable_original,source_timestamp_claim') for label,mins in CHECKPOINTS])
    write_csv(out/'s8_20_prior_evidence.csv', ['path','exists','sha256','reported_decision','parse_status'],
              [[v[k] for k in ('path','exists','sha256','reported_decision','parse_status')] for v in prior])
    report={
        'milestone':'S8.20','mode':'OFFLINE_HYBRID_STRATEGY_DESIGN',
        'generated_utc':datetime.now(timezone.utc).isoformat(),
        'strategy':'HYBRID_FORWARD_EVIDENCE_FIRST',
        'historical_partition':'EXPLORATORY_ONLY_NOT_PREGAME_CERTIFIED',
        'forward_partition':'DESIGN_ONLY_NO_SNAPSHOTS_CAPTURED',
        'prospective_snapshots_collected':0,
        'training_eligible':False,'decision':'BLOCK_TRAINING','status':'RESEARCH_ONLY',
        'network_requests':0,'model_fits':0,
        'source_kinds':len(SOURCES),'checkpoint_templates':len(CHECKPOINTS),
        'prior_reports':prior,
        'requirements_for_future_capture':[
            'Capture immutable raw bytes and receipt UTC before the applicable tipoff',
            'Preserve HTTP response headers and separate publisher-claimed timestamps from retrieval timestamps',
            'Record stable game/player IDs and independent eligibility evidence; reconcile DNPs after games only for labels',
            'Prevent historical exploratory rows from entering certified training partitions',
            'Keep market sources authorized; never scrape prohibited endpoints',
            'Record failures and absence of evidence explicitly; do not backfill prospective capture times',
            'Keep S8.13 training boundary fail-closed pending independent verification',
            'Keep 88 restart games blocked separately'
        ],
        'limitations':['No historical as-of certification','No live collector implemented','No game or player population approved','No training or betting']
    }
    (out/'s8_20_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--project-root',type=Path,default=Path('.'))
    args=ap.parse_args()
    report=run(args.project_root)
    print(json.dumps({'milestone':report['milestone'],'decision':report['decision'],'source_kinds':report['source_kinds'],'checkpoint_templates':report['checkpoint_templates'],'network_requests':report['network_requests']},indent=2))

if __name__=='__main__': main()
