"""S8.22.10.19: read-only coordinate-aware local name corroboration."""
import argparse,csv,hashlib,json,re,unicodedata
from collections import Counter
from pathlib import Path
DATE='2023-11-15'
LEDGER_SHA='70cc499b1c35cd65cde2ce0c8836e1db13e9194a43ac290450755f067ff3c3db'
AUDIT_SHA='5c5e3471673d639e0cd1e6cb97dcf747157eaa7bfe274edd29c32cf8e76ab092'
COORD=re.compile(r'^\s*(?:\d+(?:\.\d+)?):')
FIELDS=['record_id','raw_name','original_excerpt','reconstructed_excerpt','name_tokens','excerpt_tokens','match_class','match_reason','local_name_corrob','player_identity_certified','injury_status_certified','historical_asof_certified']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p):
    with p.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames:raise ValueError('Missing CSV header: '+str(p))
        return list(reader)
def locate(root,milestone,filename,expected):
    paths=sorted((root/'research/p0_s8'/milestone/'results'/DATE).glob('*/'+filename))
    matched=[p for p in paths if sha(p)==expected]
    if len(matched)!=1:raise ValueError(f'Expected one SHA-matched {filename}; got {len(matched)}')
    return matched[0]
def reconstruct(excerpt):
    # Coordinates are metadata only at the beginning of pipe-delimited chunks.
    return ' '.join(COORD.sub('',piece).strip() for piece in (excerpt or '').split('|') if COORD.sub('',piece).strip())
def tokens(value):
    value=unicodedata.normalize('NFKC',value or '').casefold()
    # Preserve accents as letters; punctuation separates tokens.
    return re.findall(r'[^\W_]+',value,flags=re.UNICODE)
def contiguous(hay,needle):
    return bool(needle) and any(hay[i:i+len(needle)]==needle for i in range(len(hay)-len(needle)+1))
def classify(name,excerpt):
    clean=reconstruct(excerpt);nt=tokens(name);et=tokens(clean)
    if not nt:return clean,'EMPTY_NAME','Candidate name missing',False
    if not et:return clean,'EMPTY_EXCERPT','No usable extracted text',False
    if contiguous(et,nt):return clean,'LOCAL_NAME_MATCH','Name tokens contiguous after coordinate removal',True
    # Last, First -> First Last is common, but do not match separated/noncontiguous words.
    if ',' in name and len(nt)>=2:
        parts=name.split(',',1);left=tokens(parts[0]);right=tokens(parts[1]);reordered=right+left
        if left and right and contiguous(et,reordered):return clean,'LOCAL_NAME_REORDERED','Comma-separated name found in given-first order',True
    return clean,'NO_LOCAL_NAME_MATCH','No contiguous exact token sequence',False
def analyze(ledger,audit):
    players=[r for r in ledger if r.get('record_type')=='PLAYER']
    if len(ledger)!=54 or len(players)!=44 or len(audit)!=44:raise ValueError('Expected 54 ledger rows and 44 player rows')
    source={r['record_id']:r for r in players}
    if len(source)!=44 or len({r['record_id'] for r in audit})!=44 or {r['record_id'] for r in audit}!=set(source):raise ValueError('Duplicate/mismatched record IDs')
    result=[]
    for a in audit:
        s=source[a['record_id']];name=s.get('name_or_notice_candidate','');excerpt=s.get('pdf_context_excerpt','')
        if a.get('raw_name')!=name or a.get('source_excerpt')!=excerpt[:600]:raise ValueError('S8.22.10.18 source mismatch: '+a['record_id'])
        clean,klass,why,matched=classify(name,excerpt)
        result.append(dict(record_id=a['record_id'],raw_name=name,original_excerpt=excerpt,reconstructed_excerpt=clean,name_tokens='|'.join(tokens(name)),excerpt_tokens='|'.join(tokens(clean)),match_class=klass,match_reason=why,local_name_corrob='YES' if matched else 'NO',player_identity_certified='NO',injury_status_certified='NO',historical_asof_certified='NO'))
    return result
def run(root):
    root=root.resolve();ledger=locate(root,'s8_22_10_7','player_and_team_manual_review.csv',LEDGER_SHA)
    audit=locate(root,'s8_22_10_18','name_layout_diagnostics.csv',AUDIT_SHA)
    rows=analyze(readcsv(ledger),readcsv(audit));token=hashlib.sha256((sha(ledger)+sha(audit)+'S8.22.10.19-v1').encode()).hexdigest()[:16]
    out=root/'research/p0_s8/s8_22_10_19/results'/DATE/token;out.mkdir(parents=True,exist_ok=True)
    with (out/'name_corroboration.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(rows)
    counts=dict(sorted(Counter(r['match_class'] for r in rows).items()))
    report=dict(milestone='S8.22.10.19',game_date=DATE,source_ledger=str(ledger),source_ledger_sha256=sha(ledger),source_diagnostic=str(audit),source_diagnostic_sha256=sha(audit),player_rows=44,team_notices_excluded=10,match_counts=counts,locally_corrob=sum(r['local_name_corrob']=='YES' for r in rows),unmatched=sum(r['local_name_corrob']=='NO' for r in rows),sample_rows=[dict(record_id=r['record_id'],raw_name=r['raw_name'],match_class=r['match_class'],reconstructed_excerpt=r['reconstructed_excerpt'][:180]) for r in rows[:6]],player_ids_certified=0,injury_statuses_certified=0,historical_asof_certified=0,research_status='RESEARCH_ONLY',training_decision='BLOCK_TRAINING',note='Local excerpt name corroboration only. Original evidence unchanged. No independent identity/status/as-of certification.')
    (out/'review.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('REPORT:',out/'review.json');print(json.dumps(report,indent=2,ensure_ascii=False));return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');args=p.parse_args()
    try:run(Path(args.project_root))
    except (ValueError,KeyError,FileNotFoundError) as e:p.exit(2,'FAIL CLOSED: '+str(e)+'\n')
