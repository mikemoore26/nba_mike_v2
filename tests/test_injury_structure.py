import csv,hashlib
from pathlib import Path
from nba_mike.data.injury_structure import candidates_from_pages,validate_review,FIELDS

def test_candidate_is_not_auto_confirmed():
    r=candidates_from_pages([{'page':2,'text':'Header\nJohn Doe Out - Ankle\nQuestionable'}],'a'*64)
    assert len(r)==2 and all(x['review_status']=='UNREVIEWED' and x['player']=='' for x in r)
def test_stable_id():
    p=[{'page':1,'text':'Player Out'}]
    assert candidates_from_pages(p,'x')[0]['candidate_id']==candidates_from_pages(p,'x')[0]['candidate_id']
def test_no_status():
    assert candidates_from_pages([{'page':1,'text':'No rows'}],'a')==[]
def worksheet(tmp_path,rows):
    p=tmp_path/'r.csv'
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    return p
def row(**kw):
    x={k:'' for k in FIELDS};x.update(candidate_id='id',source_sha256='abc',review_status='UNREVIEWED');x.update(kw);return x
def test_unreviewed_cannot_pass(tmp_path):
    r=validate_review(worksheet(tmp_path,[row()]),'abc',min_checked=1)
    assert not r['review_validation_passed'] and not r['eligible_for_asof_training']
def test_confirmed_missing_fields_fails(tmp_path):
    r=validate_review(worksheet(tmp_path,[row(review_status='CONFIRMED')]),'abc',min_checked=1)
    assert not r['review_validation_passed'] and r['problems']
def test_rejected_counts_as_checked(tmp_path):
    r=validate_review(worksheet(tmp_path,[row(review_status='REJECTED')]),'abc',min_checked=1)
    assert r['review_validation_passed'] and r['confirmed']==0
def test_duplicate_ids_fail(tmp_path):
    r=validate_review(worksheet(tmp_path,[row(review_status='REJECTED'),row(review_status='REJECTED')]),'abc',min_checked=1)
    assert not r['review_validation_passed']
def test_hash_mismatch_fails(tmp_path):
    r=validate_review(worksheet(tmp_path,[row(review_status='REJECTED')]),'different',min_checked=1)
    assert not r['review_validation_passed']
def test_confirmed_fields_pass_but_not_training(tmp_path):
    r=validate_review(worksheet(tmp_path,[row(review_status='CONFIRMED',game_date='2026-03-27',team='NYK',player='Example Player',reason='Ankle')]),'abc',min_checked=1)
    assert r['review_validation_passed'] and not r['eligible_for_asof_training']
