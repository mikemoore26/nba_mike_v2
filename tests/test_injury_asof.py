import pytest
from nba_mike.data.injury_asof import parse_official_url,select_asof,verify_pdf_bytes,audit_registry
BASE='https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-03-27_06_30AM.pdf'
def test_et_dst():
    assert parse_official_url(BASE)['report_time_utc']=='2026-03-27T10:30:00+00:00'
def test_nonstandard_minutes():
    assert parse_official_url('https://ak-static.cms.nba.com/referee/injury/Injury-Report_2025-10-27_07PM.pdf')['report_time_utc']=='2025-10-27T23:00:00+00:00'
@pytest.mark.parametrize('url',['http://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-03-27_06_30AM.pdf','https://evil.com/referee/injury/Injury-Report_2026-03-27_06_30AM.pdf','https://ak-static.cms.nba.com/referee/injury/other.pdf'])
def test_reject_bad_url(url):
    with pytest.raises(ValueError):parse_official_url(url)
def test_asof_rejects_late_obtained():
    v={'url':BASE,'sha256':'a'*64,'available_at_utc':'2026-03-27T12:00:00Z'}
    assert select_asof([v],'2026-03-27T11:00:00Z') is None
    assert select_asof([v],'2026-03-27T13:00:00Z')==v
def test_registry_is_unverified_without_provenance():
    assert audit_registry([{'url':BASE}])['verified_for_historical_asof']==0
def test_pdf_header():
    with pytest.raises(ValueError):verify_pdf_bytes(b'not pdf')
    assert len(verify_pdf_bytes(b'%PDF-1.7\n'))==64
