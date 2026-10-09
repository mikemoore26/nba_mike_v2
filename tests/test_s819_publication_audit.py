import csv
import hashlib
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'research/p0_s8/s8_19/run_s8_19.py'
spec = importlib.util.spec_from_file_location('s819', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def test_capture_before_tipoff():
    assert mod.parse_capture_timestamp('2023-10-24T22:00:00Z') < mod.TIPOFF.astimezone(mod.timezone.utc)

def test_capture_after_tipoff():
    assert mod.parse_capture_timestamp('2023-10-25T00:00:00Z') > mod.TIPOFF.astimezone(mod.timezone.utc)

def test_naive_time_rejected():
    assert mod.parse_capture_timestamp('2023-10-24T18:00:00') is None

def test_path_escape_rejected(tmp_path):
    try:
        mod.safe_repo_path(tmp_path, '../secret')
    except ValueError:
        return
    assert False, 'path escape accepted'

def test_html_metadata(tmp_path):
    p = tmp_path / 'a.html'
    p.write_text('<meta property="article:published_time" content="2023-10-23T18:00:00Z"><time datetime="2023-10-23"></time>')
    typ, claims = mod.extract_claims(p)
    assert typ == 'HTML' and len(claims) == 2

def test_missing_evidence_blocks(tmp_path):
    p = tmp_path / 'research/p0_s8/s8_18/results'
    p.mkdir(parents=True)
    with (p / 's8_18_source_audit.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['source_id','artifact_path','retrieval_status','sha256'])
        w.writeheader()
        w.writerow({'source_id':'denver_team_preview','artifact_path':'notfound.html'})
        w.writerow({'source_id':'nba_0630_report','artifact_path':'notfound.pdf'})
    report = mod.run(tmp_path)
    assert report['decision']=='BLOCK_TRAINING'
    assert report['artifacts_hash_verified']==0
    assert report['independently_verified_games']==0

def test_claims_not_certification(tmp_path):
    p = tmp_path / 'research/p0_s8/s8_18/results'
    p.mkdir(parents=True)
    artifact = tmp_path / 'source.html'
    artifact.write_text('<meta property="article:published_time" content="2023-10-23T18:00:00Z">')
    with (p / 's8_18_source_audit.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['source_id','artifact_path','retrieval_status','sha256'])
        w.writeheader()
        w.writerow({'source_id':'denver_team_preview','artifact_path':'source.html','sha256':hashlib.sha256(artifact.read_bytes()).hexdigest()})
        w.writerow({'source_id':'nba_0630_report','artifact_path':'notfound.pdf'})
    report = mod.run(tmp_path)
    assert report['artifacts_hash_verified']==1
    assert report['publisher_metadata_claims']==1
    assert report['independently_verified_captures']==0
