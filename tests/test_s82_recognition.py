import csv
import importlib.util
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / 'research/p0_s8/s8_2/run_s8_2.py'
spec = importlib.util.spec_from_file_location('s82', MODULE)
s82 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s82)
COLS = ('game_id','event_date','player_id','team_id','min','pts','reb','ast','fg3m')

def write(path, rows, cols=COLS):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(rows)

def row(**kw):
    x=dict(game_id='0021900001',event_date='2019-10-22',player_id='1',team_id='123',min='29:30',pts='20',reb='6',ast='4',fg3m='2'); x.update(kw); return x

def test_exact_schema_recognized(tmp_path):
    p=tmp_path/'x.csv';write(p,[row()]);r=s82.audit_file(p,'2019-20')
    assert r['issues']=={} and r['column_map']['date']=='event_date'
    assert set(r['available_targets'])=={'pts','reb','ast','fg3m'}
    assert r['date_min']=='2019-10-22' and r['status']=='QUALITY_CHECKS_PASS_ASOF_UNVERIFIED'
    assert not r['training_eligible']

def test_case_insensitive_targets(tmp_path):
    p=tmp_path/'x.csv'; cols=('GAME_ID','EVENT_DATE','PLAYER_ID','MIN','Pts','ReB')
    write(p,[dict(GAME_ID='1',EVENT_DATE='2019-10-22',PLAYER_ID='1',MIN='30',Pts='4',ReB='3')],cols)
    r=s82.audit_file(p,'2019-20');assert r['available_targets']==['Pts','ReB'] and r['issues']=={}

def test_duplicate(tmp_path):
    p=tmp_path/'x.csv';write(p,[row(),row()]);assert s82.audit_file(p,'2019-20')['issues']['DUPLICATE_PLAYER_GAME']==1

def test_missing_date_value(tmp_path):
    p=tmp_path/'x.csv';write(p,[row(event_date='')]);assert s82.audit_file(p,'2019-20')['issues']['MISSING_OR_INVALID_DATE']==1

def test_bad_minutes(tmp_path):
    p=tmp_path/'x.csv';write(p,[row(min='99')]);assert s82.audit_file(p,'2019-20')['issues']['MINUTES_OUTSIDE_PLAUSIBLE_RANGE']==1

def test_negative_lowercase_stat(tmp_path):
    p=tmp_path/'x.csv';write(p,[row(pts='-3')]);assert s82.audit_file(p,'2019-20')['issues']['NEGATIVE_PTS']==1

def test_nonfinite_lowercase_stat(tmp_path):
    p=tmp_path/'x.csv';write(p,[row(pts='NaN')]);assert s82.audit_file(p,'2019-20')['issues']['NONFINITE_PTS']==1

def test_outside_window(tmp_path):
    p=tmp_path/'x.csv';write(p,[row(event_date='2023-10-22')]);assert s82.audit_file(p,'2019-20')['issues']['DATE_OUTSIDE_BROAD_SEASON_WINDOW']==1

def test_all_seasons_report(tmp_path):
    base=tmp_path/'research/p0_s4/s5_1/snapshots'
    for season in s82.SEASONS:
        write(base/f'player_gamelogs_{season}.csv',[row(event_date=f'{season[:4]}-10-22')])
    r=s82.audit(tmp_path,tmp_path/'out')
    assert r['milestone']=='S8.2' and r['total_rows_scanned']==3
    assert all(not d['issues'] for d in r['datasets'])
    assert (tmp_path/'out/s8_2_dataset_review.csv').exists()
    assert (tmp_path/'out/s8_2_schema_review.csv').exists()
    assert not r['training_eligible']

def test_original_untouched(tmp_path):
    p=tmp_path/'x.csv';write(p,[row()]); before=p.read_bytes();s82.audit_file(p,'2019-20');assert p.read_bytes()==before
