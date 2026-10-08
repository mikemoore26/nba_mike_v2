import importlib.util,json,csv,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_27/run_s7_27.py'
spec=importlib.util.spec_from_file_location('s727',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
HTML=b'<html><body><h2>Knicks add player (Feb. 5)</h2><p>New York receives:</p><ul><li>Jose Alvarado</li><li>Two second-round picks</li></ul><p>Official release: Knicks</p></body></html>'
def test_extract_provisional():
 c=m.extract_candidates(HTML,'a'*64,'2026-10-08T00:00:00+00:00');assert c and all(x['evidence_class']=='UNVERIFIED_TEXT_CANDIDATE' for x in c)
def test_no_auto_qualification(tmp_path):
 p=tmp_path/'input.html';p.write_bytes(HTML);r=m.run(tmp_path/'out',p);assert r['qualified_s726_events']==0 and r['decision']=='BLOCK_TRAINING'
def test_preserves_raw_sha(tmp_path):
 p=tmp_path/'input.html';p.write_bytes(HTML);r=m.run(tmp_path/'out',p);assert (tmp_path/'out/objects'/(hashlib.sha256(HTML).hexdigest()+'.html')).read_bytes()==HTML
def test_rejects_non_html(tmp_path):
 p=tmp_path/'bad';p.write_bytes(b'not html')
 try:m.run(tmp_path/'out',p)
 except ValueError:return
 assert False
