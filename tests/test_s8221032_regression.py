"""S8.22.10.32: real builders -> governed adapter -> research features, synthetic only."""
import csv
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from nba_mike.canonical.builder import build_player_game_box
from nba_mike.adapters.canonical_snapshot import AdapterContractError, adapt_canonical_rows
from nba_mike.features.opportunity import build_opportunity_research_frame
from nba_mike.validation.invariants import assert_d1_boundary, assert_snapshot_metadata

RAW_FIELDS = ('GAME_ID','GAME_DATE','PLAYER_ID','TEAM_ID','OPP_TEAM_ID','MIN','PTS','REB','AST','FG3M')
CANON_FIELDS = ('game_id','game_date','player_id','team_id','opponent_team_id','minutes','points','rebounds','assists','three_pointers_made')
IDS = {('player','synthetic','1'):'p1',('team','synthetic','10'):'t1',('team','synthetic','20'):'t2'}


def _build(tmp_path, records=None):
    if records is None:
        records = [('g1','2026-10-20','1','10','20','20','10','4','2','1'),
                   ('g2','2026-10-22','1','10','20','30','12','5','3','2'),
                   ('g3','2026-10-24','1','10','20','35','18','7','4','3')]
    raw = tmp_path/'raw.csv'
    with raw.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(RAW_FIELDS); w.writerows(records)
    parent=tmp_path/'raw.manifest.json'
    parent.write_text(json.dumps({'artifact_id':'synthetic-raw','sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'validation_status':'PASS'}),encoding='utf-8')
    result=build_player_game_box(project_root=tmp_path,raw_path=raw,parent_manifest_path=parent,
        output_path=tmp_path/'canonical.csv',output_manifest_path=tmp_path/'canonical.manifest.json',
        source_name='synthetic',column_map=dict(zip(CANON_FIELDS,RAW_FIELDS)),identity_resolver=IDS)
    args={'project_root':tmp_path,'canonical_path':result.output_path,'canonical_manifest_path':result.manifest_path,'target_game_date':'2026-10-24'}
    return args


def test_real_canonical_builder_into_adapter(tmp_path):
    args=_build(tmp_path)
    rows,meta=adapt_canonical_rows(**args,expected_entities=[{'player_id':'p1','team_id':'t1'}])
    assert [r['game_id'] for r in rows]==['g1','g2']
    assert rows[0]['min']==20
    assert meta['parent_artifact_id']
    assert meta['entity_history'][0]['eligible_game_count']==2
    assert_d1_boundary(rows,target_game_date=args['target_game_date'])
    assert_snapshot_metadata(meta,target_game_date=args['target_game_date'])


def test_adapter_to_opportunity_features_prior_only(tmp_path):
    args=_build(tmp_path)
    rows,_=adapt_canonical_rows(**args)
    features=build_opportunity_research_frame(pd.DataFrame(rows))
    assert features['game_id'].tolist()==['g1','g2']
    assert pd.isna(features.loc[0,'minutes_last3_avg'])
    assert features.loc[1,'minutes_last3_avg']==pytest.approx(20)
    assert 'target_minutes' in features.columns  # research/evaluation label, NOT deployable feature


def test_repeat_execution_is_deterministic(tmp_path):
    args=_build(tmp_path)
    first=adapt_canonical_rows(**args)
    second=adapt_canonical_rows(**args)
    assert first==second
    assert first[1]['logical_sha256']==second[1]['logical_sha256']


def test_canonical_artifact_tamper_rejected(tmp_path):
    args=_build(tmp_path)
    with Path(args['canonical_path']).open('ab') as f: f.write(b'\n')
    with pytest.raises(AdapterContractError,match='PARENT_HASH_MISMATCH'):
        adapt_canonical_rows(**args)


def test_manifest_tamper_rejected(tmp_path):
    args=_build(tmp_path)
    manifest=Path(args['canonical_manifest_path'])
    content=json.loads(manifest.read_text(encoding='utf-8'))
    content['row_count']+=1
    manifest.write_text(json.dumps(content),encoding='utf-8')
    with pytest.raises(AdapterContractError,match='MANIFEST_ROW_COUNT_MISMATCH'):
        adapt_canonical_rows(**args)


def test_same_day_games_do_not_cross_inform(tmp_path):
    records=[('g1','2026-10-20','1','10','20','20','10','4','2','1'),
             ('g1b','2026-10-20','1','10','20','40','20','5','3','2'),
             ('g2','2026-10-22','1','10','20','30','12','5','3','2')]
    args=_build(tmp_path,records)
    rows,_=adapt_canonical_rows(**args)
    frame=build_opportunity_research_frame(pd.DataFrame(rows))
    same=frame[frame['event_date']==pd.Timestamp('2026-10-20')]
    assert len(same)==2
    assert same['minutes_last3_avg'].isna().all()
    assert frame.loc[frame['game_id']=='g2','minutes_last3_avg'].iloc[0]==pytest.approx(30)
