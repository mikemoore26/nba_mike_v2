import hashlib
from pathlib import Path
import pytest
from nba_mike.data.injury_pdf import acquire_and_audit, conservative_candidates, extract_pdf_text, fetch_pdf
URL='https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-03-27_06_30AM.pdf'
def pdf_bytes():
    fitz=pytest.importorskip('fitz')
    d=fitz.open(); p=d.new_page();p.insert_text((70,70),'Player One Questionable - Ankle');p.insert_text((70,95),'Player Two Out - Knee')
    b=d.tobytes();d.close();return b

def test_extract_pages():
    pages=extract_pdf_text(pdf_bytes())
    assert len(pages)==1 and 'Questionable' in pages[0]['text']
def test_candidates_not_verified():
    rows=conservative_candidates(extract_pdf_text(pdf_bytes()))
    assert len(rows)==2
    assert all(r['review_status']=='NEEDS_MANUAL_SCHEMA_VALIDATION' for r in rows)
def test_acquire_quarantines(tmp_path):
    b=pdf_bytes();r=acquire_and_audit(URL,tmp_path,data=b,fetched_at_utc='2026-10-07T12:00:00Z')
    assert r['sha256']==hashlib.sha256(b).hexdigest()
    assert Path(r['pdf_path']).read_bytes()==b
    assert not r['eligible_for_asof_training']
    assert (tmp_path/(r['sha256']+'.audit.json')).exists()
def test_bad_bytes_rejected(tmp_path):
    with pytest.raises(ValueError): acquire_and_audit(URL,tmp_path,data=b'not pdf')
def test_naive_timestamp_rejected(tmp_path):
    with pytest.raises(ValueError): acquire_and_audit(URL,tmp_path,data=pdf_bytes(),fetched_at_utc='2026-10-07T12:00:00')
def test_unapproved_host_rejected(tmp_path):
    with pytest.raises(ValueError): acquire_and_audit('https://example.com/referee/injury/Injury-Report_2026-03-27_06_30AM.pdf',tmp_path,data=pdf_bytes())
def test_no_network_for_invalid_url():
    with pytest.raises(ValueError): fetch_pdf('http://example.com/file.pdf')
def test_empty_candidates():
    assert conservative_candidates([{'page':1,'text':'No injury updates'}])==[]
