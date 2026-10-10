import hashlib
import importlib.util
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / 'research/p0_s8/s8_22_7_11'

def module(name, file):
    spec = importlib.util.spec_from_file_location(name, BASE / file)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

mod = module('audit711', 'run_s8_22_7_11.py')
docs = module('docs711', 'append_docs.py')

def setup(tmp):
    report = {'milestone':'S8.22.7.10','date':'2023-11-15','game_agreement':'PASS','date_completeness':'NOT_CERTIFIED','decision':'BLOCK_TRAINING','issues':[], 'reconstructed_matches':[{'official_nba_game_id':f'002230019{i}'} for i in range(2,10)]}
    (tmp/'prior.json').write_text(json.dumps(report))
    return 'prior.json'

def test_no_evidence_remains_uncertified(tmp_path):
    r = mod.assess(tmp_path, setup(tmp_path))
    assert r['game_agreement'] == 'PASS'
    assert r['date_completeness'] == 'NOT_CERTIFIED'
    assert r['decision'] == 'BLOCK_TRAINING'
    assert r['independent_completeness_evidence'] == 'NOT_ESTABLISHED'

def test_candidate_only_even_with_explicit_manifest(tmp_path):
    prior = setup(tmp_path)
    raw = b'archived independently reviewed schedule bytes'
    (tmp_path/'source.bin').write_bytes(raw)
    h = hashlib.sha256(raw).hexdigest()
    receipt = {'date':'2023-11-15','source_url':'https://example.org/independent-schedule','evidence_path':'source.bin','sha256':h,'bytes':len(raw),'retrieved_utc':'2026-10-10T00:00:00Z'}
    manifest = {'date':'2023-11-15','source_url':receipt['source_url'],'source_sha256':h,'official_nba_game_ids':[f'002230019{i}' for i in range(2,10)],'source_explicitly_states_full_date_slate':True,'supporting_quote_or_locator':'page 2 slate header','reviewed_by':'HUMAN_REVIEWER'}
    (tmp_path/'receipt.json').write_text(json.dumps(receipt))
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    r = mod.assess(tmp_path, prior, 'manifest.json','receipt.json')
    assert r['independent_completeness_evidence'] == 'CANDIDATE_HUMAN_REVIEW_REQUIRED'
    assert r['date_completeness'] == 'NOT_CERTIFIED'

def test_tampered_source_blocks_candidate(tmp_path):
    prior = setup(tmp_path)
    (tmp_path/'source.bin').write_bytes(b'altered')
    (tmp_path/'receipt.json').write_text(json.dumps({'date':'2023-11-15','source_url':'https://example.org/schedule','evidence_path':'source.bin','sha256':'0'*64,'bytes':7}))
    (tmp_path/'manifest.json').write_text(json.dumps({'date':'2023-11-15','source_url':'https://example.org/schedule','source_sha256':'0'*64,'official_nba_game_ids':[f'002230019{i}' for i in range(2,10)],'source_explicitly_states_full_date_slate':True,'supporting_quote_or_locator':'page 1','reviewed_by':'PERSON'}))
    r = mod.assess(tmp_path, prior,'manifest.json','receipt.json')
    assert 'independent_source_integrity' in r['issues']
    assert r['independent_completeness_evidence'] == 'NOT_ESTABLISHED'

def test_missing_pair_fails_closed(tmp_path):
    r = mod.assess(tmp_path,setup(tmp_path),'manifest.json')
    assert r['issues'] and r['decision'] == 'BLOCK_TRAINING'

def test_append_docs_idempotent(tmp_path):
    (tmp_path/'docs').mkdir()
    (tmp_path/'docs/DEVELOPMENT_JOURNAL.md').write_text('original\n')
    (tmp_path/'docs/fragment.md').write_text('milestone')
    assert docs.append_once(tmp_path,'docs/DEVELOPMENT_JOURNAL.md','docs/fragment.md') == 'APPENDED_WITH_BACKUP'
    assert docs.append_once(tmp_path,'docs/DEVELOPMENT_JOURNAL.md','docs/fragment.md') == 'ALREADY_PRESENT'
    assert (tmp_path/'docs/DEVELOPMENT_JOURNAL.md.pre_s822711.bak').read_text() == 'original\n'
