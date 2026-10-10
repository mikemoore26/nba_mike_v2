import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

SCRIPT = Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_7_9/run_s8_22_7_9.py'
spec=importlib.util.spec_from_file_location('directory_verifier',SCRIPT)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def fixture(tmp_path):
    root=tmp_path
    ev=root/'evidence';ev.mkdir()
    raw=json.dumps({'data':[{'id':1,'abbreviation':'ATL'},{'id':20,'abbreviation':'NYK'}]}).encode()
    (ev/'source.bin').write_bytes(raw)
    receipt={'source_url':'https://api.balldontlie.io/v1/teams','sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'evidence_path':'evidence/source.bin','retrieved_utc':'2026-10-10T00:00:00Z'}
    (ev/'receipt.json').write_text(json.dumps(receipt))
    with (root/'crosswalk.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=sorted(m.REQUIRED));w.writeheader()
        for i,a in [(1,'ATL'),(20,'NYK')]:w.writerow({'provider_team_id':i,'nba_abbreviation':a})
    matches=[{'home_team':'ATL','away_team':'NYK'} for _ in range(8)]
    (root/'comparison.json').write_text(json.dumps({'milestone':'S8.22.7.8','date':'2023-11-15','matched_games':8,'issues':[],'matches':matches}))
    return root,ev,receipt

def test_valid(tmp_path):
    root,_,_=fixture(tmp_path)
    r=m.run(root,'evidence/receipt.json','crosswalk.csv','comparison.json')
    assert r['team_identity_verified_from_directory'] and r['verified_rows']==2
    assert r['decision']=='BLOCK_TRAINING' and not r['training_eligible']

def test_bad_hash(tmp_path):
    root,ev,_=fixture(tmp_path)
    (ev/'source.bin').write_bytes(b'{}')
    with pytest.raises(ValueError,match='integrity'):m.verify_receipt(root,'evidence/receipt.json')

def test_bad_url(tmp_path):
    root,ev,receipt=fixture(tmp_path)
    receipt['source_url']='https://example.com/v1/teams'
    (ev/'receipt.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='endpoint'):m.verify_receipt(root,'evidence/receipt.json')

def test_abbreviation_conflict(tmp_path):
    root,ev,_=fixture(tmp_path)
    p=root/'crosswalk.csv'; p.write_text(p.read_text().replace('ATL','BOS'))
    r=m.run(root,'evidence/receipt.json','crosswalk.csv','comparison.json')
    assert not r['team_identity_verified_from_directory']
    assert any('ABBREVIATION_CONFLICT' in x for x in r['issues'])

def test_missing_directory_team(tmp_path):
    root,ev,_=fixture(tmp_path)
    p=root/'crosswalk.csv';p.write_text(p.read_text().replace('20,NYK','22,NYK').replace('20,NYK','22,NYK'))
    # CSV writer orders columns alphabetically; replace the ID in the corresponding row instead.
    rows=list(csv.DictReader(p.open()))
    rows[1]['provider_team_id']='22'
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=sorted(m.REQUIRED));w.writeheader();w.writerows(rows)
    r=m.run(root,'evidence/receipt.json','crosswalk.csv','comparison.json')
    assert not r['team_identity_verified_from_directory']

def test_duplicate_crosswalk(tmp_path):
    root,ev,_=fixture(tmp_path)
    p=root/'crosswalk.csv';p.write_text(p.read_text()+p.read_text().splitlines()[-1]+'\n')
    r=m.run(root,'evidence/receipt.json','crosswalk.csv','comparison.json')
    assert any('DUPLICATE' in x for x in r['issues'])

def test_incomplete_directory(tmp_path):
    root,ev,receipt=fixture(tmp_path)
    raw=json.dumps({'data':[{'id':1,'abbreviation':'ATL'}],'meta':{'next_cursor':123}}).encode()
    (ev/'source.bin').write_bytes(raw)
    receipt['sha256']=hashlib.sha256(raw).hexdigest();receipt['bytes']=len(raw)
    (ev/'receipt.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='pagination'):m.verify_receipt(root,'evidence/receipt.json')

def test_escape_path(tmp_path):
    with pytest.raises(ValueError,match='escapes'):m.safe_path(tmp_path,'../outside')

def test_wrong_comparison(tmp_path):
    root,_,_=fixture(tmp_path)
    p=root/'comparison.json';p.write_text(p.read_text().replace('S8.22.7.8','S8.22.7.7'))
    with pytest.raises(ValueError,match='Wrong comparison'):m.run(root,'evidence/receipt.json','crosswalk.csv','comparison.json')
