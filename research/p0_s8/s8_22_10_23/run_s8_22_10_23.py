"""S8.22.10.23: fail-closed historical team evidence reconciliation.

Never treat season roster membership, user-entered CSV, or modern player directory as
independently certified date-specific team membership.
"""
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path

DATE = '2023-11-15'
FIELDS = ['record_id','raw_name','candidate_nba_person_id','report_team','evidence_count','classification','evidence_ids','historical_team_verified','identity_certified','training_decision']
EVIDENCE_FIELDS = ['evidence_id','nba_person_id','team_abbreviation','valid_from','valid_to','source_url','source_title','source_published_at_utc','captured_at_utc','source_document_sha256','source_type','notes']

def sha(data): return hashlib.sha256(data).hexdigest()
def csvrows(path):
    with path.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def write_immutable(path, data):
    if path.exists() and path.read_bytes()!=data: raise ValueError('Immutable output conflict: '+str(path))
    if not path.exists(): path.write_bytes(data)
def csvbytes(rows,fields):
    out=io.StringIO(newline=''); writer=csv.DictWriter(out,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows);return out.getvalue().encode('utf-8')
def parse_date(s): return dt.date.fromisoformat(s)
def locate_candidates(root):
    base=root/'research/p0_s8/s8_22_10_22a/results'/DATE
    matches=[]
    for mf in base.glob('*/capture_manifest.json'):
        m=json.loads(mf.read_text(encoding='utf-8'))
        csvfile=mf.parent/'player_id_candidates.csv'
        if m.get('milestone')!='S8.22.10.22A' or m.get('training_decision')!='BLOCK_TRAINING' or not csvfile.exists() or sha(csvfile.read_bytes())!=m.get('candidate_csv_sha256'): continue
        matches.append((mf,csvfile,m))
    if len(matches)!=1:raise ValueError(f'Expected exactly one hash-validated S8.22.10.22A candidate capture, found {len(matches)}')
    return matches[0]
def validate_candidates(rows):
    if len(rows)!=44 or len({r['record_id'] for r in rows})!=44:raise ValueError('Expected 44 distinct player candidates')
    for r in rows:
        if r.get('match_class')!='UNIQUE_NAME_ID_CANDIDATE' or not r.get('candidate_nba_person_id','').isdigit() or not r.get('report_team'):raise ValueError('Invalid predecessor candidate')
        if r.get('historical_team_verified')!='NO' or r.get('player_identity_certified')!='NO':raise ValueError('Predecessor unexpectedly certified identities')
def load_evidence(path):
    if path is None:return [],None
    if not path.is_file():raise ValueError('Evidence file not found: '+str(path))
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not set(EVIDENCE_FIELDS).issubset(set(reader.fieldnames or [])):raise ValueError('Evidence CSV schema incomplete')
        rows=list(reader)
    seen=set()
    for r in rows:
        eid=r['evidence_id'].strip()
        if not eid or eid in seen:raise ValueError('Duplicate/blank evidence ID')
        seen.add(eid)
        if not r['nba_person_id'].isdigit() or int(r['nba_person_id'])<=0:raise ValueError('Invalid evidence player ID')
        if not r['team_abbreviation'].strip():raise ValueError('Blank team')
        start,end=parse_date(r['valid_from']),parse_date(r['valid_to'])
        if start>end:raise ValueError('Invalid date range')
        if r['source_document_sha256'] and (len(r['source_document_sha256'])!=64 or any(c not in '0123456789abcdef' for c in r['source_document_sha256'].lower())):raise ValueError('Invalid source SHA-256')
        for key in ('source_published_at_utc','captured_at_utc'):
            if r[key]:dt.datetime.fromisoformat(r[key].replace('Z','+00:00'))
    return rows,sha(path.read_bytes())
def classify(candidates,evidence):
    idx=defaultdict(list)
    for e in evidence:
        if parse_date(e['valid_from'])<=parse_date(DATE)<=parse_date(e['valid_to']):idx[e['nba_person_id']].append(e)
    out=[]
    for r in sorted(candidates,key=lambda r:r['record_id']):
        hits=idx.get(r['candidate_nba_person_id'],[])
        same=[h for h in hits if h['team_abbreviation'].strip().upper()==r['report_team'].strip().upper()]
        other=[h for h in hits if h not in same]
        if not hits:cls='NO_DATED_EVIDENCE'
        elif same and other:cls='CONFLICTING_DATED_TEAM_EVIDENCE'
        elif other:cls='DATED_TEAM_MISMATCH_REVIEW'
        elif len(same)>0:cls='DATED_TEAM_MATCH_UNCERTIFIED'
        else:raise AssertionError('unreachable')
        out.append({'record_id':r['record_id'],'raw_name':r['raw_name'],'candidate_nba_person_id':r['candidate_nba_person_id'],'report_team':r['report_team'],'evidence_count':len(hits),'classification':cls,'evidence_ids':';'.join(h['evidence_id'] for h in hits),'historical_team_verified':'NO','identity_certified':'NO','training_decision':'BLOCK_TRAINING'})
    return out

def run(root,evidence_path=None):
    root=Path(root).resolve();mf,src,manifest=locate_candidates(root)
    candidates=csvrows(src);validate_candidates(candidates)
    evidence,evidence_hash=load_evidence(Path(evidence_path).resolve() if evidence_path else None)
    results=classify(candidates,evidence)
    # Token reflects input evidence and predecessor, not mutable clock time.
    token=sha((manifest['candidate_csv_sha256']+'|'+(evidence_hash or 'NONE')).encode())[:16]
    dest=root/'research/p0_s8/s8_22_10_23/results'/DATE/token;dest.mkdir(parents=True,exist_ok=True)
    output=dest/'historical_team_evidence_review.csv';write_immutable(output,csvbytes(results,FIELDS))
    counts=dict(sorted(Counter(r['classification'] for r in results).items()))
    review={'milestone':'S8.22.10.23','target_game_date':DATE,'predecessor_manifest':str(mf.relative_to(root)),'predecessor_candidate_sha256':manifest['candidate_csv_sha256'],'evidence_supplied':evidence_path is not None,'evidence_file_sha256':evidence_hash,'evidence_rows':len(evidence),'review_csv_sha256':sha(output.read_bytes()),'player_candidates':44,'classification_counts':counts,'historical_team_verified':0,'player_ids_certified':0,'injury_statuses_certified':0,'historical_asof_certified':0,'research_status':'RESEARCH_ONLY','training_decision':'BLOCK_TRAINING','note':'Evidence rows are untrusted until independently authenticated. Date ranges in supplied CSV are claims, not certified historical roster proof. No automatic promotion.'}
    report=dest/'review.json';write_immutable(report,(json.dumps(review,indent=2)+'\n').encode())
    print('REPORT:',report);print(json.dumps(review,indent=2));return review

def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');p.add_argument('--evidence-csv',default=None);a=p.parse_args()
    try:run(a.project_root,a.evidence_csv)
    except (ValueError,KeyError,OSError,TypeError,json.JSONDecodeError) as e:p.exit(2,'FAIL CLOSED: '+str(e)+'\n')
if __name__=='__main__':main()
