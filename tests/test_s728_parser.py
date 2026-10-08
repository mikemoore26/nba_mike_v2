import csv,hashlib,importlib.util
from pathlib import Path
import pytest
S=Path(__file__).resolve().parents[1]/'research/p0_s4/s7_28/run_s7_28.py'
spec=importlib.util.spec_from_file_location('s728',S);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def fixtures(tmp_path,items=None):
    html=tmp_path/'source.html';html.write_text('<html><body>test</body></html>');sha=hashlib.sha256(html.read_bytes()).hexdigest()
    rows=items or [('Trade announced (Feb. 5)','New York receives:','Jose Alvarado (via New Orleans)')]
    csvfile=tmp_path/'candidates.csv';fields=['event_date','destination_team_text','player_text','source_url','source_sha256','retrieved_utc']
    with csvfile.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for section,dest,player in rows:w.writerow(dict(zip(fields,[section,dest,player,m.SOURCE_URL,sha,'2026-10-08T23:39:00+00:00'])))
    return csvfile,html
def test_date():assert m.parse_date('Foo (Feb. 5)')=='2026-02-05'
def test_date_fail_closed():assert m.parse_date('Foo (Feb. 31)')==''
def test_team():assert m.destination('New York receives:')=='NYK'
def test_unicode():assert m.norm('Nikola Vučević')==m.norm('Nikola Vucevic')
def test_no_id_no_promotion(tmp_path):
    csvfile,html=fixtures(tmp_path);r,rows=m.inspect(csvfile,html,output_dir=tmp_path/'out');assert r['input_candidates']==1 and r['qualified_s726_events']==0 and rows[0]['from_team']=='NOP' and not rows[0]['player_id']
def test_asset_excluded(tmp_path):
    c,h=fixtures(tmp_path,[('Trade (Feb. 5)','New York receives:','Three future second-round picks')]);r,rows=m.inspect(c,h);assert r['non_player_assets']==1 and not rows[0]['player_name']
def test_source_mismatch(tmp_path):
    c,h=fixtures(tmp_path);h.write_text('<html>changed</html>')
    with pytest.raises(ValueError,match='provenance'):m.inspect(c,h)
def test_ids_still_review(tmp_path):
    c,h=fixtures(tmp_path);ids=tmp_path/'ids.csv';ids.write_text('player_id,player_name,source_url\n1628988,Jose Alvarado,https://stats.nba.com/\n')
    r,rows=m.inspect(c,h,ids);assert rows[0]['player_id']=='1628988' and r['qualified_s726_events']==0 and r['review_only_structured']==1
def test_ambiguous_ids(tmp_path):
    c,h=fixtures(tmp_path);ids=tmp_path/'ids.csv';ids.write_text('player_id,player_name,source_url\n1,Jose Alvarado,https://stats.nba.com/\n2,Jose Alvarado,https://stats.nba.com/\n')
    r,rows=m.inspect(c,h,ids);assert not rows[0]['player_id']
def test_unknown_origin(tmp_path):
    c,h=fixtures(tmp_path,[('Trade (Feb. 5)','New York receives:','Jose Alvarado')]);r,rows=m.inspect(c,h);assert 'NO_EXPLICIT_ORIGIN' in rows[0]['review_reason']
