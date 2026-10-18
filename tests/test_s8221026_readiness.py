from pathlib import Path
import importlib.util

SCRIPT = Path(__file__).resolve().parents[1] / 'research/p0_s8/s8_22_10_26/run_readiness_audit.py'
spec = importlib.util.spec_from_file_location('readiness_audit', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_finds_candidate_but_does_not_approve(tmp_path):
    (tmp_path / 'models').mkdir()
    (tmp_path / 'models/predict_points.py').write_text('def predict(): return 12\n')
    report, path = m.audit(tmp_path)
    assert report['categories']['stat_predictions']['candidate_file_count'] == 1
    assert report['readiness']['real_money_approval'] == 'DENIED'
    assert report['training_decision'] == 'BLOCK_TRAINING'
    assert path.is_file()


def test_skips_venv_results_and_generated_output(tmp_path):
    for folder in ['.venv', 'results', 'research/p0_s8/s8_22_10_26/results']:
        p = tmp_path / folder
        p.mkdir(parents=True)
        (p / 'ticket.py').write_text('betting model')
    report, _ = m.audit(tmp_path)
    assert report['inventory_file_count'] == 0


def test_hashes_source(tmp_path):
    (tmp_path / 'odds.py').write_text('odds = 123')
    report, _ = m.audit(tmp_path)
    assert report['source_inventory'][0]['sha256'] == m.sha256(b'odds = 123')


def test_no_output_outside_root(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        m.audit(tmp_path, tmp_path.parent / 'outside.json')


def test_classify_name_and_content():
    assert 'injuries_and_lineups' in m.classify('injury_fetch.py', '')
    assert 'ticket_and_parlay' in m.classify('other.py', 'parlay = 1')


def test_unrelated_file_not_classified():
    assert m.classify('hello.py', 'print("hello")') == {}
