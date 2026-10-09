import csv
import hashlib
import importlib.util
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / 'research/p0_s8/s8_14/run_s8_14.py'
spec=importlib.util.spec_from_file_location('s814',MODULE)
s814=importlib.util.module_from_spec(spec)
spec.loader.exec_module(s814)

def test_sampling_excludes_restart():
    games={'a':{'game_id':'a','event_date':'2020-07-30','participant_rows':1},'b':{'game_id':'b','event_date':'2020-01-01','participant_rows':1},'c':{'game_id':'c','event_date':'2020-08-15','participant_rows':1}}
    result=s814.select_sample(games,'2019-20')
    assert {x['game_id'] for x in result}=={'b','c'}
    assert all(x['decision']=='RESEARCH_SAMPLE_ONLY' for x in result)

def test_rejects_post_tipoff():
    row={'game_id':'1','source_name':'A','source_url':'https://example.org/a','evidence_type':'injury_status','published_at':'2026-10-01T21:00:00Z','tipoff_at':'2026-10-01T20:00:00Z','captured_at':'2026-10-01T22:00:00Z','sha256':'a'*64,'source_file':'artifact.txt'}
    assert s814.classify_evidence(row,Path('.'))[0]=='REJECT_NOT_PREGAME'

def test_rejects_naive_time():
    try:s814.parse_time('2026-10-01T19:00:00')
    except ValueError:pass
    else:raise AssertionError('naive timestamp accepted')

def test_rejects_missing_artifact(tmp_path):
    row={'game_id':'1','source_name':'A','source_url':'https://example.org/a','evidence_type':'injury_status','published_at':'2026-10-01T19:00:00Z','tipoff_at':'2026-10-01T20:00:00Z','captured_at':'2026-10-01T19:30:00Z','sha256':'a'*64,'source_file':'missing.txt'}
    assert s814.classify_evidence(row,tmp_path)[0]=='REJECT_MISSING_ARTIFACT'

def test_consistent_artifact_still_not_certified(tmp_path):
    (tmp_path/'source.txt').write_text('source bytes')
    row={'game_id':'1','source_name':'A','source_url':'https://example.org/a','evidence_type':'injury_status','published_at':'2026-10-01T19:00:00Z','tipoff_at':'2026-10-01T20:00:00Z','captured_at':'2026-10-01T19:30:00Z','sha256':hashlib.sha256(b'source bytes').hexdigest(),'source_file':'source.txt'}
    assert s814.classify_evidence(row,tmp_path)[0]=='CANDIDATE_MANUAL_REVIEW'
    row['sha256']='b'*64
    assert s814.classify_evidence(row,tmp_path)[0]=='REJECT_DIGEST_MISMATCH'

def test_runner_never_approves(tmp_path):
    d=tmp_path/'research/p0_s4/s5_1/snapshots';d.mkdir(parents=True)
    with (d/'player_gamelogs_2019-20.csv').open('w',newline='') as fh:
        w=csv.DictWriter(fh,fieldnames=['game_id','event_date','player_id']);w.writeheader();w.writerow({'game_id':'1','event_date':'2020-01-01','player_id':'5'})
    report=s814.run(tmp_path)
    assert report['decision']=='BLOCK_TRAINING'
    assert report['independently_verified_games']==0
    assert report['sampled_games']==1
    assert (tmp_path/'research/p0_s8/s8_14/results/s8_14_sample_games.csv').exists()

def test_conflicting_dates_fail(tmp_path):
    p=tmp_path/'data.csv'
    p.write_text('game_id,event_date,player_id\n1,2020-01-01,5\n1,2020-01-02,6\n')
    try:s814.load_games(p)
    except ValueError:pass
    else:raise AssertionError('conflicting dates accepted')
