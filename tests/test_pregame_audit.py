from nba_mike.data.pregame_audit import audit_observation, summarize_records

BASE = dict(source_id='example', game_id='G', player_id='P', field='status', value='out',
            observed_at_utc='2026-01-01T18:00:00Z', available_at_utc='2026-01-01T18:05:00Z',
            prediction_cutoff_utc='2026-01-01T19:00:00Z')

def test_eligible():
    assert audit_observation(BASE)['eligible']

def test_availability_after_cutoff_fails():
    x = {**BASE, 'available_at_utc':'2026-01-01T19:01:00Z'}
    assert audit_observation(x)['reason'] == 'available_after_cutoff'

def test_naive_timestamp_fails():
    x = {**BASE, 'prediction_cutoff_utc':'2026-01-01T19:00:00'}
    assert not audit_observation(x)['eligible']

def test_missing_provenance_fails():
    x = dict(BASE); del x['source_id']
    assert audit_observation(x)['reason'].startswith('missing_required:')

def test_revision_fails_closed():
    assert audit_observation({**BASE, 'is_revised':True})['reason'] == 'revision_asof_unverified'

def test_observed_after_cutoff_fails():
    x = {**BASE, 'observed_at_utc':'2026-01-01T20:00:00Z', 'available_at_utc':'2026-01-01T20:01:00Z'}
    assert audit_observation(x)['reason'] == 'observed_after_cutoff'

def test_available_before_observed_fails():
    x = {**BASE, 'available_at_utc':'2026-01-01T17:59:00Z'}
    assert audit_observation(x)['reason'] == 'availability_before_observation'

def test_summary():
    assert summarize_records([BASE, {**BASE,'source_id':''}])['eligible'] == 1
