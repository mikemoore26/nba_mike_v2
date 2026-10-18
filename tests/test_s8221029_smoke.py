import importlib.util
from pathlib import Path
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'research/p0_s8/s8_22_10_29/run_smoke.py'
spec = importlib.util.spec_from_file_location('s829_smoke', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def fixture_root(tmp_path):
    (tmp_path / 'pyproject.toml').write_text('[project]\nname="sample"\n', encoding='utf8')
    (tmp_path / 'src/nba_mike').mkdir(parents=True)
    return tmp_path

def test_default_never_executes(tmp_path):
    r = mod.run(fixture_root(tmp_path))
    assert not r['all_smoke_passed']
    assert all(s['status'] == 'MISSING_TEST' for s in r['suites'])

def test_missing_root_rejected(tmp_path):
    with pytest.raises(ValueError): mod.run(tmp_path)

def test_inventory_does_not_approve(tmp_path):
    r = mod.run(fixture_root(tmp_path))
    assert r['real_money_approval'] == 'DENIED'
    assert r['training_decision'] == 'BLOCK_TRAINING'

def test_five_explicit_suites():
    assert len(mod.SUITES) == 5
    assert all(all(x.startswith('tests/test_') for x in v) for v in mod.SUITES.values())

def test_inventory_ready_when_tests_present(tmp_path):
    root = fixture_root(tmp_path)
    for paths in mod.SUITES.values():
        for p in paths:
            f = root / p; f.parent.mkdir(exist_ok=True); f.write_text('def test_ok(): assert True\n')
    r = mod.run(root)
    assert all(x['status'] == 'READY_NOT_EXECUTED' for x in r['suites'])
    assert not r['all_smoke_passed']
