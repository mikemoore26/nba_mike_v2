import csv,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/p0_s4/s7_49'))
from run_s7_49 import direction,stage,check_row,process

def test_acquisition():assert direction('Atlanta Hawks Acquire Buddy Hield from Golden State','Buddy Hield','GSW','ATL')=='GRAMMATICAL_DIRECTION_CANDIDATE'
def test_reverse():assert direction('Golden State Warriors acquire Buddy Hield from Atlanta Hawks','Buddy Hield','GSW','ATL')!='GRAMMATICAL_DIRECTION_CANDIDATE'
def test_no_player():assert direction('Atlanta Hawks acquire someone from Golden State','Buddy Hield','GSW','ATL')=='NO_DIRECTION_PROPOSAL'
def test_cooccurrence():assert direction('Buddy Hield played for Golden State. Atlanta Hawks watched.','Buddy Hield','GSW','ATL')=='COOCCURRENCE_ONLY'
def test_sent():assert direction('Golden State Warriors traded Buddy Hield to Atlanta Hawks','Buddy Hield','GSW','ATL')=='GRAMMATICAL_DIRECTION_CANDIDATE'
def test_pending():assert stage('This transaction is pending league approval')=='PENDING_APPROVAL'
def test_reported():assert stage('Reportedly agreed to the deal')=='REPORTED_OR_AGREED'
def test_announced():assert stage('The Hawks officially acquired him')=='ANNOUNCED_LANGUAGE_UNVERIFIED'
def test_stage_unknown():assert stage('Basketball news')=='STAGE_UNKNOWN'
def test_missing_mapping(tmp_path):
 r=check_row({'player_name':'Anthony Davis','hash_verified':'false','archive_original_url_match':'false'},tmp_path)
 assert r['mapping_issue']=='MISSING_PLAYER_OR_TEAM_MAPPING'
def test_no_promotion(tmp_path):
 r=check_row({'hash_verified':'false'},tmp_path)
 assert r['eligible_for_asof_training']=='false' and r['historical_publication_verified']=='false'
def test_bad_sha(tmp_path):
 r=check_row({'hash_verified':'true','archive_original_url_match':'true','captured_sha256':'bad'},tmp_path)
 assert r['integrity_status']=='INVALID_SHA'
def test_missing_object(tmp_path):
 r=check_row({'hash_verified':'true','archive_original_url_match':'true','captured_sha256':'a'*64},tmp_path)
 assert r['integrity_status']=='OBJECT_MISSING'
def test_hash_mismatch(tmp_path):
 (tmp_path/('a'*64+'.html')).write_text('fake')
 r=check_row({'hash_verified':'true','archive_original_url_match':'true','captured_sha256':'a'*64},tmp_path)
 assert r['integrity_status']=='HASH_MISMATCH'
def test_verified_object(tmp_path):
 blob=b'<html><h1>Atlanta Hawks acquire Buddy Hield from Golden State</h1></html>'
 sha=hashlib.sha256(blob).hexdigest();(tmp_path/(sha+'.html')).write_bytes(blob)
 r=check_row({'hash_verified':'true','archive_original_url_match':'true','captured_sha256':sha,'player_name':'Buddy Hield','origin_candidate':'GSW','destination_candidate':'ATL','source_locator':'h1:0','best_location':'HEADING','best_excerpt':'Atlanta Hawks acquire Buddy Hield from Golden State'},tmp_path)
 assert r['direction_status']=='GRAMMATICAL_DIRECTION_CANDIDATE' and r['eligible_for_asof_training']=='false'
def test_report_reconciles(tmp_path):
 inp=tmp_path/'input.csv';out=tmp_path/'output';objects=tmp_path/'objects';objects.mkdir()
 with inp.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['hash_verified','archive_original_url_match']);w.writeheader();w.writerow({'hash_verified':'false','archive_original_url_match':'false'})
 report=process(inp,objects,out)
 assert report['review_rows']==sum(report['direction_status_counts'].values())==sum(report['integrity_status_counts'].values())==1
 assert report['eligible_for_asof_training'] is False
