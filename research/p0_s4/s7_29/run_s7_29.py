"""S7.29: NBA player-directory exact-ID candidates; no historical membership assertions."""
import argparse,csv,hashlib,json,re,unicodedata
from collections import defaultdict,Counter
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen

ENDPOINT='https://stats.nba.com/stats/commonallplayers'
FIELDS=['candidate_number','event_date','player_name','player_id','identity_status','identity_evidence','to_team','from_team','review_reason','source_sha256','directory_sha256','evidence_class']

def normalized(s):
 s=unicodedata.normalize('NFKD',str(s).replace('’',"'").replace('‘',"'"))
 return re.sub(r'[^a-z0-9]','', ''.join(c for c in s if not unicodedata.combining(c)).lower())

def parse_directory(raw):
 payload=json.loads(raw)
 tables=payload.get('resultSets',payload.get('resultSet',[]))
 if isinstance(tables,dict):tables=[tables]
 for table in tables:
  if str(table.get('name','')).lower()!='commonallplayers':continue
  headers=table.get('headers',[]);rows=table.get('rowSet',[])
  if 'PERSON_ID' not in headers or 'DISPLAY_FIRST_LAST' not in headers or not isinstance(rows,list):raise ValueError('Invalid CommonAllPlayers schema')
  ids=defaultdict(set)
  for row in rows:
   if len(row)!=len(headers):raise ValueError('Directory column mismatch')
   obj=dict(zip(headers,row));pid=str(obj['PERSON_ID']).strip();name=str(obj['DISPLAY_FIRST_LAST']).strip()
   if not pid.isdigit() or not name or not normalized(name):raise ValueError('Invalid directory identity')
   ids[normalized(name)].add(pid)
  if not ids:raise ValueError('Empty directory is not evidence of zero players')
  return ids,sum(len(v) for v in ids.values())
 raise ValueError('Missing CommonAllPlayers result set')

def fetch(season='2025-26',timeout=20,opener=urlopen):
 if not re.fullmatch(r'20\d\d-\d\d',season) or int(season[-2:])!=(int(season[:4])+1)%100:raise ValueError('Invalid season')
 url=ENDPOINT+'?'+urlencode({'LeagueID':'00','Season':season,'IsOnlyCurrentSeason':'0'})
 request=Request(url,headers={'User-Agent':'Mozilla/5.0 (NBA_MIKE research)','Referer':'https://www.nba.com/','Origin':'https://www.nba.com','Accept':'application/json'})
 with opener(request,timeout=timeout) as response:raw=response.read(8_000_001)
 if len(raw)>8_000_000:raise ValueError('Directory response too large')
 return raw,url

def resolve(review_csv,source_html,directory_raw,output_dir,directory_url='OFFLINE_FIXTURE'):
 source=Path(source_html).read_bytes();source_sha=hashlib.sha256(source).hexdigest()
 if b'<html' not in source[:2000].lower() and b'<!doctype html' not in source[:2000].lower():raise ValueError('Invalid original source HTML')
 ids,directory_count=parse_directory(directory_raw)
 directory_sha=hashlib.sha256(directory_raw).hexdigest()
 with Path(review_csv).open(encoding='utf-8-sig',newline='') as f:
  reader=csv.DictReader(f);required={'candidate_number','event_date','player_name','source_sha256','review_reason','to_team','from_team'}
  if not reader.fieldnames or not required.issubset(reader.fieldnames):raise ValueError('Invalid S7.28 review CSV')
  candidates=list(reader)
 if not candidates:raise ValueError('Empty candidate file is not successful identity coverage')
 out=[];counts=Counter()
 for row in candidates:
  if row['source_sha256']!=source_sha:raise ValueError('S7.28 source provenance mismatch')
  name=row['player_name'].strip();prior=row['review_reason'];nonplayer='NON_PLAYER_ASSET' in prior or not name
  matched=ids.get(normalized(name),set()) if not nonplayer else set()
  if nonplayer:status='NON_PLAYER_ASSET';pid=''
  elif len(matched)==1:status='EXACT_UNIQUE_ID_CANDIDATE';pid=next(iter(matched))
  elif len(matched)>1:status='AMBIGUOUS_ID';pid=''
  else:status='UNMATCHED_NAME';pid=''
  counts[status]+=1
  out.append({'candidate_number':row['candidate_number'],'event_date':row['event_date'],'player_name':name,'player_id':pid,'identity_status':status,'identity_evidence':'NBA_STATS_COMMON_ALL_PLAYERS_EXACT_NAME' if pid else '', 'to_team':row['to_team'],'from_team':row['from_team'],'review_reason':prior,'source_sha256':source_sha,'directory_sha256':directory_sha,'evidence_class':'IDENTITY_CANDIDATE_ONLY'})
 dest=Path(output_dir);dest.mkdir(parents=True,exist_ok=True);rawdir=dest/'objects';rawdir.mkdir(exist_ok=True)
 (rawdir/(directory_sha+'.json')).write_bytes(directory_raw)
 with (dest/'s7_29_identity_candidates.csv').open('w',encoding='utf-8',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(out)
 report={'milestone':'S7.29','status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','source_sha256':source_sha,'directory_sha256':directory_sha,'directory_url':directory_url,'retrieved_utc':datetime.now(timezone.utc).isoformat(),'directory_id_count':directory_count,'input_candidates':len(out),'exact_unique_id_candidates':counts['EXACT_UNIQUE_ID_CANDIDATE'],'ambiguous_ids':counts['AMBIGUOUS_ID'],'unmatched_names':counts['UNMATCHED_NAME'],'non_player_assets':counts['NON_PLAYER_ASSET'],'qualified_s726_events':0,'verified_injury_assignments':0,'historical_publication_verified':False,'eligible_for_asof_training':False,'limitations':['Exact name matches identify candidates, not verified trade participation','Directory retrieved now does not prove historical team membership or source publication','No automatic promotion to S7.26, S7.24, or S7.23','Unmatched and ambiguous identities remain unresolved']}
 (dest/'s7_29_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--review-csv',default='research/p0_s4/s7_28/results/s7_28_review.csv');p.add_argument('--source-html');p.add_argument('--directory-json');p.add_argument('--season',default='2025-26');p.add_argument('--output-dir',default='research/p0_s4/s7_29/results');a=p.parse_args()
 try:
  if a.source_html:html=a.source_html
  else:
   paths=list(Path('research/p0_s4/s7_27/results/objects').glob('*.html'))
   if len(paths)!=1:raise ValueError('Specify --source-html if there are zero/multiple HTML snapshots')
   html=paths[0]
  if a.directory_json:raw=Path(a.directory_json).read_bytes();url='OFFLINE:'+str(a.directory_json)
  else:raw,url=fetch(a.season)
  print(json.dumps(resolve(a.review_csv,html,raw,a.output_dir,url),indent=2))
 except (ValueError,OSError,KeyError,json.JSONDecodeError) as exc:
  print(json.dumps({'milestone':'S7.29','status':'FAILED_CLOSED','decision':'BLOCK_TRAINING','error':str(exc)}));raise SystemExit(1)
if __name__=='__main__':main()
