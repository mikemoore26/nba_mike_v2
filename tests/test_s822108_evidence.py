import importlib.util
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_8/run_s8_22_10_8.py'
spec=importlib.util.spec_from_file_location('s822108',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def base():
    return [{'game_date':'2023-11-15','away_at_home':k,'provisional_nba_game_id':str(22300192+i).zfill(10),'game_id_status':'UNVERIFIED_PROVISIONAL'} for i,k in enumerate(['DAL@WAS','NYK@ATL','BOS@PHI','MIL@TOR','ORL@CHI','MIN@PHX','SAC@LAL','CLE@POR'])]+[{'game_date':'2023-11-16','away_at_home':k,'game_id_status':'OUTSIDE_TARGET_SLATE'} for k in ['BKN@MIA','OKC@GSW']]

def test_no_evidence_stays_unverified(tmp_path):
    out=m.evaluate(base(),[],tmp_path)
    assert len(out)==8 and all(x['verified_game_id']=='NO' and x['evidence_status']=='MISSING_EVIDENCE' for x in out)

def test_duplicate_evidence_rejected(tmp_path):
    e={'game_date':'2023-11-15','away_at_home':'DAL@WAS'}
    with pytest.raises(ValueError,match='Duplicate evidence'):m.evaluate(base(),[e,e],tmp_path)

def test_wrong_sha_rejected(tmp_path):
    (tmp_path/'snapshot.txt').write_text('evidence')
    with pytest.raises(ValueError,match='SHA256 mismatch'):
        m.evaluate(base(),[{'game_date':'2023-11-15','away_at_home':'DAL@WAS','snapshot_path':'snapshot.txt','snapshot_sha256':'0'*64}],tmp_path)

def test_source_snapshot_still_requires_manual_check(tmp_path):
    f=tmp_path/'snapshot.txt';f.write_text('source bytes')
    e={'game_date':'2023-11-15','away_at_home':'DAL@WAS','nba_game_id':'0022300192','source_url':'https://www.nba.com/game/example','snapshot_path':'snapshot.txt','snapshot_sha256':m.sha(f),'source_row_reference':'row1','review_decision':'ACCEPT'}
    x=next(r for r in m.evaluate(base(),[e],tmp_path) if r['away_at_home']=='DAL@WAS')
    assert x['evidence_status']=='SNAPSHOT_PRESENT_REQUIRES_MANUAL_SOURCE_CHECK' and x['verified_game_id']=='NO'

def test_conflicting_id_not_accepted(tmp_path):
    e={'game_date':'2023-11-15','away_at_home':'DAL@WAS','nba_game_id':'0022300999'}
    x=next(r for r in m.evaluate(base(),[e],tmp_path) if r['away_at_home']=='DAL@WAS')
    assert x['evidence_status']=='GAME_ID_DISAGREEMENT_REQUIRES_INVESTIGATION'

def test_outside_slate_rejected(tmp_path):
    with pytest.raises(ValueError,match='outside target slate'):
        m.evaluate(base(),[{'game_date':'2023-11-16','away_at_home':'BKN@MIA'}],tmp_path)

def test_path_escape_rejected(tmp_path):
    f=tmp_path.parent/'outside.txt';f.write_text('x')
    with pytest.raises(ValueError,match='outside evidence directory'):
        m.evaluate(base(),[{'game_date':'2023-11-15','away_at_home':'DAL@WAS','snapshot_path':'../outside.txt','snapshot_sha256':m.sha(f)}],tmp_path)

def test_duplicate_crosswalk_rejected(tmp_path):
    b=base();b.append(dict(b[0]))
    with pytest.raises(ValueError,match='Duplicate crosswalk'):m.evaluate(b,[],tmp_path)
