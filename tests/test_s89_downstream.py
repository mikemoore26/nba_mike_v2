import importlib.util
from pathlib import Path
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'research/p0_s8/s8_9/run_s8_9.py'
spec = importlib.util.spec_from_file_location('s89_audit', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

@pytest.mark.parametrize('forbidden', sorted(mod.BANNED))
def test_all_known_realized_and_target_columns_rejected(forbidden):
    with pytest.raises(ValueError, match='prohibited'):
        mod.validate_predictor_columns(['minutes_last5_avg', forbidden])

def test_valid_features_not_automatically_certified():
    assert mod.validate_predictor_columns(['minutes_last5_avg','prior_games']) == ['minutes_last5_avg','prior_games']

def test_empty_and_duplicate_selections_rejected():
    with pytest.raises(ValueError, match='empty'):
        mod.validate_predictor_columns([])
    with pytest.raises(ValueError, match='duplicate'):
        mod.validate_predictor_columns(['prior_games','prior_games'])

def test_scanner_discovers_fit_and_columns():
    source = 'def train(df):\n    X = df[["min", "prior_games"]]\n    model.fit(X, y)\n'
    hits, err = mod.scan_source('example.py', source)
    assert err is None
    rules = {x['rule'] for x in hits}
    assert 'MODEL_FIT' in rules and 'OUTCOME_COLUMN_REFERENCE' in rules

def test_scanner_handles_syntax_error():
    hits, err = mod.scan_source('bad.py', 'def broken(\n')
    assert not hits and 'SyntaxError' in err['error']

def test_runner_remains_blocked(tmp_path):
    (tmp_path/'src/nba_mike').mkdir(parents=True)
    (tmp_path/'src/nba_mike/example.py').write_text('model.fit(X, y)\n')
    report = mod.run(tmp_path, tmp_path/'output')
    assert report['decision'] == 'BLOCK_TRAINING'
    assert not report['training_eligible']
    assert report['findings_count'] >= 1
    assert (tmp_path/'output/s8_9_findings.csv').exists()
