import csv,hashlib,json,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_7_6'))
from run_s8_22_7_6 import build_queue,validate_receipt,safe_path,main,TARGETS

@pytest.fixture
def project(tmp_path):
 rows=[]
 for d,(phase,kind) in TARGETS.items():
  n={'2023-10-24':2,'2023-11-15':8,'2024-01-15':11,'2024-06-20':0,'2026-10-10':0}[d]
  status='CANDIDATE_ANNOUNCEMENT_AGREEMENT_REVIEW_REQUIRED' if n==2 else 'INDEPENDENT_REFERENCE_MISSING' if n else 'ZERO_PROVIDER_ROWS_NEGATIVE_EVIDENCE_REVIEW_REQUIRED'
  rows.append({'date':d,'phase':phase,'provider_rows':n,'status':status})
 p=tmp_path/'coverage.json';p.write_text(json.dumps({'summary':{'milestone':'S8.22.7.5','decision':'BLOCK_TRAINING'},'dates':rows}))
 return tmp_path,p

def test_five_tasks(project):
 root,p=project;tasks=build_queue(root,p,{})
 assert len(tasks)==5 and [t['priority'] for t in tasks]==['CONTROL','P1','P2','P3','P4']
 assert all(t['source_integrity']=='NOT_SUPPLIED' for t in tasks)

def test_zero_is_not_no_game(project):
 root,p=project;tasks=build_queue(root,p,{})
 assert 'negative' in tasks[3]['required_evidence'].lower()
 assert 'preseason' in tasks[4]['required_evidence'].lower()

def test_no_certification(project):
 root,p=project;tasks=build_queue(root,p,{})
 assert all('AWAITING' in t['review_status'] or t['priority']=='CONTROL' for t in tasks)

def test_wrong_milestone(project):
 root,p=project;data=json.loads(p.read_text());data['summary']['milestone']='wrong';p.write_text(json.dumps(data))
 with pytest.raises(ValueError,match='WRONG_MILESTONE'):build_queue(root,p,{})

def test_duplicate_date(project):
 root,p=project;data=json.loads(p.read_text());data['dates'][0]=data['dates'][1];p.write_text(json.dumps(data))
 with pytest.raises(ValueError,match='DATE_SET_MISMATCH'):build_queue(root,p,{})

def test_phase_mismatch(project):
 root,p=project;data=json.loads(p.read_text());data['dates'][0]['phase']='preseason';p.write_text(json.dumps(data))
 with pytest.raises(ValueError,match='PHASE_MISMATCH'):build_queue(root,p,{})

def test_unsafe_path(tmp_path):
 for p in ['../secrets','.\\..\\x','/tmp/outside']:
  if p=='.\\..\\x':continue
  with pytest.raises(ValueError):safe_path(tmp_path,p)

def receipt(tmp_path,date='2023-11-15'):
 source=tmp_path/'source.bin';source.write_bytes(b'<html>nba schedule</html>')
 obj={'date':date,'source_url':'https://www.nba.com/schedule','evidence_path':'source.bin','sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bytes':source.stat().st_size,'retrieved_utc':'2026-10-10T00:00:00+00:00'}
 r=tmp_path/'receipt.json';r.write_text(json.dumps(obj));return r,source

def test_receipt_pass(tmp_path):
 r,_=receipt(tmp_path);assert validate_receipt(tmp_path,r,'2023-11-15')=='PASS_BYTES_ONLY'

def test_receipt_tamper(tmp_path):
 r,s=receipt(tmp_path);s.write_bytes(b'tampered');assert validate_receipt(tmp_path,r,'2023-11-15')=='SOURCE_INTEGRITY_MISMATCH'

def test_receipt_wrong_date(tmp_path):
 r,_=receipt(tmp_path);assert validate_receipt(tmp_path,r,'2024-01-15')=='DATE_MISMATCH'

def test_receipt_host_spoof(tmp_path):
 r,_=receipt(tmp_path);data=json.loads(r.read_text());data['source_url']='https://www.nba.com.evil.example/schedule';r.write_text(json.dumps(data))
 assert validate_receipt(tmp_path,r,'2023-11-15')=='NOT_OFFICIAL_NBA_URL'

def test_receipt_missing_bytes(tmp_path):
 r,s=receipt(tmp_path);s.unlink();assert validate_receipt(tmp_path,r,'2023-11-15')=='SOURCE_BYTES_MISSING'

def test_receipt_bad_timestamp(tmp_path):
 r,_=receipt(tmp_path);data=json.loads(r.read_text());data['retrieved_utc']='2026-10-10T00:00:00';r.write_text(json.dumps(data))
 assert validate_receipt(tmp_path,r,'2023-11-15')=='RETRIEVAL_TIME_INVALID'

def test_cli_writes_both_reports(project):
 root,p=project
 assert main(['--project-root',str(root),'--coverage-report','coverage.json'])==0
 folder=root/'research/p0_s8/s8_22_7_6/results'
 files=list(folder.glob('*.json'));assert len(files)==1
 data=json.loads(files[0].read_text());assert data['decision']=='BLOCK_TRAINING' and data['training_eligible'] is False
 assert len(list(folder.glob('*.csv')))==1

def test_cli_manifest_rejects_duplicates(project):
 root,p=project;manifest=root/'manifest.csv';manifest.write_text('date,receipt_path\n2023-11-15,\n2023-11-15,\n')
 with pytest.raises(SystemExit):main(['--project-root',str(root),'--coverage-report','coverage.json','--receipt-manifest','manifest.csv'])
