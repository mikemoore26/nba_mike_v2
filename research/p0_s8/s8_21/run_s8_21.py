"""S8.21 offline-only evidence capture prototype. No network or training."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

SCHEMA = '''CREATE TABLE IF NOT EXISTS capture_events (
 event_id TEXT PRIMARY KEY, received_utc TEXT NOT NULL, source_kind TEXT NOT NULL,
 source_url TEXT NOT NULL, game_id TEXT, checkpoint TEXT, outcome TEXT NOT NULL,
 http_status INTEGER, sha256 TEXT, blob_path TEXT, duplicate_of TEXT,
 error_code TEXT, publisher_claim TEXT,
 CHECK(outcome IN ('SUCCESS','DUPLICATE','FAILURE'))
);'''
CHECKPOINTS = ('T-24H','T-6H','T-90M','T-30M')
KINDS = ('schedule','injury_report','roster','starting_lineup','market')

def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')

def validate(kind, url, checkpoint, payload, error_code):
    if kind not in KINDS: raise ValueError('unknown source_kind')
    if not url.startswith(('https://','fixture://')): raise ValueError('source URL must be https or fixture')
    if checkpoint not in CHECKPOINTS: raise ValueError('unknown checkpoint')
    if payload is None and not error_code: raise ValueError('failure requires error_code')
    if payload is not None and error_code: raise ValueError('success cannot carry error_code')
    if payload is not None and not isinstance(payload,bytes): raise TypeError('payload must be bytes')
    if payload is not None and len(payload)>3_000_000: raise ValueError('payload exceeds 3MB limit')

def capture(root: Path, *, kind: str, url: str, checkpoint: str, payload: bytes | None,
            game_id: str='0022300061', http_status: int | None=None,
            error_code: str | None=None, publisher_claim: str | None=None):
    validate(kind,url,checkpoint,payload,error_code)
    root = Path(root)
    root.mkdir(parents=True,exist_ok=True)
    blobs=root/'blobs'
    blobs.mkdir(exist_ok=True)
    if blobs.is_symlink(): raise ValueError('blob directory must not be a symlink')
    db=root/'capture_ledger.sqlite3'
    if db.is_symlink(): raise ValueError('ledger must not be a symlink')
    with sqlite3.connect(db) as conn:
        conn.execute(SCHEMA)
        # No UPDATE or DELETE API: append a new event for each attempt.
        digest=hashlib.sha256(payload).hexdigest() if payload is not None else None
        rel=f'blobs/{digest}.bin' if digest else None
        prior=conn.execute('SELECT event_id FROM capture_events WHERE sha256=? AND outcome IN (\'SUCCESS\',\'DUPLICATE\') ORDER BY rowid LIMIT 1',(digest,)).fetchone() if digest else None
        if digest:
            target=blobs/f'{digest}.bin'
            if target.is_symlink(): raise ValueError('artifact path must not be a symlink')
            if target.exists():
                if hashlib.sha256(target.read_bytes()).hexdigest()!=digest:
                    raise ValueError('artifact integrity mismatch: refusing to overwrite')
            else:
                try:
                    with target.open('xb') as fh:
                        fh.write(payload)
                        fh.flush(); os.fsync(fh.fileno())
                except FileExistsError:
                    if hashlib.sha256(target.read_bytes()).hexdigest()!=digest: raise ValueError('artifact race/integrity mismatch')
        outcome='FAILURE' if payload is None else ('DUPLICATE' if prior else 'SUCCESS')
        eid=uuid4().hex
        conn.execute('INSERT INTO capture_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                     (eid,utc_now(),kind,url,game_id,checkpoint,outcome,http_status,digest,rel,prior[0] if prior else None,error_code,publisher_claim))
        conn.commit()
    return {'event_id':eid,'outcome':outcome,'sha256':digest,'blob_path':rel}

def integrity(root: Path):
    root=Path(root)
    with sqlite3.connect(root/'capture_ledger.sqlite3') as conn:
        rows=conn.execute('SELECT DISTINCT sha256,blob_path FROM capture_events WHERE sha256 IS NOT NULL').fetchall()
    problems=[]
    for digest,rel in rows:
        p=root/rel
        if p.is_symlink() or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
            problems.append(rel)
    return {'checked_blobs':len(rows),'corrupt_or_missing':problems}

def report(root:Path):
    root=Path(root)
    with sqlite3.connect(root/'capture_ledger.sqlite3') as conn:
        conn.row_factory=sqlite3.Row
        events=[dict(r) for r in conn.execute('SELECT * FROM capture_events ORDER BY received_utc,event_id')]
    integ=integrity(root)
    results=root/'results';results.mkdir(exist_ok=True)
    with (results/'s8_21_capture_ledger.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['event_id','received_utc','source_kind','source_url','game_id','checkpoint','outcome','http_status','sha256','blob_path','duplicate_of','error_code','publisher_claim']);w.writeheader();w.writerows(events)
    counts={x:sum(e['outcome']==x for e in events) for x in ('SUCCESS','DUPLICATE','FAILURE')}
    observed={e['checkpoint'] for e in events if e['outcome'] in ('SUCCESS','DUPLICATE')}
    health={'milestone':'S8.21','mode':'OFFLINE_FIXTURE_CAPTURE','event_count':len(events),
            'outcomes':counts,'integrity':integ,'checkpoints_observed':sorted(observed),
            'checkpoints_missing':sorted(set(CHECKPOINTS)-observed),
            'independent_pregame_eligibility_verified':False,'network_requests':0,'model_fits':0,
            'status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING',
            'limitations':['Fixture timestamps are not evidence of historical pregame availability',
                           'Append-only API is not tamper-proof storage; DB file permissions and backups need hardening',
                           'No live source adapters, automatic scheduling, or independent eligibility certification']}
    (results/'s8_21_health_report.json').write_text(json.dumps(health,indent=2)+'\n',encoding='utf-8')
    return health

def demo(root:Path):
    # Fixed payloads simulate 2 successes, one duplicate, one failed retrieval.
    capture(root,kind='schedule',url='fixture://nba/schedule',checkpoint='T-24H',payload=b'{"game_id":"DEMO_ONLY"}',http_status=200,game_id='DEMO_ONLY')
    capture(root,kind='injury_report',url='fixture://nba/injury',checkpoint='T-6H',payload=b'%PDF-1.4 DEMO FIXTURE',http_status=200,game_id='DEMO_ONLY')
    capture(root,kind='schedule',url='fixture://nba/schedule',checkpoint='T-24H',payload=b'{"game_id":"DEMO_ONLY"}',http_status=200,game_id='DEMO_ONLY')
    capture(root,kind='market',url='fixture://market/authorized',checkpoint='T-90M',payload=None,error_code='SIMULATED_PROVIDER_UNAVAILABLE',game_id='DEMO_ONLY')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--project-root',type=Path,default=Path('.'))
    p.add_argument('--demo',action='store_true',help='Append four synthetic fixture events (repeat runs append more)')
    args=p.parse_args()
    root=args.project_root/'research/p0_s8/s8_21/artifacts'
    if args.demo: demo(root)
    elif not (root/'capture_ledger.sqlite3').exists():
        print('No ledger yet. Run with --demo to create offline fixture evidence.');return
    print(json.dumps(report(root),indent=2))
if __name__=='__main__': main()
