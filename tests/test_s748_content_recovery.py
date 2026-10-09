import csv,hashlib,importlib.util
from pathlib import Path
M=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_48/run_s7_48.py'
spec=importlib.util.spec_from_file_location('s748',M);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_digest():assert m.digest(b'abc')==hashlib.sha256(b'abc').hexdigest()
def test_title():assert any(k=='TITLE' for k,_,_ in m.extract(b'<title>Trade report</title>'))
def test_meta():assert any(k=='META_OG:TITLE' for k,_,_ in m.extract(b'<meta property="og:title" content="Trade report">'))
def test_jsonld():assert any(k=='JSON_LD_HEADLINE' for k,_,_ in m.extract(b'<script type="application/ld+json">{"headline":"Warriors acquire Kristaps Porzingis"}</script>'))
def test_body():assert any(k=='PARAGRAPH' for k,_,_ in m.extract(b'<p>Body sentence</p>'))
def test_slug_not_content():
 s=m.classify([], 'Buddy Hield','GSW','ATL','https://nba.com/hawks-acquire-buddy-hield-from-golden-state')
 assert s[0]=='PLAYER_ONLY_IN_URL' and s[-1]=='false'
def test_missing_player():assert m.classify([('PARAGRAPH','Other player','p:0')],'Buddy Hield','GSW','ATL','https://nba.com/x')[0]=='PLAYER_NOT_IN_CAPTURE_CONTENT'
def test_full_claim():
 x=m.classify([('PARAGRAPH','Atlanta Hawks acquire Buddy Hield from Golden State Warriors.','p:0')],'Buddy Hield','GSW','ATL','https://nba.com/x')
 assert x[0]=='LOCAL_CLAIM_CANDIDATE_REVIEW_ONLY' and x[-1]=='true'
def test_player_only():assert m.classify([('PARAGRAPH','Buddy Hield played.','p:0')],'Buddy Hield','GSW','ATL','https://nba.com/x')[0]=='PARTIAL_CONTENT_REVIEW_ONLY'
def test_no_proposal():assert m.classify([],'','','','https://nba.com/x')[0]=='NO_DIRECTION_PROPOSAL'
def test_team_word_boundaries():assert not m.team('wizardry','WAS')
def test_team_alias():assert m.team('The Clippers traded Ivica Zubac','LAC')
def test_no_false_action():assert not m.action('tradeoffs are complex')
def test_url_normalization():assert m.norm_url('https://www.nba.com/x/')==m.norm_url('https://nba.com/x')
def test_missing_capture(tmp_path):
 inp=tmp_path/'in.csv';out=tmp_path/'out'
 with inp.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['article_url','source_capture_status','evidence_status']);w.writeheader();w.writerow({'article_url':'https://nba.com/x','source_capture_status':'CAPTURE_FETCH_FAILED','evidence_status':'NO_SAVED_CAPTURE'})
 result=m.process(inp,tmp_path/'objects',out)
 assert result['recovery_status_counts']['NO_SAVED_CAPTURE']==1 and result['eligible_for_asof_training'] is False
