import importlib.util
import json
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_9'
spec=importlib.util.spec_from_file_location('s8229',BASE/'run_s8_22_9.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
data=json.loads((BASE/'source_candidates.json').read_text())
def test_catalog_passes():assert mod.assess(data)['source_shortlist_status']=='REVIEW_READY'
def test_training_blocked():assert mod.assess(data)['training_eligible'] is False
def test_all_categories():assert all(mod.assess(data)['coverage'].values())
def test_duplicate_fails():
    d=json.loads(json.dumps(data));d['candidate_sources'].append(d['candidate_sources'][0]);assert mod.assess(d)['issues']
def test_false_verified_rejected():
    d=json.loads(json.dumps(data));d['candidate_sources'][0]['pregame_timestamp_proof']='VERIFIED';assert mod.assess(d)['issues']
def test_bad_url_rejected():
    d=json.loads(json.dumps(data));d['candidate_sources'][0]['url']='http://example.com';assert mod.assess(d)['issues']
