import csv,hashlib,importlib.util,tempfile
from pathlib import Path
import pytest
SPEC=importlib.util.spec_from_file_location('s742',Path(__file__).resolve().parents[1]/'research/p0_s4/s7_42/run_s7_42.py')
s=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(s)
@pytest.mark.parametrize('text,player,expected',[
('Hornets Acquire Malaki Branham From Wizards In Three-Team Trade','Malaki Branham',('WAS','CHA')),
('Hornets Acquire Tyus Jones And Two Second-Round Picks From Magic','Tyus Jones',('ORL','CHA')),
('Atlanta Hawks Acquire Buddy Hield and Jonathan Kuminga from Golden State','Buddy Hield',('GSW','ATL')),
('Atlanta Hawks Acquire Buddy Hield and Jonathan Kuminga from Golden State','Jonathan Kuminga',('GSW','ATL')),
('Warriors Acquire Kristaps Porzingis From Atlanta Hawks','Kristaps Porziņģis',('ATL','GSW')),
('Golden State has acquired Kristaps Porziņģis from Atlanta','Kristaps Porziņģis',('ATL','GSW')),
('Indiana Pacers Acquire Ivica Zubac and Kobe Brown from Los Angeles Clippers','Ivica Zubac',('LAC','IND')),
('Pacers trade for Clippers center Ivica Zubac','Ivica Zubac',('LAC','IND')),
('Anthony Davis traded to Wizards in 9-player, 3-team deal','Anthony Davis',('','')),
('Atlanta Hawks Acquire Buddy Hield and Jonathan Kuminga from Golden State','Tyus Jones',('','')),
])
def test_directions(text,player,expected):assert s.direction(text,player)[1:]==expected

def test_fixture_pipeline(tmp_path):
    raw='Hornets Acquire Malaki Branham From Wizards'
    evidence_sha=hashlib.sha256(raw.encode()).hexdigest()
    article=b'<html>sample</html>'; article_sha=hashlib.sha256(article).hexdigest()
    obj=tmp_path/'objects';obj.mkdir();(obj/(article_sha+'.html')).write_bytes(article)
    r={k:'' for k in s.REQ}
    r.update(candidate_number='1',player_name='Malaki Branham',player_id='1631103',event_date='2026-02-05',to_team='CHA',article_url='https://www.nba.com/hornets/news/trade',article_sha256=article_sha,evidence_type='HEADLINE',evidence_text=raw,evidence_sha256=evidence_sha,historical_publication_verified='false',origin_team_verified='false')
    p=tmp_path/'input.csv'
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=sorted(s.REQ));w.writeheader();w.writerow(r)
    report=s.run(p,tmp_path/'results',obj)
    assert report['direction_rows']==1 and report['unique_source_objects_sha256_verified']==1
    assert report['origin_teams_verified']==0 and report['status_totals_reconcile']

def test_hash_rejection(tmp_path):
    p=tmp_path/'bad.csv';p.write_text(','.join(sorted(s.REQ))+'\n'+','.join('bad' for _ in s.REQ)+'\n')
    with pytest.raises(ValueError):s.run(p,tmp_path/'out')

def test_family():
    assert s.family('https://www.nba.com/hawks/news/test')=='TEAM:hawks'
    assert s.family('https://www.nba.com/news/test')=='NBA_NEWS'
    with pytest.raises(ValueError):s.family('https://example.com/news/test')
