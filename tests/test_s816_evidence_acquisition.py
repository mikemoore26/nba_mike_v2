import importlib.util
import json
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / 'research/p0_s8/s8_16/run_s8_16.py'
spec = importlib.util.spec_from_file_location('s816', MODULE)
s816 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s816)


def test_no_network_default(tmp_path):
    report = s816.audit(tmp_path)
    assert report['network_opt_in'] is False
    assert report['decision'] == 'BLOCK_TRAINING'
    assert report['independently_verified_games'] == 0
    assert (tmp_path / 'research/p0_s8/s8_16/results/s8_16_report.json').exists()


def test_pre_tipoff_archive_candidate_is_not_verified(tmp_path):
    base = tmp_path / 'research/p0_s8/s8_16/artifacts'
    base.mkdir(parents=True)
    (base / 'wayback_cdx_response.json').write_text(json.dumps([
        ['timestamp', 'original', 'statuscode'],
        ['20231024200000', s816.OFFICIAL, '200'],
        ['20231025000000', s816.OFFICIAL, '200']
    ]), encoding='utf-8')
    report = s816.audit(tmp_path)
    assert report['archive_pre_tipoff_candidates'] == 1
    assert report['independently_verified_publication'] is False
    assert report['verdict'] == 'UNVERIFIED'


def test_bad_original_rejected():
    row = s816.archive_review([{'timestamp': '20231024200000', 'original': 'https://evil.example/a.pdf'}])[0]
    assert row['index_verdict'] == 'REJECTED'


def test_invalid_cdx_fails_closed(tmp_path):
    path = tmp_path / 'bad.json'
    path.write_text('{broken', encoding='utf-8')
    rows, error = s816.parse_cdx(path)
    assert not rows and error == 'CDX_PARSE_FAILED'


def test_fake_pdf_is_not_valid(tmp_path):
    path = tmp_path / 'file.pdf'
    path.write_bytes(b'not a pdf')
    assert not s816.pdf_metadata(path)['pdf_signature_valid']


def test_disallowed_host(tmp_path):
    import pytest
    with pytest.raises(ValueError, match='DISALLOWED_SOURCE_HOST'):
        s816.fetch('https://evil.example/file', tmp_path / 'file')


def test_existing_evidence_never_overwritten(tmp_path):
    import pytest
    path = tmp_path / 'file'
    path.write_bytes(b'preserved')
    with pytest.raises(FileExistsError):
        s816.fetch(s816.OFFICIAL, path)
    assert path.read_bytes() == b'preserved'
