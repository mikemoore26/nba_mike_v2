import importlib.util
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'research/p0_s4/s7_51/run_s7_51.py'
spec = importlib.util.spec_from_file_location('s751', SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def row(**kwargs):
    d = dict(player_name='A', mapping_status='COMPLETE', integrity_status='SHA256_MATCH', captured_sha256='a'*64, direction_status='FULL_TEXT_DIRECTION_CANDIDATE', article_url='https://www.nba.com/news/trade', origin_candidate='ATL', destination_candidate='GSW')
    d.update(kwargs)
    return d


def test_direction(): assert m.category(row()) == 'DIRECTION_CANDIDATE_UNVERIFIED'
def test_mapping(): assert m.category(row(player_name='')) == 'MAPPING_GAP'
def test_mapping_flag(): assert m.category(row(mapping_status='MAPPING_GAP_REVIEW')) == 'MAPPING_GAP'
def test_no_capture(): assert m.category(row(integrity_status='NO_SAVED_OBJECT')) == 'CAPTURE_UNAVAILABLE_OR_UNVERIFIED'
def test_cooccurrence(): assert m.category(row(direction_status='COOCCURRENCE_ONLY')) == 'DIRECTION_NOT_ESTABLISHED'
def test_missing_player(): assert m.category(row(direction_status='NO_PLAYER_IN_EXTRACTED_CONTENT')) == 'PLAYER_NOT_RECOVERED'
def test_other(): assert m.category(row(direction_status='OTHER')) == 'CONTENT_OR_EXTRACTION_UNRESOLVED'
def test_url_normalize(): assert m.canonical_url('HTTPS://WWW.NBA.COM/news/x/?a=1#z') == 'https://www.nba.com/news/x'
def test_url_invalid(): assert m.canonical_url('not-a-url') == ''
def test_priority(): assert m.priority('MAPPING_GAP') == 'P1_MAPPING_FIX'
def test_count_reconciles():
    rep, rev, arts = m.audit([row(), row(player_name='B')], 'abc')
    assert sum(rep['bottleneck_counts'].values()) == rep['input_rows'] == 2
    assert rep['sha256_verified_unique_capture_objects'] == 1
    assert len(arts) == 1
    assert rep['eligible_for_asof_training'] is False

def test_duplicate_same_claim():
    rep, rev, _ = m.audit([row(), row()], 'abc')
    assert rep['duplicate_player_claim_rows'] == 1
    assert rev[1]['duplicate_player_claim_row'] == 'true'
def test_different_capture_not_duplicate():
    rep, _, _ = m.audit([row(), row(captured_sha256='b'*64)], 'abc')
    assert rep['duplicate_player_claim_rows'] == 0
    assert rep['sha256_verified_unique_capture_objects'] == 2
def test_source_independence_never_assumed():
    rep, rev, arts = m.audit([row(), row(player_name='B')], 'abc')
    assert rep['verified_independent_source_families'] == 0
    assert arts[0]['source_independence_verified'] == 'false'
def test_empty():
    rep, rev, arts = m.audit([], 'abc')
    assert rep['input_rows'] == 0 and not rev and not arts
