"""S8.22.10.18 read-only investigation of uniform name/excerpt diagnostic failures.

Evidence is local extracted text only, never independently authenticated identities.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import unicodedata

DATE='2023-11-15'
SOURCE_SHA='70cc499b1c35cd65cde2ce0c8836e1db13e9194a43ac290450755f067ff3c3db'
AUDIT_FIELDS=('record_id','raw_player_name','source_pdf_context','name_quality','source_excerpt_check')
OUT_FIELDS=['record_id','raw_name','source_excerpt','source_name_candidate','name_tokens','excerpt_tokens','name_format','literal_name_present','token_order_match','reverse_token_order_match','name_in_source_candidate','diagnostic_class','reason','player_identity_certified','injury_status_certified','historical_asof_certified']

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def csv_rows(p):
    with p.open(newline='',encoding='utf-8-sig') as f:
        rd=csv.DictReader(f)
        if not rd.fieldnames: raise ValueError('Missing CSV header: '+str(p))
        return list(rd)
def norm(v): return ' '.join(unicodedata.normalize('NFKC',v or '').casefold().split())
def tokens(v): return re.findall(r"[^\W_]+",norm(v),flags=re.UNICODE)
def ordered(haystack, needle):
    if not needle:return False
    return any(haystack[i:i+len(needle)]==needle for i in range(len(haystack)-len(needle)+1))
def diagnose(name,excerpt,source_name=''):
    nt=tokens(name); et=tokens(excerpt); st=tokens(source_name)
    literal=bool(norm(name) and norm(name) in norm(excerpt))
    order=ordered(et,nt); reverse=ordered(et,list(reversed(nt))) if len(nt)>1 else False
    source_equal=bool(nt and st and nt==st)
    if not name.strip(): klass,why='EMPTY_NAME','Candidate name empty'
    elif literal: klass,why='LITERAL_MATCH','Full normalized name appears literally in excerpt'
    elif order: klass,why='TOKEN_LAYOUT_MISMATCH','Name tokens appear consecutively but text spacing/punctuation differs'
    elif reverse: klass,why='REVERSED_NAME_LAYOUT','Name tokens appear in reverse order in excerpt'
    elif source_equal: klass,why='SOURCE_NAME_FIELD_MATCH','Candidate agrees with separate source name field; excerpt not sufficient'
    elif not excerpt.strip(): klass,why='EMPTY_EXCERPT','Excerpt is empty; cannot test name presence'
    else: klass,why='NO_LOCAL_NAME_CORROBORATION','No contiguous name match in local excerpt or source name field'
    return dict(name_tokens='|'.join(nt),excerpt_tokens='|'.join(et[:60]),literal_name_present=str(literal).upper(),token_order_match=str(order).upper(),reverse_token_order_match=str(reverse).upper(),name_in_source_candidate=str(source_equal).upper(),diagnostic_class=klass,reason=why)

def locate(root,milestone,filename,sha=None):
    base=root/'research/p0_s8'/milestone/'results'/DATE
    candidates=sorted(base.glob('*/'+filename))
    if sha: candidates=[p for p in candidates if digest(p)==sha]
    if len(candidates)!=1:raise ValueError(f'Expected exactly one {filename} under {base}, found {len(candidates)}')
    return candidates[0]

def analyze(ledger,audit):
    source={r['record_id']:r for r in ledger if r.get('record_type')=='PLAYER'}
    if len(source)!=44 or len(audit)!=44:raise ValueError('Expected exactly 44 unique player rows')
    ids=[r['record_id'] for r in audit]
    if len(set(ids))!=44 or set(ids)!=set(source):raise ValueError('Player record IDs do not match source ledger')
    out=[]
    for a in audit:
        s=source[a['record_id']]
        name=s.get('name_or_notice_candidate','')
        excerpt=s.get('pdf_context_excerpt','')
        if a.get('raw_player_name')!=name or a.get('source_pdf_context')!=excerpt:raise ValueError('Source/audit evidence mismatch: '+a['record_id'])
        d=diagnose(name,excerpt,s.get('source_name_candidate',''))
        out.append(dict(record_id=a['record_id'],raw_name=name,source_excerpt=excerpt[:600],source_name_candidate=s.get('source_name_candidate',''),name_format=a.get('name_quality',''),player_identity_certified='NO',injury_status_certified='NO',historical_asof_certified='NO',**d))
    return out

def run(root):
    root=root.resolve()
    ledger=locate(root,'s8_22_10_7','player_and_team_manual_review.csv',SOURCE_SHA)
    audit=locate(root,'s8_22_10_17','player_identity_evidence_audit.csv')
    data=analyze(csv_rows(ledger),csv_rows(audit))
    token=hashlib.sha256((digest(ledger)+digest(audit)+'S8.22.10.18-v1').encode()).hexdigest()[:16]
    out=root/'research/p0_s8/s8_22_10_18/results'/DATE/token
    out.mkdir(parents=True,exist_ok=True)
    with (out/'name_layout_diagnostics.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=OUT_FIELDS);w.writeheader();w.writerows(data)
    counts=dict(sorted(Counter(r['diagnostic_class'] for r in data).items()))
    report=dict(milestone='S8.22.10.18',game_date=DATE,player_rows=44,source_ledger=str(ledger),source_ledger_sha256=digest(ledger),source_audit=str(audit),source_audit_sha256=digest(audit),diagnostic_counts=counts,source_name_field_available=sum(bool(r['source_name_candidate']) for r in data),sample_rows=[{'record_id':r['record_id'],'raw_name':r['raw_name'],'excerpt':r['source_excerpt'][:160],'classification':r['diagnostic_class']} for r in data[:6]],name_diagnostics_not_certification=True,player_ids_certified=0,injury_statuses_certified=0,historical_asof_certified=0,research_status='RESEARCH_ONLY',training_decision='BLOCK_TRAINING',next_action='Inspect diagnostic class distribution and source layout before changing extraction logic. Acquire authoritative player ID, status, and publication time evidence.')
    (out/'review.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('REPORT:',out/'review.json');print(json.dumps(report,indent=2,ensure_ascii=False));return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project-root',default='.');a=p.parse_args()
    try:run(Path(a.project_root))
    except (ValueError,KeyError,FileNotFoundError) as e:p.exit(2,'FAIL CLOSED: '+str(e)+'\n')
if __name__=='__main__':main()
