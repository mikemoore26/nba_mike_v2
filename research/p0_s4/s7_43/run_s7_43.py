"""S7.43 offline event identity and source-independence audit. Never promotes training."""
import argparse,csv,hashlib,json,re
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

REQ={'candidate_number','player_name','player_id','event_date','tracker_to_team','article_url','article_sha256','source_family','evidence_text','evidence_sha256','origin_candidate','destination_candidate','direction_pattern','review_status','historical_publication_verified','origin_team_verified'}
FIELDS=['candidate_number','player_name','player_id','tracker_event_date','tracker_to_team','article_url','article_sha256','source_family','evidence_type','evidence_text','evidence_sha256','origin_candidate','destination_candidate','article_event_date','date_basis','event_identity','tracker_comparison','source_independence','review_status','quality_flags','historical_publication_verified','origin_team_verified']
MONTHS='January February March April May June July August September October November December'.split()
MONTH_NUM={m.lower():i for i,m in enumerate(MONTHS,1)}

def read_rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        rd=csv.DictReader(f)
        if not rd.fieldnames or not REQ.issubset(rd.fieldnames):raise ValueError('S7.42 schema mismatch')
        rows=list(rd)
    if not rows:raise ValueError('Empty S7.42 input')
    return rows

def iso(s):
    try:return date.fromisoformat(s).isoformat()
    except ValueError:return ''

def dates_in_text(text):
    # These are mentions, NOT event dates. Never promote a date without contextual proof.
    out=set()
    for m in re.finditer(r'\b(20\d{2})-(\d{2})-(\d{2})\b',text):
        d=iso(m.group(0))
        if d:out.add(d)
    for m in re.finditer(r'\b('+'|'.join(MONTHS)+r')\s+(\d{1,2}),?\s+(20\d{2})\b',text,re.I):
        try:out.add(date(int(m.group(3)),MONTH_NUM[m.group(1).lower()],int(m.group(2))).isoformat())
        except ValueError:pass
    return sorted(out)

def approved_url(url):
    p=urlsplit(url)
    if p.scheme!='https' or p.hostname not in ('nba.com','www.nba.com') or p.username or p.password or p.port not in (None,443):raise ValueError('Non-official article URL')
    return p

def run(input_csv,output_dir,objects_dir=None):
    rows=read_rows(input_csv);seen=set();out=[];verified=set()
    for r in rows:
        if r['historical_publication_verified'].lower()!='false' or r['origin_team_verified'].lower()!='false':raise ValueError('Unexpected upstream verification flag')
        approved_url(r['article_url'])
        sha=r['article_sha256'];e=r['evidence_text'];esh=r['evidence_sha256']
        if not re.fullmatch(r'[0-9a-f]{64}',sha) or not re.fullmatch(r'[0-9a-f]{64}',esh) or hashlib.sha256(e.encode()).hexdigest()!=esh:raise ValueError('Evidence hash mismatch')
        if objects_dir is not None:
            obj=Path(objects_dir)/(sha+'.html')
            if not obj.is_file() or hashlib.sha256(obj.read_bytes()).hexdigest()!=sha:raise ValueError('Article hash mismatch')
            verified.add(sha)
        key=(r['candidate_number'],r['player_id'],r['article_url'],sha,esh)
        if key in seen:continue
        seen.add(key)
        if not iso(r['event_date']):raise ValueError('Invalid tracker event date')
        flags=set(filter(None,r.get('quality_flags','').split(';')))
        # Extracted article headlines and paragraphs do not establish the event date.
        mentions=dates_in_text(e)
        if mentions:flags.add('UNATTRIBUTED_DATE_MENTION')
        origin=r['origin_candidate'];dest=r['destination_candidate']
        if (origin and not dest) or (dest and not origin):raise ValueError('Incomplete direction')
        direction=bool(origin and dest and r['direction_pattern']!='NONE')
        if not direction:origin=dest=''
        if direction and (origin==dest or not re.fullmatch(r'[A-Z]{3}',origin) or not re.fullmatch(r'[A-Z]{3}',dest)):raise ValueError('Invalid direction')
        out.append({'candidate_number':r['candidate_number'],'player_name':r['player_name'],'player_id':r['player_id'],'tracker_event_date':r['event_date'],'tracker_to_team':r['tracker_to_team'],'article_url':r['article_url'],'article_sha256':sha,'source_family':r['source_family'],'evidence_type':r.get('evidence_type',''),'evidence_text':e,'evidence_sha256':esh,'origin_candidate':origin,'destination_candidate':dest,'article_event_date':'','date_basis':'NO_EVENT_DATE_PROOF','event_identity':'EVENT_UNRESOLVED','tracker_comparison':'','source_independence':'','review_status':'','quality_flags':';'.join(sorted(flags)),'historical_publication_verified':'false','origin_team_verified':'false'})
    groups=defaultdict(list)
    for r in out:
        if r['origin_candidate']:
            groups[(r['player_id'],r['origin_candidate'],r['destination_candidate'])].append(r)
    for r in out:
        flags=set(filter(None,r['quality_flags'].split(';')))
        if not r['origin_candidate']:
            r['tracker_comparison']='NO_DIRECTION'
            r['source_independence']='NOT_APPLICABLE'
            r['review_status']='CONTEXT_REVIEW_ONLY'
            continue
        same=groups[(r['player_id'],r['origin_candidate'],r['destination_candidate'])]
        urls={x['article_url'] for x in same};objects={x['article_sha256'] for x in same};families={x['source_family'] for x in same}
        if len(urls)==1:r['source_independence']='SINGLE_ARTICLE'
        elif len(objects)==1:r['source_independence']='SHARED_CONTENT_OBJECT'
        elif len(families)>1:r['source_independence']='MULTI_FAMILY_INDEPENDENCE_UNPROVEN'
        else:r['source_independence']='MULTI_ARTICLE_INDEPENDENCE_UNPROVEN'
        if r['tracker_to_team'] and r['destination_candidate']!=r['tracker_to_team']:
            r['tracker_comparison']='DESTINATION_MISMATCH_EVENT_UNRESOLVED'
            flags.add('TRACKER_DESTINATION_MISMATCH')
            r['review_status']='EVENT_IDENTITY_REVIEW_REQUIRED'
        else:
            r['tracker_comparison']='DESTINATION_COMPATIBLE_EVENT_UNRESOLVED'
            r['review_status']='DIRECTION_EVENT_UNRESOLVED'
        # Same player, different direction does not prove same event.
        alternatives={(x['origin_candidate'],x['destination_candidate']) for x in out if x['player_id']==r['player_id'] and x['origin_candidate'] and (x['origin_candidate'],x['destination_candidate'])!=(r['origin_candidate'],r['destination_candidate'])}
        if alternatives:flags.add('OTHER_DIRECTION_SAME_PLAYER_EVENT_UNKNOWN')
        r['quality_flags']=';'.join(sorted(flags))
    output=Path(output_dir);output.mkdir(parents=True,exist_ok=True)
    with (output/'s7_43_review.csv').open('w',encoding='utf-8',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=FIELDS);wr.writeheader();wr.writerows(out)
    counts=dict(Counter(r['review_status'] for r in out));ind=dict(Counter(r['source_independence'] for r in out))
    report={'milestone':'S7.43','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','input_rows':len(rows),'review_rows':len(out),'duplicate_rows_removed':len(rows)-len(out),'unique_source_objects_sha256_verified':len(verified),'direction_rows':sum(bool(r['origin_candidate']) for r in out),'unique_direction_relationships':len(groups),'event_dates_verified':0,'event_identity_resolved':0,'true_same_event_conflicts_verified':0,'tracker_destination_mismatches_unresolved':sum(r['tracker_comparison']=='DESTINATION_MISMATCH_EVENT_UNRESOLVED' for r in out),'independent_reports_verified':0,'status_counts':counts,'independence_counts':ind,'status_totals_reconcile':sum(counts.values())==len(out),'historical_publication_verified':False,'eligible_for_asof_training':False,'limitations':['Tracker event_date is not automatically the article transaction date','Date mentions in article evidence are not verified transaction dates','Distinct source families or URLs do not prove editorial independence','Tracker destination mismatch is not a same-event contradiction without event identity','No evidence promotion or training']}
    (output/'s7_43_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--review-csv',default='research/p0_s4/s7_42/results/s7_42_review.csv');p.add_argument('--objects-dir',default='research/p0_s4/s7_38/results/objects');p.add_argument('--output-dir',default='research/p0_s4/s7_43/results');a=p.parse_args()
    try:print(json.dumps(run(a.review_csv,a.output_dir,a.objects_dir),indent=2))
    except (ValueError,OSError) as e:print(json.dumps({'milestone':'S7.43','status':'FAILED_CLOSED','decision':'BLOCK_TRAINING','error':str(e)}));raise SystemExit(1)
if __name__=='__main__':main()
