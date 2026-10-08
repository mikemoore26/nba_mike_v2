import importlib.util
from pathlib import Path
import pytest

MODULE = Path(__file__).resolve().parents[1] / 'research/p0_s4/s7_19/run_s7_19.py'
spec = importlib.util.spec_from_file_location('s719_audit', MODULE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_empty_directory_fails(tmp_path):
    with pytest.raises(ValueError, match='No PDFs'):
        audit.audit_directory(tmp_path)


def test_fake_pdf_fails(tmp_path):
    path=tmp_path/'fake.pdf';path.write_bytes(b'not pdf')
    with pytest.raises(ValueError, match='Not a PDF'):
        audit.audit_pdf(path)


def test_valid_pdf_never_proves_publication(tmp_path):
    import pymupdf
    path=tmp_path/'one.pdf'
    d=pymupdf.open();p=d.new_page();p.insert_text((72,72),'NBA Injury Report');d.set_metadata({'creationDate':'D:20260325063000'});d.save(path);d.close()
    result=audit.audit_directory(tmp_path)
    assert result['pdf_count']==1
    assert result['pdfs_with_internal_timestamp']==1
    assert result['decision']=='BLOCK_TRAINING'
    assert result['historical_publication_verified'] is False
    assert result['reports'][0]['historical_publication_verified'] is False
    assert result['reports'][0]['eligible_for_asof_training'] is False


def test_duplicate_content_not_distinct(tmp_path):
    import pymupdf
    d=pymupdf.open();d.new_page();raw=d.tobytes();d.close()
    (tmp_path/'a.pdf').write_bytes(raw);(tmp_path/'b.pdf').write_bytes(raw)
    result=audit.audit_directory(tmp_path)
    assert result['pdf_count']==2
    assert result['distinct_hashes']==1
    assert result['decision']=='BLOCK_TRAINING'
