import csv,hashlib,importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('s815',ROOT/'research/p0_s8/s8_15/run_s8_15.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def setup(tmp_path,rows):
    b=tmp_path/'research/p0_s8/s8_15';(b/'artifacts').mkdir(parents=True)
    with (b/'evidence_intake.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['source_url','artifact_relative_path','sha256','document_claimed_timestamp','independent_capture_url','independent_capture_timestamp','notes']);w.writeheader();w.writerows(rows)
    return b

def test_no_evidence_blocks(tmp_path):
    setup(tmp_path,[]);r=m.inspect(tmp_path);assert r['decision']=='BLOCK_TRAINING' and r['independently_verified_games']==0

def test_fake_claimed_capture_never_certifies(tmp_path):
    b=setup(tmp_path,[]);p=b/'artifacts/doc.pdf';p.write_bytes(b'%PDF-1.4\ntest')
    with (b/'evidence_intake.csv').open('a',newline='') as f:
        csv.writer(f).writerow([m.URL,'doc.pdf',hashlib.sha256(p.read_bytes()).hexdigest(),'2023-10-24T17:30:00-04:00','https://example.org/archive','2023-10-24T18:00:00-04:00',''])
    r=m.inspect(tmp_path);assert r['candidate_manual_review']==1 and r['independently_verified_artifacts']==0 and r['decision']=='BLOCK_TRAINING'

def test_checksum_mismatch_rejected(tmp_path):
    b=setup(tmp_path,[dict(source_url=m.URL,artifact_relative_path='doc.pdf',sha256='0'*64,document_claimed_timestamp='2023-10-24T17:30:00-04:00',independent_capture_url='',independent_capture_timestamp='',notes='')]);(b/'artifacts/doc.pdf').write_bytes(b'hello')
    m.inspect(tmp_path);assert 'SHA256_MISSING_OR_MISMATCH' in (b/'results/s8_15_evidence_review.csv').read_text()

def test_path_escape_rejected(tmp_path):
    b=setup(tmp_path,[dict(source_url=m.URL,artifact_relative_path='../../outside',sha256='',document_claimed_timestamp='',independent_capture_url='',independent_capture_timestamp='',notes='')]);m.inspect(tmp_path);assert 'MISSING_OR_UNSAFE_ARTIFACT_PATH' in (b/'results/s8_15_evidence_review.csv').read_text()

def test_timestamp_rules():
    assert m.iso('2023-10-24T17:30:00') is None
    assert m.iso('2023-10-24T17:30:00-04:00') is not None
