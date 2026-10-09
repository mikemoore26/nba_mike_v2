import csv
import importlib.util
import json
from pathlib import Path
import pytest

P=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_45/run_s7_45.py'
spec=importlib.util.spec_from_file_location('s745',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
SHA='a'*64
URL='https://www.nba.com/news/sample'
def row(field='datePublished',date='2026-02-01',source='JSON_LD',sha=SHA):
    return dict(article_sha256=sha,article_url=URL,metadata_field=field,metadata_raw_value=date,metadata_normalized_date=date,metadata_source=source,historical_publication_verified='false',origin_team_verified='false',player_name='Test Player',candidate_number='1')

def test_one_publication_date():
    r=m.reconcile([row()])[0]
    assert r['preferred_publication_candidate']=='2026-02-01'
    assert r['archive_priority']=='HIGH_ARCHIVE_LOOKUP'
def test_conflicting_publication_fields():
    r=m.reconcile([row(),row('datePublished','2026-02-02')])[0]
    assert r['publication_conflict']=='true' and not r['preferred_publication_candidate']
def test_modified_separate():
    r=m.reconcile([row(),row('dateModified','2026-02-03')])[0]
    assert r['publication_dates']=='2026-02-01' and r['modified_dates']=='2026-02-03'
def test_modified_before_publication_flagged():
    assert m.reconcile([row(),row('dateModified','2026-01-31')])[0]['modified_before_publication']=='true'
def test_time_text_not_publication():
    r=m.reconcile([row('time.text','2026-02-01','HTML_TIME_TEXT')])[0]
    assert r['publication_dates']=='' and r['unattributed_dates']=='2026-02-01'
def test_created_only():
    assert m.reconcile([row('dateCreated')])[0]['archive_priority']=='MEDIUM_ARCHIVE_LOOKUP'
def test_no_dates():
    r=m.reconcile([row('time.text','','HTML_TIME_TEXT')])[0]
    assert r['archive_priority']=='LOW_INSUFFICIENT_PUBLICATION_SIGNAL'
def test_repeated_rows_single_article():
    assert len(m.reconcile([row(),row()]))==1
def test_multiple_articles():
    assert len(m.reconcile([row(),row(sha='b'*64)]))==2
def test_sha_url_mismatch():
    r=row();r['article_url']='https://www.nba.com/news/other'
    with pytest.raises(ValueError,match='multiple article URLs'):m.reconcile([row(),r])
def test_upstream_verified_fails():
    r=row();r['historical_publication_verified']='true'
    with pytest.raises(ValueError,match='verification'):m.reconcile([r])
def test_bad_date_fails():
    with pytest.raises(ValueError,match='Invalid normalized date'):m.reconcile([row(date='2026-02-30')])
def test_bad_host_fails():
    r=row();r['article_url']='https://evil.example/news'
    with pytest.raises(ValueError,match='Non-official'):m.reconcile([r])
def test_report_and_csv(tmp_path):
    src=tmp_path/'input.csv'; out=tmp_path/'output'
    with src.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(row()));w.writeheader();w.writerow(row())
    report=m.run(src,out)
    assert report['unique_articles']==1 and report['eligible_for_asof_training'] is False
    assert len(list(csv.DictReader((out/'s7_45_review.csv').open())))==1
    assert json.loads((out/'s7_45_report.json').read_text())['decision']=='BLOCK_TRAINING'
def test_empty_rejected():
    with pytest.raises(ValueError,match='Empty'):m.reconcile([])
