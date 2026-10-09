import csv, importlib.util, json
from pathlib import Path
import pytest

SRC=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_0/run_s8_0.py'
spec=importlib.util.spec_from_file_location('s80',SRC)
s80=importlib.util.module_from_spec(spec);spec.loader.exec_module(s80)

def test_no_data_blocks(tmp_path):
 report=s80.run(tmp_path,tmp_path/'out')
 assert report['decision']=='BLOCK_TRAINING'
 assert all(c['status']=='BLOCKED' for c in report['components'])

def test_csv_schema_only(tmp_path):
 d=tmp_path/'data';d.mkdir();(d/'player_minutes.csv').write_text('player_id,game_date,minutes,as_of\n1,2026-01-01,25,2025-12-31\n')
 report=s80.run(tmp_path,tmp_path/'out')
 assert next(c for c in report['components'] if c['component']=='minutes')['status']=='NEEDS_REPAIR'
 assert report['historical_asof_training_eligible'] is False

def test_no_asof_inference_from_date(tmp_path):
 (tmp_path/'player_stats.csv').write_text('player_id,game_date,points\n')
 rows,_=s80.scan(tmp_path)
 assert rows[0]['has_asof_column'] is False

def test_hidden_venv_excluded(tmp_path):
 d=tmp_path/'.venv';d.mkdir();(d/'minutes.csv').write_text('minutes\n')
 rows,_=s80.scan(tmp_path)
 assert rows==[]

def test_outputs_exist(tmp_path):
 s80.run(tmp_path,tmp_path/'out')
 for n in ('s8_0_report.json','s8_0_inventory.csv','s8_0_component_review.csv'):
  assert (tmp_path/'out'/n).exists()

def test_roster_always_blocked(tmp_path):
 (tmp_path/'roster.csv').write_text('player_id,as_of\n')
 report=s80.run(tmp_path,tmp_path/'out')
 assert next(c for c in report['components'] if c['component']=='availability_roster')['status']=='BLOCKED'

def test_bounded_scan(tmp_path):
 for i in range(5):(tmp_path/f'data{i}.csv').write_text('x\n')
 rows,skipped=s80.scan(tmp_path,max_files=2)
 assert len(rows)==2 and skipped==3

def test_deterministic_component_count(tmp_path):
 assert len(s80.evaluate([]))==6

def test_invalid_root(tmp_path):
 with pytest.raises(ValueError):s80.run(tmp_path/'absent',tmp_path/'out')

def test_no_training_side_effects(tmp_path):
 (tmp_path/'model.py').write_text('print("do not execute")')
 s80.run(tmp_path,tmp_path/'out')
 assert not (tmp_path/'model_output').exists()

def test_json_status_consistent(tmp_path):
 report=s80.run(tmp_path,tmp_path/'out')
 disk=json.loads((tmp_path/'out'/'s8_0_report.json').read_text())
 assert disk['component_status_counts']==report['component_status_counts']

def test_inventory_header(tmp_path):
 s80.run(tmp_path,tmp_path/'out')
 with (tmp_path/'out'/'s8_0_inventory.csv').open() as f:
  assert 'has_asof_column' in next(csv.reader(f))

def test_parquet_without_pyarrow_never_crashes(tmp_path):
 (tmp_path/'minutes.parquet').write_bytes(b'not a real parquet')
 rows,_=s80.scan(tmp_path)
 assert rows[0]['header_error'].startswith('PARQUET_SCHEMA_UNAVAILABLE')

def test_research_mode(tmp_path):
 assert s80.run(tmp_path,tmp_path/'out')['status']=='RESEARCH_ONLY'

def test_output_outside_root_allowed(tmp_path):
 d=tmp_path/'project';d.mkdir()
 report=s80.run(d,tmp_path/'outputs')
 assert report['scanned_files']==0
