import csv
import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'research/p0_s4/s7_46/run_s7_46.py'
spec=importlib.util.spec_from_file_location('s746',SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def test_sha(): assert len(m.sha256(b'a'))==64
def test_exact_url(): assert m.exact_url_match('https://www.nba.com/news/x/','https://nba.com/news/x')
def test_url_reject_different(): assert not m.exact_url_match('https://nba.com/news/a','https://nba.com/news/b')
def test_timestamp_valid(): assert m.valid_timestamp('20260205010000')
def test_timestamp_invalid_calendar(): assert not m.valid_timestamp('20260231010000')
def test_timestamp_invalid_format(): assert not m.valid_timestamp('20260205')
def test_parse_cdx():
    x=json.dumps([['timestamp','original','statuscode','digest','mimetype'],['20260206010101','https://nba.com/news/x','200','a','text/html']])
    assert len(m.parse_cdx(x))==1
def test_parse_empty(): assert m.parse_cdx('[]')==[]
def test_parse_missing_columns():
    try: m.parse_cdx('[ ["timestamp"] ]')
    except ValueError: return
    assert False
def test_replay(): assert '20260205010000id_' in m.replay_url('20260205010000','https://nba.com/news/x')
def test_player_mention(): assert m.check_claim(b'<p>Tyus Jones joined the team</p>','Tyus Jones')=='PLAYER_MENTION_ONLY'
def test_missing_player(): assert m.check_claim(b'<p>Other news</p>','Tyus Jones')=='NO_PLAYER_MENTION'
def test_script_removed(): assert m.check_claim(b'<script>Tyus Jones</script><p>Other</p>','Tyus Jones')=='NO_PLAYER_MENTION'
def test_offline(tmp_path):
    inp=tmp_path/'in.csv';out=tmp_path/'results'
    with inp.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['article_url','article_sha256','player_names','preferred_publication_candidate']);w.writeheader();w.writerow(dict(article_url='https://www.nba.com/news/x',article_sha256='abc',player_names='Tyus Jones',preferred_publication_candidate='2026-02-05'))
    result=m.process(inp,out,offline=True)
    assert result['decision']=='BLOCK_TRAINING'
    assert result['archive_status_counts']=={'NOT_QUERIED_OFFLINE':1}
    assert (out/'s7_46_review.csv').exists()
def test_non_nba_rejected(tmp_path):
    inp=tmp_path/'in.csv'
    inp.write_text('article_url\nhttps://example.org/x\n')
    try:m.process(inp,tmp_path/'out',offline=True)
    except ValueError:return
    assert False
