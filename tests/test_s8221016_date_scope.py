import importlib.util
import csv
import json
from pathlib import Path
import pytest

PATH=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_16/run_s8_22_10_16.py'
spec=importlib.util.spec_from_file_location('s816',PATH)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def row(rid='T-007',team='BKN',matchup='BKN@MIA',date='2023-11-16',kind='TEAM_SUBMISSION'):
    return {'record_id':rid,'record_type':kind,'game_date_candidate':date,'matchup_candidate':matchup,
            'team_candidate':team,'source_pdf_context':'PDF excerpt','source_page':'1',
            'mapping_resolution':'MANUAL_EXCEPTION_REQUIRED','reason':'DATE_MISMATCH_NO_AUTOMATIC_REPAIR'}

@pytest.mark.parametrize('rid,team,matchup', [('T-007','BKN','BKN@MIA'),('T-008','MIA','BKN@MIA'),('T-009','OKC','OKC@GSW'),('T-010','GSW','OKC@GSW')])
def test_classifies_date_mismatch_without_correcting(rid,team,matchup):
    result=m.classify(row(rid,team,matchup))
    assert result['classification']=='DATE_SCOPE_MISMATCH_REVIEW_REQUIRED'
    assert result['verified_game_id']==result['proposed_corrected_date']==''
    assert result['training_eligible']=='NO'

def test_same_date_outside_slate():
    assert m.classify(row(date='2023-11-15'))['classification']=='OUT_OF_VERIFIED_SLATE_REVIEW_REQUIRED'

@pytest.mark.parametrize('changes', [{'record_id':'T-999'},{'record_type':'PLAYER'},{'team_candidate':'BOS'},
                                    {'matchup_candidate':'BOS@PHI'},{'source_pdf_context':''},{'source_page':''}])
def test_fail_closed(changes):
    original=row();original.update(changes)
    with pytest.raises(ValueError):m.classify(original)

def test_integration(tmp_path):
    base=tmp_path/'research/p0_s8/s8_22_10_15/results/2023-11-15/token';base.mkdir(parents=True)
    source=[row('T-007','BKN','BKN@MIA'),row('T-008','MIA','BKN@MIA'),row('T-009','OKC','OKC@GSW'),row('T-010','GSW','OKC@GSW')]
    with (base/'mapping_exception_analysis.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=source[0].keys());writer.writeheader();writer.writerows(source)
    (base/'review.json').write_text(json.dumps({'milestone':'S8.22.10.15','mapping_exceptions_analyzed':4,
        'training_decision':'BLOCK_TRAINING','reason_counts':{'DATE_MISMATCH_NO_AUTOMATIC_REPAIR':4}}))
    summary=m.run(tmp_path)
    assert summary['records_classified']==4 and summary['corrected_dates_asserted']==0
    assert summary['injury_rows_certified']==0 and summary['training_decision']=='BLOCK_TRAINING'
    output=list((tmp_path/'research/p0_s8/s8_22_10_16/results/2023-11-15').glob('*/team_notice_date_scope.csv'))
    assert len(output)==1 and len(m.read_csv(output[0]))==4

def test_integration_rejects_duplicate_ids(tmp_path):
    base=tmp_path/'research/p0_s8/s8_22_10_15/results/2023-11-15/token';base.mkdir(parents=True)
    rows=[row() for _ in range(4)]
    with (base/'mapping_exception_analysis.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    (base/'review.json').write_text(json.dumps({'milestone':'S8.22.10.15','mapping_exceptions_analyzed':4,
        'training_decision':'BLOCK_TRAINING','reason_counts':{'DATE_MISMATCH_NO_AUTOMATIC_REPAIR':4}}))
    with pytest.raises(ValueError,match='distinct'):m.run(tmp_path)
