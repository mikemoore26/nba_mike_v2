"""S7.49: conservative offline archived-claim direction audit. Research only."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'research/p0_s4'
INPUT = BASE / 's7_48/results/s7_48_review.csv'
OBJECTS = BASE / 's7_46/results/archive_objects'
OUTPUT = Path(__file__).resolve().parent / 'results'
FIELDS = ['player_name','origin_candidate','destination_candidate','article_url','archive_timestamp','captured_sha256','source_locator','best_location','best_excerpt','recovery_status','integrity_status','content_provenance','direction_status','transaction_stage','tracker_alignment','source_independence','mapping_issue','historical_publication_verified','event_date_verified','eligible_for_asof_training','review_reason']
ALIASES = {'ATL':['atlanta','hawks'],'GSW':['golden state','warriors'],'CHA':['charlotte','hornets'],'WAS':['washington','wizards'],'ORL':['orlando','magic'],'LAC':['los angeles clippers','la clippers','clippers'],'IND':['indiana','pacers'],'DAL':['dallas','mavericks']}

def load(path):
    with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def phrase(s,term):return bool(term and re.search(r'(?<!\w)'+re.escape(term)+r'(?!\w)',s,re.I))

def alias_regex(code):
    words=ALIASES.get((code or '').upper(),[])
    return '(?:'+ '|'.join(re.escape(x) for x in words)+')' if words else '(?!)'

def stage(text):
    if re.search(r'\b(pending|not yet|subject to|awaiting)\b.{0,70}\b(approval|approved|league|physical)|\bnot yet (?:been )?approved\b',text,re.I):return 'PENDING_APPROVAL'
    if re.search(r'\b(reportedly|reports? say|according to|agreed to|agreement in principle|expected to)\b',text,re.I):return 'REPORTED_OR_AGREED'
    if re.search(r'\b(officially|announced|has acquired|have acquired|acquires|acquired|completed)\b',text,re.I):return 'ANNOUNCED_LANGUAGE_UNVERIFIED'
    return 'STAGE_UNKNOWN'

def direction(text,player,origin,dest):
    """Require a grammatical direction expression, not mere co-occurrence."""
    if not all((player,origin,dest)) or not phrase(text,player):return 'NO_DIRECTION_PROPOSAL'
    p=re.escape(player);o=alias_regex(origin);d=alias_regex(dest)
    patterns=[
        rf'{d}.{{0,90}}\b(?:acquire[ds]?|obtains?|receive[ds]?)\b.{{0,100}}{p}.{{0,90}}\bfrom\b\s+(?:the\s+)?{o}',
        rf'{d}.{{0,90}}\b(?:acquire[ds]?|obtains?|receive[ds]?)\b.{{0,100}}{p}.{{0,100}}\bfrom\b\s+(?:the\s+)?{o}',
        rf'{o}.{{0,90}}\b(?:trade[ds]?|send[st]?)\b.{{0,100}}{p}.{{0,90}}\bto\b\s+(?:the\s+)?{d}',
        rf'{p}.{{0,100}}\b(?:traded|sent|dealt)\b.{{0,90}}\bfrom\b\s+(?:the\s+)?{o}.{{0,90}}\bto\b\s+(?:the\s+)?{d}',
        rf'{p}.{{0,80}}\b(?:traded|sent|dealt)\b.{{0,90}}\bto\b\s+(?:the\s+)?{d}.{{0,90}}\bfrom\b\s+(?:the\s+)?{o}',
    ]
    if any(re.search(pat,text,re.I) for pat in patterns):return 'GRAMMATICAL_DIRECTION_CANDIDATE'
    if any(phrase(text,x) for x in ALIASES.get(origin,[])) and any(phrase(text,x) for x in ALIASES.get(dest,[])):
        return 'COOCCURRENCE_ONLY'
    return 'NO_GRAMMATICAL_DIRECTION'

def check_row(src,objects):
    r={k:src.get(k,'') for k in FIELDS}
    r.update(historical_publication_verified='false',event_date_verified='false',eligible_for_asof_training='false',source_independence='NOT_ESTABLISHED',tracker_alignment='NOT_VERIFIED',transaction_stage='NOT_EVALUATED',direction_status='NOT_EVALUATED')
    player=src.get('player_name','');origin=src.get('origin_candidate','');dest=src.get('destination_candidate','')
    if not player or not origin or not dest:r['mapping_issue']='MISSING_PLAYER_OR_TEAM_MAPPING'
    sha=src.get('captured_sha256','')
    if src.get('hash_verified')!='true' or src.get('archive_original_url_match')!='true':
        r.update(integrity_status='UPSTREAM_NOT_VERIFIED',review_reason='Upstream hash or original URL check not confirmed');return r
    if not re.fullmatch('[0-9a-f]{64}',sha):
        r.update(integrity_status='INVALID_SHA',review_reason='Invalid object digest');return r
    path=objects/(sha+'.html')
    if not path.is_file():
        r.update(integrity_status='OBJECT_MISSING',review_reason='Archived HTML object not present');return r
    blob=path.read_bytes()
    if hashlib.sha256(blob).hexdigest()!=sha:
        r.update(integrity_status='HASH_MISMATCH',review_reason='Object hash mismatch');return r
    r['integrity_status']='SHA256_MATCH'
    locator=src.get('source_locator','');kind=src.get('best_location','');excerpt=src.get('best_excerpt','')
    if not excerpt or not locator:
        r.update(content_provenance='NO_LOCALIZED_CONTENT',direction_status='NO_EXCERPT',review_reason='No localized source excerpt');return r
    if kind.startswith('JSON_LD_'):
        r['content_provenance']='STRUCTURED_METADATA_REVIEW_ONLY'
    elif kind in ('HEADING','PARAGRAPH','TITLE'):
        r['content_provenance']='ARTICLE_TEXT_REVIEW_ONLY'
    else:r['content_provenance']='OTHER_HTML_REVIEW_ONLY'
    r['direction_status']=direction(excerpt,player,origin,dest)
    r['transaction_stage']=stage(excerpt)
    if re.search(rb'web\.archive\.org|__wm|wm-ipp',blob,re.I):
        r['content_provenance']+=';REPLAY_MARKERS_PRESENT'
    r['review_reason']='Archive-reported capture time, source authenticity, transaction completion, and independent publication not established'
    return r

def process(input_path=INPUT,objects_dir=OBJECTS,output_dir=OUTPUT):
    rows_in=load(input_path);out=[check_row(r,objects_dir) for r in rows_in]
    output_dir.mkdir(parents=True,exist_ok=True)
    with (output_dir/'s7_49_review.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(out)
    report={'milestone':'S7.49','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','input_rows':len(rows_in),'review_rows':len(out),'integrity_status_counts':dict(Counter(r['integrity_status'] for r in out)),'direction_status_counts':dict(Counter(r['direction_status'] for r in out)),'transaction_stage_counts':dict(Counter(r['transaction_stage'] for r in out)),'mapping_issues':sum(bool(r['mapping_issue']) for r in out),'grammatical_direction_candidates':sum(r['direction_status']=='GRAMMATICAL_DIRECTION_CANDIDATE' for r in out),'independent_reports_verified':0,'historical_publication_verified':False,'event_dates_verified':0,'eligible_for_asof_training':False,'limitations':['Only previously captured SHA-verified bytes; no network requests','Best excerpt is truncated upstream to 450 characters; not a complete article proof','Archived HTML replay or syndicated structured metadata can mislead extraction','Grammatical direction is still a review candidate, not a completed transaction','No independent archive timestamp attestation or source-family independence established','Historical roster, transaction chronology and training remain blocked']}
    (output_dir/'s7_49_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=INPUT);p.add_argument('--objects',type=Path,default=OBJECTS);p.add_argument('--output-dir',type=Path,default=OUTPUT);a=p.parse_args();print(json.dumps(process(a.input,a.objects,a.output_dir),indent=2,ensure_ascii=False))
