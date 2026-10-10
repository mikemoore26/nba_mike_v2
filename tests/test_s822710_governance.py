import csv
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_7_10'))
from run_s8_22_7_10 import audit

D = Path(__file__).resolve().parent

def fixture(tmp_path):
    root=tmp_path
    def write(path, content):
        p=root/path;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(content if isinstance(content,bytes) else json.dumps(content).encode());return path
    source=b'official archived bytes'
    write('official.bin',source)
    digest=hashlib.sha256(source).hexdigest()
    write('official_receipt.json',{'date':'2023-11-15','source_url':'https://www.nba.com/games?date=2023-11-15','sha256':digest,'bytes':len(source),'evidence_path':'official.bin'})
    games=[];provider=[];mappings=[];prior=[]
    for i in range(8):
        h=f'H{i}';a=f'A{i}'
        games.append({'official_nba_game_id':str(i),'home_team':h,'away_team':a,'tipoff_utc':'2023-11-16T00:00:00Z'})
        provider.append({'provider_game_id':str(i),'game_date':'2023-11-15','home_provider_team_id':str(i*2),'away_provider_team_id':str(i*2+1),'tipoff_utc':'2023-11-16T00:00:00+00:00'})
        prior.append({'provider_game_id':str(i),'official_nba_game_id':str(i)})
        for tid,ab in ((i*2,h),(i*2+1,a)):
            mappings.append({'provider_team_id':str(tid),'nba_abbreviation':ab,'evidence_sha256':'dirhash','verification_status':'DIRECTORY_BYTES_MATCH'})
    write('official.json',{'milestone':'S8.22.7.7','date':'2023-11-15','source_url':'https://www.nba.com/games?date=2023-11-15','source_sha256':digest,'official_game_count':8,'official_games':games})
    def csv_write(path,rows):
        import io
        f=io.StringIO();w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        write(path,f.getvalue().encode())
    csv_write('provider.csv',provider);csv_write('crosswalk.csv',mappings)
    write('capture.json',{'date':'2023-11-15','provider_rows':8,'provider_csv_sha256':hashlib.sha256((root/'provider.csv').read_bytes()).hexdigest()})
    write('directory.json',{'date':'2023-11-15','status':'DIRECTORY_CROSSWALK_VERIFIED_CANDIDATE_GAME_AGREEMENT','team_identity_verified_from_directory':True,'verified_rows':16,'issues':[],'source_sha256':'dirhash'})
    write('prior.json',{'milestone':'S8.22.7.8','date':'2023-11-15','matched_games':8,'issues':[],'matches':prior})
    return root,dict(official_receipt='official_receipt.json',official_report='official.json',provider_csv='provider.csv',provider_capture_report='capture.json',directory_review='directory.json',verified_crosswalk='crosswalk.csv',comparison_report='prior.json')

def test_agreement_never_certifies_completeness(tmp_path):
    root,kw=fixture(tmp_path)
    r=audit(root,**kw)
    assert r['game_agreement']=='PASS'
    assert r['date_completeness']=='NOT_CERTIFIED'
    assert r['decision']=='BLOCK_TRAINING'
    assert len(r['reconstructed_matches'])==8

def test_hash_tampering_blocks(tmp_path):
    root,kw=fixture(tmp_path)
    (root/'provider.csv').write_text((root/'provider.csv').read_text()+'\n')
    r=audit(root,**kw)
    assert r['game_agreement']=='BLOCKED'
    assert r['checks']['provider_csv_sha256']['status']=='BLOCKED'

def test_wrong_tipoff_blocks(tmp_path):
    root,kw=fixture(tmp_path)
    data=json.loads((root/'official.json').read_text())
    data['official_games'][0]['tipoff_utc']='2023-11-16T00:01:00Z'
    (root/'official.json').write_text(json.dumps(data))
    r=audit(root,**kw)
    assert r['game_agreement']=='BLOCKED'
    assert any('tipoff_disagreement' in x for x in r['issues'])

def test_path_escape_rejected(tmp_path):
    root,kw=fixture(tmp_path)
    kw['provider_csv']='../escape.csv'
    import pytest
    with pytest.raises(ValueError,match='escapes'):
        audit(root,**kw)
