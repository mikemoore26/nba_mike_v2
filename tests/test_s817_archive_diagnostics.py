import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'research/p0_s8/s8_17/run_s8_17.py'
spec = importlib.util.spec_from_file_location('s817', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_empty_cdx_is_valid():
    assert module.parse_cdx_bytes(b'[]\n') == ([], 'VALID_EMPTY_CDX_ARRAY')


def test_invalid_json_rejected():
    assert module.parse_cdx_bytes(b'not json')[1] == 'MALFORMED_JSON'


def test_index_candidate_never_verified():
    item = {'timestamp': '20231024220000', 'original': module.OFFICIAL}
    assert module.classify(item) == 'CANDIDATE_PRE_TIPOFF_CAPTURE'


def test_post_tipoff():
    assert module.classify({'timestamp': '20231025000000', 'original': module.OFFICIAL}) == 'POST_TIPOFF'


def test_wrong_url_rejected():
    assert module.classify({'timestamp': '20231024220000', 'original': 'https://example.org/'}) == 'REJECTED'


def test_offline_run_blocks(tmp_path):
    report = module.run(tmp_path, False)
    assert report['decision'] == 'BLOCK_TRAINING'
    assert report['sources_attempted'] == 0
    assert not report['independently_verified_publication']
    assert (tmp_path / 'research/p0_s8/s8_17/results/s8_17_report.json').exists()


def test_previous_empty_response_classified(tmp_path):
    prev = tmp_path / 'research/p0_s8/s8_16/artifacts'
    prev.mkdir(parents=True)
    (prev / 'wayback_cdx.json').write_bytes(b'[]\n')
    report = module.run(tmp_path)
    assert report['previous_s816_json_artifacts'][0]['cdx_parse_status'] == 'VALID_EMPTY_CDX_ARRAY'


def test_endpoints_approved_hosts():
    from urllib.parse import urlparse
    assert all(urlparse(url).hostname in {'web.archive.org', 'archive.org'} for _, url in module.endpoints())
