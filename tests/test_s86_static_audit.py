import importlib.util
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / 'research/p0_s8/s8_6/run_s8_6.py'
spec = importlib.util.spec_from_file_location('s86', PATH)
s86 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s86)

def make(tmp_path, source):
    p = tmp_path/'src/nba_mike/features/feature.py'
    p.parent.mkdir(parents=True)
    p.write_text(source)
    return p

def test_negative_shift(tmp_path):
    x = s86.inspect_file(make(tmp_path, 'def f(df):\n return df.shift(-1)\n'), tmp_path)
    assert any(z['rule']=='NEGATIVE_SHIFT' for z in x['findings'])

def test_rolling(tmp_path):
    x = s86.inspect_file(make(tmp_path, 'def f(df):\n return df.rolling(5)\n'), tmp_path)
    assert x['findings'][0]['function']=='f'

def test_centered(tmp_path):
    x = s86.inspect_file(make(tmp_path, 'x = df.rolling(3, center=True)\n'), tmp_path)
    assert any(z['rule']=='CENTERED_ROLLING' for z in x['findings'])

def test_no_false_certification(tmp_path):
    make(tmp_path, 'x = 1\n')
    report = s86.audit(tmp_path)
    assert report['decision']=='BLOCK_TRAINING' and report['confirmed_leakage_count']==0

def test_syntax_error(tmp_path):
    x = s86.inspect_file(make(tmp_path, 'def f(:\n'), tmp_path)
    assert not x['parsed'] and x['findings'][0]['rule']=='SYNTAX_ERROR'

def test_missing_roots(tmp_path):
    report = s86.audit(tmp_path)
    assert report['audit_completeness']=='PARTIAL_SOURCE_SCOPE'

def test_comments_ignored(tmp_path):
    x = s86.inspect_file(make(tmp_path, '# df.shift(-1)\nx = 1\n'), tmp_path)
    assert not x['findings']

def test_source_hash(tmp_path):
    x = s86.inspect_file(make(tmp_path, 'x=1\n'), tmp_path)
    assert len(x['sha256'])==64

def test_random_split(tmp_path):
    x = s86.inspect_file(make(tmp_path, 'x = train_test_split(data)\n'), tmp_path)
    assert any(z['rule']=='RANDOM_SPLIT' for z in x['findings'])

def test_findings_are_review_only(tmp_path):
    make(tmp_path, 'x = df.shift(-1)\n')
    report = s86.audit(tmp_path)
    assert all(f['classification']=='REVIEW_REQUIRED_NOT_CONFIRMED' for f in report['findings'])
