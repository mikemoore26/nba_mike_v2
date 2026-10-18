import importlib.util
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / 'research/p0_s8/s8_22_10_27/run_s8_22_10_27.py'
spec = importlib.util.spec_from_file_location('s827', MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def test_static_scan_no_execution(tmp_path):
    (tmp_path / 'runner.py').write_text('import argparse\nif __name__ == "__main__":\n    raise RuntimeError("MUST NOT EXECUTE")\n')
    report = mod.scan(tmp_path)
    assert report['potential_cli_count'] == 1
    assert report['readiness']['real_money_approval'] == 'DENIED'
    assert report['python_files'][0]['runtime_checked'] is False

def test_syntax_error_is_reported(tmp_path):
    (tmp_path / 'bad.py').write_text('def broken(:\n')
    assert len(mod.scan(tmp_path)['parse_errors']) == 1

def test_skips_results_and_venv(tmp_path):
    (tmp_path / '.venv').mkdir()
    (tmp_path / '.venv' / 'other.py').write_text('pass')
    (tmp_path / 'results').mkdir()
    (tmp_path / 'results' / 'other.py').write_text('pass')
    assert mod.scan(tmp_path)['python_file_count'] == 0

def test_detects_model_artifact_but_does_not_validate(tmp_path):
    (tmp_path / 'example.joblib').write_bytes(b'not a model')
    result = mod.scan(tmp_path)
    assert result['model_artifact_count_in_scanned_paths'] == 1
    assert result['model_artifacts'][0]['validated_for_inference'] is False

def test_no_training_approval(tmp_path):
    report = mod.scan(tmp_path)
    assert report['training_decision'] == 'BLOCK_TRAINING'
    assert report['research_status'] == 'RESEARCH_ONLY'
