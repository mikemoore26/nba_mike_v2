"""S7.27: snapshot official NBA 2025-26 trade tracker; conservative event candidates only."""
import argparse,csv,hashlib,json,re,urllib.request
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path

URL='https://www.nba.com/news/2025-26-nba-trade-tracker'
FIELDS=['event_date','destination_team_text','player_text','source_url','source_sha256','retrieved_utc','evidence_class','review_reason']
class Text(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.hidden=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','noscript'):self.hidden+=1
        if tag in ('p','h2','h3','h4','li','br'):self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style','noscript') and self.hidden:self.hidden-=1
        if tag in ('p','h2','h3','h4','li'):self.parts.append('\n')
    def handle_data(self,data):
        if not self.hidden:self.parts.append(data)

def extract_candidates(raw,sha,retrieved):
    parser=Text();parser.feed(raw.decode('utf-8','replace'))
    lines=[re.sub(r'\s+',' ',x).strip() for x in ''.join(parser.parts).splitlines()]
    lines=[x for x in lines if x]
    # These are raw textual candidates only; neither player IDs nor event effective dates are inferred.
    date_marker=re.compile(r'\((Jan\.?|Feb\.?|Mar\.?|Apr\.?|May|Jun\.?|Jul\.?|Aug\.?|Sep\.?|Oct\.?|Nov\.?|Dec\.?)\s+\d{1,2}\)',re.I)
    receive=re.compile(r'^(?:[A-Z][\w .’\-]+\s+)?receives?:$',re.I)
    candidates=[];section=''
    for i,line in enumerate(lines):
        if date_marker.search(line):section=line[:180]
        if receive.match(line):
            for value in lines[i+1:i+9]:
                if value.lower().startswith(('official release','official releases')) or receive.match(value):break
                if re.search(r'\b(?:pick|cash|consideration|rights|swap)\b',value,re.I):continue
                if len(value)>100 or len(value)<4:continue
                candidates.append({'event_date':section,'destination_team_text':line,'player_text':value,'source_url':URL,'source_sha256':sha,'retrieved_utc':retrieved,'evidence_class':'UNVERIFIED_TEXT_CANDIDATE','review_reason':'No stable player ID, explicit team normalization or independently verified effective date'})
    return candidates

def run(output_dir,offline_file=None):
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    if offline_file:raw=Path(offline_file).read_bytes();mode='OFFLINE_INPUT'
    else:
        req=urllib.request.Request(URL,headers={'User-Agent':'NBA-MIKE-Research/1.0 (+research; no automated retries)','Accept':'text/html'})
        with urllib.request.urlopen(req,timeout=25) as resp:
            if resp.status!=200:raise ValueError(f'HTTP {resp.status}')
            raw=resp.read(8_000_001)
        if len(raw)>8_000_000:raise ValueError('Source exceeds maximum size')
        mode='LIVE_FETCH'
    if not raw or b'<html' not in raw[:2000].lower() and b'<!doctype html' not in raw[:2000].lower():raise ValueError('Not a recognizable HTML document')
    sha=hashlib.sha256(raw).hexdigest();retrieved=datetime.now(timezone.utc).isoformat()
    obj=out/'objects';obj.mkdir(exist_ok=True);path=obj/(sha+'.html')
    if path.exists() and path.read_bytes()!=raw:raise ValueError('Immutable object collision')
    if not path.exists():path.write_bytes(raw)
    candidates=extract_candidates(raw,sha,retrieved)
    with (out/'s7_27_candidates.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(candidates)
    report={'milestone':'S7.27','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','source_url':URL,'source_sha256':sha,'retrieved_utc':retrieved,'fetch_mode':mode,'source_bytes':len(raw),'raw_text_candidates':len(candidates),'qualified_s726_events':0,'date_specific_verified_assignments':0,'historical_publication_verified':False,'eligible_for_asof_training':False,'limitations':['Page retrieved now does not prove historical availability','Candidates may include HTML navigation/noise and are not authenticated transactions','Stable player IDs, team normalization, event date and source publication provenance not established','No automatic export into S7.26 or S7.23']}
    (out/'s7_27_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',default='research/p0_s4/s7_27/results');p.add_argument('--offline-file');a=p.parse_args()
    try:print(json.dumps(run(a.output_dir,a.offline_file),indent=2))
    except Exception as exc:
        print(json.dumps({'milestone':'S7.27','status':'FAILED_CLOSED','decision':'BLOCK_TRAINING','error':str(exc)}));raise SystemExit(1)
if __name__=='__main__':main()
