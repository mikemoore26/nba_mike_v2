"""Regression for S8.22.10.24 candidate capture unpacking bug."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_24/run_s8_22_10_24.py'
spec=importlib.util.spec_from_file_location('s824_regression',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_candidates_from_single_capture(tmp_path):
    d=tmp_path/'research/p0_s8/s8_22_10_22a/results/2023-11-15/abc';d.mkdir(parents=True)
    rows=[{'record_id':f'P{i:03d}','raw_name':f'Last{i}, First','candidate_nba_person_id':str(1000+i),'report_team':'WAS','registry_full_name':f'First Last{i}','match_class':'UNIQUE_NAME_ID_CANDIDATE','historical_team_verified':'NO'} for i in range(44)]
    with (d/'player_id_candidates.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    sha=hashlib.sha256((d/'player_id_candidates.csv').read_bytes()).hexdigest()
    (d/'capture_manifest.json').write_text(json.dumps({'milestone':'S8.22.10.22A','training_decision':'BLOCK_TRAINING','candidate_csv_sha256':sha}))
    got,manifest,metadata=m.candidates_from(tmp_path)
    assert len(got)==44 and manifest==d/'capture_manifest.json' and metadata['candidate_csv_sha256']==sha
