import csv
import json
from pathlib import Path
import pytest
from nba_mike.data.injury_multi_report import audit_pages,audit_directory

def empty_page():return {'page':1,'width':841.95,'words':[]}

def test_empty_page_is_not_consistent():
    report,*_=audit_pages([empty_page()],'a'*64)
    assert report['players']==0
    assert report['status']=='REVIEW_REQUIRED'

def test_empty_page_has_zero_events():
    report,*_=audit_pages([empty_page()],'a'*64)
    assert report['matchup_events']==0

def test_missing_directory(tmp_path):
    with pytest.raises(ValueError,match='not found'):
        audit_directory(tmp_path/'missing',tmp_path/'out')

def test_reject_low_min_distinct(tmp_path):
    with pytest.raises(ValueError,match='min_distinct'):
        audit_directory(tmp_path,tmp_path/'out',min_distinct=1)

def test_reject_zero_max_files(tmp_path):
    with pytest.raises(ValueError,match='max_files'):
        audit_directory(tmp_path,tmp_path/'out',max_files=0)

def test_empty_directory_blocks(tmp_path):
    report=audit_directory(tmp_path,tmp_path/'out')
    assert report['validation_gate']=='INSUFFICIENT_DISTINCT_VALID_REPORTS'
    assert report['eligible_for_asof_training'] is False

def test_invalid_pdf_is_reported(tmp_path):
    (tmp_path/'broken.pdf').write_bytes(b'not pdf')
    report=audit_directory(tmp_path,tmp_path/'out')
    assert report['reports_with_errors']==1
    assert report['distinct_reports']==1

def test_duplicate_bytes_not_counted(tmp_path):
    for name in ('a.pdf','b.pdf'):(tmp_path/name).write_bytes(b'%PDF-duplicate-but-broken')
    report=audit_directory(tmp_path,tmp_path/'out')
    assert report['distinct_reports']==1
    assert report['duplicate_files_skipped']==1

def test_max_files_enforced(tmp_path):
    for name in ('a.pdf','b.pdf'):(tmp_path/name).write_bytes(b'%PDF-')
    with pytest.raises(ValueError,match='exceed max_files'):
        audit_directory(tmp_path,tmp_path/'out',max_files=1)

def test_json_output(tmp_path):
    report=audit_directory(tmp_path,tmp_path/'out')
    assert json.loads((tmp_path/'out/s7_14_report.json').read_text())==report

def test_csv_headers_even_empty(tmp_path):
    audit_directory(tmp_path,tmp_path/'out')
    with (tmp_path/'out/s7_14_reports.csv').open() as f:
        assert 'filename' in next(csv.reader(f))

def test_no_publication_verification(tmp_path):
    report=audit_directory(tmp_path,tmp_path/'out')
    assert report['historical_publication_verified'] is False

def test_status_research_only(tmp_path):
    report=audit_directory(tmp_path,tmp_path/'out')
    assert report['status']=='RESEARCH_ONLY'
    assert report['decision']=='BLOCK_TRAINING'
