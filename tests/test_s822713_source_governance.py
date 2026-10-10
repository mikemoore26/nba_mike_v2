import importlib.util
from pathlib import Path
import json

p=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_7_13/run_s8_22_7_13.py'
spec=importlib.util.spec_from_file_location('audit13',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def fixture():
    games=[{'away_team':a,'home_team':h} for a,h in [('DAL','WAS'),('NYK','ATL'),('BOS','PHI'),('MIL','TOR'),('ORL','CHI'),('MIN','PHX'),('SAC','LAL'),('CLE','POR')]]
    gov={'date':'2023-11-15','game_agreement':'PASS','issues':[],'reconstructed_matches':games}
    gb=json.dumps(gov).encode(); raw=b'<html>sample</html>'
    intake={'date':'2023-11-15','source_sha256':m.sha(raw),'source_bytes':len(raw),'source_url':m.EXPECTED_URL,'status':'CANDIDATE_INDEPENDENT_SLATE_CORROBORATION_REVIEW_REQUIRED','issues':[],'matchups_agree':True,'independent_listing_games':8,'prior_official_games':8,'matched_pairs':[g['away_team']+'@'+g['home_team'] for g in games],'prior_report_sha256':m.sha(gb),'source_retrieved_utc':'2026-10-10T02:15:00Z'}
    return raw,intake,gov,gb

def run(raw,intake,gov,gb):return m.review(raw,intake,gov,json.dumps(intake).encode(),gb)

def test_clean_candidate_stays_blocked():
    raw,i,g,gb=fixture();r=run(raw,i,g,gb)
    assert r['issues']==[] and r['decision']=='BLOCK_TRAINING'
    assert r['retrospective_date_completeness']=='NOT_CERTIFIED'
    assert r['checks']['upstream_editorial_independence']=='NOT_VERIFIED'

def test_modified_source_fails():
    raw,i,g,gb=fixture();assert 'SOURCE_HASH_MISMATCH' in run(raw+b'x',i,g,gb)['issues']

def test_wrong_prior_report_fails():
    raw,i,g,gb=fixture();assert 'PRIOR_REPORT_HASH_MISMATCH' in run(raw,i,g,gb+b' ')['issues']

def test_mismatched_game_fails():
    raw,i,g,gb=fixture();i['matched_pairs'][0]='AAA@BBB';assert 'MATCHUPS_DIFFER_FROM_PRIOR' in run(raw,i,g,gb)['issues']

def test_wrong_date_fails():
    raw,i,g,gb=fixture();i['date']='2024-01-15';assert 'DATE_MISMATCH' in run(raw,i,g,gb)['issues']

def test_invalid_retrieval_time_fails():
    raw,i,g,gb=fixture();i['source_retrieved_utc']='not a timestamp';assert 'INVALID_RETRIEVAL_UTC' in run(raw,i,g,gb)['issues']
