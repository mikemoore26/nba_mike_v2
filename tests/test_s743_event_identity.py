import csv,hashlib,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/p0_s4/s7_43'))
from run_s7_43 import run,dates_in_text,approved_url

def fixture(tmp_path,rows=None):
    obj=tmp_path/'objects';obj.mkdir();raw=b'<html>article</html>';sha=hashlib.sha256(raw).hexdigest();(obj/(sha+'.html')).write_bytes(raw)
    def row(player='Tyus Jones',dest='CHA',tracker='DAL',url='https://www.nba.com/hornets/news/tyus',family='TEAM:hornets',evidence='Hornets acquire Tyus Jones from Magic'):
        return dict(candidate_number='4',player_name=player,player_id='1626145',event_date='2026-02-05',tracker_to_team=tracker,article_url=url,article_sha256=sha,source_family=family,evidence_type='HEADLINE',evidence_text=evidence,evidence_sha256=hashlib.sha256(evidence.encode()).hexdigest(),origin_candidate='ORL',destination_candidate=dest,direction_pattern='ACQUIRED_FROM',review_status='TRACKER_CONFLICT_REVIEW_ONLY',quality_flags='',historical_publication_verified='false',origin_team_verified='false')
    data=rows or [row()];p=tmp_path/'in.csv'
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    return p,obj,row

def test_mismatch_not_same_event_conflict(tmp_path):
    p,obj,_=fixture(tmp_path);r=run(p,tmp_path/'out',obj)
    assert r['tracker_destination_mismatches_unresolved']==1
    assert r['true_same_event_conflicts_verified']==0
    assert r['event_identity_resolved']==0

def test_no_independence_from_source_family(tmp_path):
    p,obj,row=fixture(tmp_path)
    data=[row(),row(url='https://www.nba.com/news/tyus',family='NBA_NEWS')]
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    r=run(p,tmp_path/'out',obj)
    assert r['independent_reports_verified']==0
    assert r['independence_counts']['SHARED_CONTENT_OBJECT']==2

def test_duplicate_dedup(tmp_path):
    p,obj,row=fixture(tmp_path);data=[row(),row()]
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    assert run(p,tmp_path/'out',obj)['duplicate_rows_removed']==1

def test_sha_tamper_fails(tmp_path):
    p,obj,_=fixture(tmp_path);next(obj.iterdir()).write_bytes(b'tamper')
    with pytest.raises(ValueError,match='Article hash'):run(p,tmp_path/'out',obj)

def test_upstream_verification_fails(tmp_path):
    p,obj,row=fixture(tmp_path);r=row();r['historical_publication_verified']='true'
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(r));w.writeheader();w.writerow(r)
    with pytest.raises(ValueError,match='Unexpected'):run(p,tmp_path/'out',obj)

def test_article_date_mentions_not_event_dates(tmp_path):
    p,obj,row=fixture(tmp_path);r=row(evidence='Hornets acquire Tyus Jones from Magic on February 5, 2026')
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(r));w.writeheader();w.writerow(r)
    run(p,tmp_path/'out',obj)
    with (tmp_path/'out'/'s7_43_review.csv').open() as f:record=next(csv.DictReader(f))
    assert record['article_event_date']=='' and record['date_basis']=='NO_EVENT_DATE_PROOF'
    assert 'UNATTRIBUTED_DATE_MENTION' in record['quality_flags']

def test_date_parser():
    assert dates_in_text('February 5, 2026 and 2026-02-06')==['2026-02-05','2026-02-06']

def test_invalid_dates_not_used():
    assert dates_in_text('February 31, 2026')==[]

def test_url_reject_external():
    with pytest.raises(ValueError):approved_url('https://example.com/news/trade')

def test_url_reject_fake_subdomain():
    with pytest.raises(ValueError):approved_url('https://nba.com.evil.test/news/trade')

def test_reconcile(tmp_path):
    p,obj,_=fixture(tmp_path);r=run(p,tmp_path/'out',obj)
    assert r['status_totals_reconcile'] and sum(r['status_counts'].values())==r['review_rows']

def test_direction_without_verified_training(tmp_path):
    p,obj,_=fixture(tmp_path);r=run(p,tmp_path/'out',obj)
    assert r['decision']=='BLOCK_TRAINING' and not r['eligible_for_asof_training']
