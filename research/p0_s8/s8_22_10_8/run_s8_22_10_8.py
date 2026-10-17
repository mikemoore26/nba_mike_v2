"""Evidence intake and Git inventory; never certifies game IDs or training eligibility."""
import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

FIELDS = ['game_date','away_at_home','nba_game_id','source_url','snapshot_path','snapshot_sha256','source_row_reference','reviewer','reviewed_at_utc','review_decision']


def rows(path):
    with path.open(newline='',encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def write(path, data, fields):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(data)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(crosswalk, evidence, evidence_root):
    if not crosswalk: raise ValueError('Crosswalk empty')
    keys=[(r['game_date'],r['away_at_home']) for r in crosswalk]
    if len(set(keys))!=len(keys): raise ValueError('Duplicate crosswalk keys')
    if len(keys)!=10: raise ValueError('Expected ten unique matchups')
    targets={k:r for k,r in zip(keys,crosswalk) if r['game_id_status']=='UNVERIFIED_PROVISIONAL'}
    if len(targets)!=8: raise ValueError('Expected eight target games')
    seen=set(); used_ids={}; out=[]
    for e in evidence:
        key=(e.get('game_date',''),e.get('away_at_home',''))
        if key not in targets: raise ValueError('Evidence outside target slate: '+str(key))
        if key in seen: raise ValueError('Duplicate evidence: '+str(key))
        seen.add(key)
        gid=e.get('nba_game_id','').strip()
        if gid and not re.fullmatch(r'\d{10}',gid): raise ValueError('Invalid game ID: '+gid)
        if gid in used_ids and gid: raise ValueError('Duplicate game ID across matchups: '+gid)
        if gid: used_ids[gid]=key
        path_text=e.get('snapshot_path','').strip()
        digest=e.get('snapshot_sha256','').strip().lower()
        evidence_status='MISSING_EVIDENCE'
        if any(e.get(x,'').strip() for x in ('nba_game_id','source_url','snapshot_path','snapshot_sha256','source_row_reference','reviewer','review_decision')):
            evidence_status='INCOMPLETE_EVIDENCE'
            if path_text:
                path=(evidence_root/path_text).resolve()
                if not path.is_relative_to(evidence_root.resolve()): raise ValueError('Snapshot outside evidence directory')
                if not path.is_file(): raise ValueError('Missing snapshot: '+str(path))
                if not re.fullmatch('[0-9a-f]{64}',digest) or sha(path)!=digest: raise ValueError('Snapshot SHA256 mismatch: '+str(path))
            if (gid and gid==targets[key]['provisional_nba_game_id'] and
                e.get('source_url','').startswith('https://') and path_text and
                e.get('source_row_reference','').strip()):
                evidence_status='SNAPSHOT_PRESENT_REQUIRES_MANUAL_SOURCE_CHECK'
            if gid and gid!=targets[key]['provisional_nba_game_id']:
                evidence_status='GAME_ID_DISAGREEMENT_REQUIRES_INVESTIGATION'
        if e.get('review_decision','PENDING') not in ('','PENDING','ACCEPT','REJECT'):
            raise ValueError('Invalid review decision')
        # Review decisions are recorded but not promoted without separate independent source verification.
        out.append({'game_date':key[0],'away_at_home':key[1],
                    'provisional_nba_game_id':targets[key]['provisional_nba_game_id'],
                    'submitted_nba_game_id':gid,'evidence_status':evidence_status,
                    'review_decision_recorded':e.get('review_decision','PENDING') or 'PENDING',
                    'verified_game_id':'NO','source_url':e.get('source_url',''),
                    'snapshot_sha256':digest,'source_row_reference':e.get('source_row_reference','')})
    for key,r in targets.items():
        if key not in seen:
            out.append({'game_date':key[0],'away_at_home':key[1],
                        'provisional_nba_game_id':r['provisional_nba_game_id'],
                        'submitted_nba_game_id':'','evidence_status':'MISSING_EVIDENCE',
                        'review_decision_recorded':'PENDING','verified_game_id':'NO',
                        'source_url':'','snapshot_sha256':'','source_row_reference':''})
    return sorted(out,key=lambda r:(r['game_date'],r['away_at_home']))


def inventory(root):
    commands=[['git','status','--porcelain=v1','--untracked-files=normal'],
              ['git','diff','--name-only'],['git','ls-files','--others','--exclude-standard']]
    data={}
    for label,cmd in zip(('status','modified_tracked','untracked'),commands):
        p=subprocess.run(cmd,cwd=root,capture_output=True,text=True,check=False)
        data[label]={'returncode':p.returncode,'lines':p.stdout.splitlines(),'error':p.stderr.strip()}
    return data


def find_one(root):
    paths=sorted((root/'research/p0_s8/s8_22_10_7/results/2023-11-15').glob('*/provisional_game_id_crosswalk.csv'))
    if len(paths)!=1: raise RuntimeError('Expected one S8.22.10.7 crosswalk; pass --crosswalk explicitly')
    return paths[0]


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--project-root',default='.')
    p.add_argument('--crosswalk')
    p.add_argument('--evidence-csv')
    p.add_argument('--evidence-root')
    p.add_argument('--output')
    a=p.parse_args();root=Path(a.project_root).resolve()
    cw=Path(a.crosswalk).resolve() if a.crosswalk else find_one(root)
    evidence_root=Path(a.evidence_root).resolve() if a.evidence_root else root/'research/p0_s8/s8_22_10_8/manual_input'
    evidence_path=Path(a.evidence_csv).resolve() if a.evidence_csv else evidence_root/'game_id_evidence.csv'
    source=rows(cw)
    if evidence_path.exists():
        supplied=rows(evidence_path)
        if supplied and not set(FIELDS).issubset(supplied[0]): raise ValueError('Evidence CSV missing required columns')
    else: supplied=[]
    result=evaluate(source,supplied,evidence_root)
    token=hashlib.sha256((sha(cw)+(sha(evidence_path) if evidence_path.exists() else 'NO_EVIDENCE')).encode()).hexdigest()[:16]
    out=Path(a.output).resolve() if a.output else root/'research/p0_s8/s8_22_10_8/results/2023-11-15'/token
    out.mkdir(parents=True,exist_ok=True)
    write(out/'game_id_evidence_audit.csv',result,list(result[0]))
    if not evidence_path.exists():
        write(out/'game_id_evidence_template.csv',[
            {'game_date':r['game_date'],'away_at_home':r['away_at_home'],
             'nba_game_id':r['provisional_nba_game_id'],'review_decision':'PENDING'} for r in result],FIELDS)
    git=inventory(root)
    (out/'git_inventory.json').write_text(json.dumps(git,indent=2)+'\n',encoding='utf-8')
    report={'milestone':'S8.22.10.8','crosswalk_sha256':sha(cw),
            'evidence_csv_sha256':sha(evidence_path) if evidence_path.exists() else None,
            'target_games':len(result),'evidence_status_counts':dict(Counter(r['evidence_status'] for r in result)),
            'verified_game_ids':0,'manual_player_reviews_completed_by_this_step':0,
            'historical_asof':'NOT_CERTIFIED','decision':'BLOCK_TRAINING',
            'git_modified_tracked_count':len(git['modified_tracked']['lines']),
            'git_untracked_count':len(git['untracked']['lines']),
            'note':'A matching ID and archived source file are not automatic proof of an authoritative source row. Never overwrite research evidence.'}
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',out/'review.json');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
