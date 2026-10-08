import hashlib
import json
import pytest
from nba_mike.data.injury_acquire import validate_url, fetch_pdf, acquire, MAX_BYTES

BASE='https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-03-27_06_30AM.pdf'
PDF=b'%PDF-1.4\nhello\n%%EOF\n'
class FakeResponse:
    def __init__(self,raw=PDF,url=BASE): self.raw=raw;self.url=url
    def __enter__(self): return self
    def __exit__(self,*a): pass
    def read(self,n): return self.raw[:n]
    def geturl(self): return self.url

def fake(req,timeout): return FakeResponse()

@pytest.mark.parametrize('url',[
 'http://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-03-27_06_30AM.pdf',
 'https://evil.example/referee/injury/Injury-Report_2026-03-27_06_30AM.pdf',
 'https://ak-static.cms.nba.com.evil.example/referee/injury/Injury-Report_2026-03-27_06_30AM.pdf',
 'https://ak-static.cms.nba.com/referee/injury/../../secret.pdf',
 BASE+'?q=1', BASE+'#fragment',
 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-03-27_06_30AM.pdf/other',
])
def test_reject_bad_urls(url):
    with pytest.raises(ValueError): validate_url(url)

def test_allow_official(): assert validate_url(BASE)==BASE

def test_fetch_valid(): assert fetch_pdf(BASE,opener=fake)==(PDF,BASE)

def test_reject_html():
    with pytest.raises(ValueError,match='complete PDF'):
        fetch_pdf(BASE,opener=lambda *a,**kw: FakeResponse(b'<html>no</html>'))

def test_reject_truncated():
    with pytest.raises(ValueError,match='complete PDF'):
        fetch_pdf(BASE,opener=lambda *a,**kw: FakeResponse(b'%PDF-1.4\n'))

def test_reject_large():
    with pytest.raises(ValueError,match='maximum'):
        fetch_pdf(BASE,opener=lambda *a,**kw: FakeResponse(b'%PDF-'+b'x'*MAX_BYTES+b'%%EOF'))

def test_redirect_rejected():
    with pytest.raises(ValueError): fetch_pdf(BASE,opener=lambda *a,**kw: FakeResponse(url='https://evil.example/x.pdf'))

def test_download_and_duplicate(tmp_path):
    out=acquire([BASE],tmp_path/'pdf',tmp_path/'results',opener=fake)
    assert out['downloaded']==1 and out['failed']==0
    assert (tmp_path/'pdf'/(hashlib.sha256(PDF).hexdigest()+'.pdf')).read_bytes()==PDF
    out2=acquire([BASE],tmp_path/'pdf',tmp_path/'results',opener=fake)
    assert out2['duplicates']==1 and out2['downloaded']==0
    assert out2['eligible_for_asof_training'] is False
    assert json.loads((tmp_path/'results'/'s7_15_acquisition.json').read_text())['decision']=='BLOCK_TRAINING'

def test_failure_logged(tmp_path):
    def fail(req,timeout): raise OSError('offline')
    out=acquire([BASE],tmp_path/'pdf',tmp_path/'results',opener=fail)
    assert out['failed']==1 and out['entries'][0]['status']=='FETCH_FAILED'

def test_invalid_before_network(tmp_path):
    called=[]
    def opener(req,timeout): called.append(1);return FakeResponse()
    with pytest.raises(ValueError): acquire([BASE,'https://evil.example/a.pdf'],tmp_path/'pdf',tmp_path/'results',opener=opener)
    assert not called

def test_duplicate_manifest_rejected(tmp_path):
    with pytest.raises(ValueError,match='Duplicate URLs'):
        acquire([BASE,BASE],tmp_path/'pdf',tmp_path/'results',opener=fake)

def test_more_than_twelve_rejected(tmp_path):
    with pytest.raises(ValueError): acquire([BASE]*13,tmp_path/'pdf',tmp_path/'results',opener=fake)
