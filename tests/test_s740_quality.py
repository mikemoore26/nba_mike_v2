import csv, hashlib, importlib.util, json
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_40/run_s7_40.py'
spec=importlib.util.spec_from_file_location('s740',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
SHA='a'*64

def record(**kw):
    r={k:'' for k in m.FIELDS};r.update(candidate_number='1',player_name='Malaki Branham',player_id='12',event_date='2026-02-01',to_team='CHA',article_url='https://www.nba.com/news/example',article_sha256=SHA,review_label='SAME_SENTENCE_REVIEW_ONLY',statement='Charlotte Hornets acquired Malaki Branham from Washington Wizards in a trade.',team_mentions='CHA;WAS',origin_team_verified='false',historical_publication_verified='false');r.update(kw);return r

def write(tmp,rows):
    f=tmp/'input.csv'
    with f.open('w',newline='',encoding='utf-8') as h:
        w=csv.DictWriter(h,fieldnames=sorted(m.FIELDS));w.writeheader();w.writerows(rows)
    return f

def test_direction_acquired():assert m.direction('Charlotte Hornets acquired Malaki Branham from Washington Wizards in a trade.','Malaki Branham')==('ACQUIRED_FROM','WAS','CHA')
def test_direction_traded():assert m.direction('Washington Wizards traded Malaki Branham to Charlotte Hornets in a deal.','Malaki Branham')==('TRADED_TO','WAS','CHA')
def test_no_inference():assert m.direction('Malaki Branham was in a trade involving Charlotte and Washington.','Malaki Branham')[0]=='NONE'
def test_wrong_player():assert 'PLAYER_NOT_IN_STATEMENT' in m.quality('Charlotte acquired John Smith from Washington.','Malaki Branham','CHA;WAS')
def test_many_teams():assert 'MANY_TEAM_MENTIONS' in m.quality('Malaki Branham traded','Malaki Branham','ATL;BOS;CHA;WAS')
def test_page_chrome():assert 'PAGE_CHROME' in m.quality('Malaki Branham traded. Privacy policy.','Malaki Branham','')
def test_long():assert 'LONG_OR_BOILERPLATE' in m.quality('Malaki Branham traded '+'x'*450,'Malaki Branham','')
def test_duplicates_and_counts(tmp_path):
    f=write(tmp_path,[record(),record()]);r=m.run(f,tmp_path/'out');assert r['unique_review_rows']==1 and r['duplicates_removed']==1 and r['review_status_sum_matches_rows']
    with (tmp_path/'out'/'s7_40_review.csv').open() as h:rows=list(csv.DictReader(h))
    assert rows[0]['origin_candidate']=='WAS' and rows[0]['origin_team_verified']=='false'
def test_destination_conflict(tmp_path):
    r=m.run(write(tmp_path,[record(to_team='BOS')]),tmp_path/'out');assert r['direction_proposals']==0
    with (tmp_path/'out'/'s7_40_review.csv').open() as h:assert 'DESTINATION_CONFLICT_WITH_TRACKER' in next(csv.DictReader(h))['quality_flags']
def test_invalid_verified_fails(tmp_path):
    with pytest.raises(ValueError):m.run(write(tmp_path,[record(origin_team_verified='true')]),tmp_path/'out')
def test_invalid_hash_fails(tmp_path):
    with pytest.raises(ValueError):m.run(write(tmp_path,[record(article_sha256='bad')]),tmp_path/'out')
def test_empty_unmatched(tmp_path):
    r=m.run(write(tmp_path,[record(statement='',review_label='NO_SAME_SENTENCE_MATCH',team_mentions='')]),tmp_path/'out');assert r['direction_proposals']==0
