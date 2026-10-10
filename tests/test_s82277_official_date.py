import importlib.util,hashlib,json
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_7_7/run_s8_22_7_7.py'
spec=importlib.util.spec_from_file_location('audit',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def fixture(tmp_path):
    src=tmp_path/'evidence/source.bin';src.parent.mkdir();src.write_bytes(b'<script id="__NEXT_DATA__" type="application/json">'+json.dumps({'props':{'pageProps':{'gameCardFeed':{'modules':[{'cards':[{'cardData':{'gameId':'123','homeTeam':{'teamTricode':'DEN'},'awayTeam':{'teamTricode':'LAL'},'gameTimeUtc':'2023-11-16T00:00:00Z'}}]}]}}}}).encode()+b'</script>')
    r={'date':'2023-11-15','source_url':'https://www.nba.com/games?date=2023-11-15','evidence_path':'evidence/source.bin','sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'bytes':src.stat().st_size,'retrieved_utc':'2026-10-10T01:00:00Z'}
    receipt=tmp_path/'receipt.json';receipt.write_text(json.dumps(r));return receipt,src,r
def test_extract(tmp_path):
    receipt,src,r=fixture(tmp_path);result=m.run(tmp_path,'2023-11-15',receipt);assert result['official_game_count']==1;assert result['decision']=='BLOCK_TRAINING'
def test_bad_hash(tmp_path):
    receipt,src,r=fixture(tmp_path);src.write_bytes(src.read_bytes()+b'x')
    with pytest.raises(ValueError):m.verify(tmp_path,receipt,'2023-11-15')
def test_bad_date(tmp_path):
    receipt,src,r=fixture(tmp_path)
    with pytest.raises(ValueError):m.verify(tmp_path,receipt,'2023-11-16')
def test_bad_url(tmp_path):
    receipt,src,r=fixture(tmp_path);r['source_url']='https://evil.example/games?date=2023-11-15';receipt.write_text(json.dumps(r))
    with pytest.raises(ValueError):m.verify(tmp_path,receipt,'2023-11-15')
def test_traversal(tmp_path):
    receipt,src,r=fixture(tmp_path);r['evidence_path']='../source.bin';receipt.write_text(json.dumps(r))
    with pytest.raises(ValueError):m.verify(tmp_path,receipt,'2023-11-15')
def test_missing_next_data():
    with pytest.raises(ValueError):m.games_from_html(b'<html></html>')
def test_duplicate_games(tmp_path):
    receipt,src,r=fixture(tmp_path);b=src.read_bytes();d=json.loads(b.split(b'>',1)[1].split(b'</script>',1)[0]);cards=d['props']['pageProps']['gameCardFeed']['modules'][0]['cards'];cards.append(cards[0]);b=b'<script id="__NEXT_DATA__">'+json.dumps(d).encode()+b'</script>'
    with pytest.raises(ValueError):m.games_from_html(b)
def test_team_columns():
    assert m.provider_teams({'home_team':'DEN','away_team':'LAL'})==('DEN','LAL')
    assert m.provider_teams({'home_team_id':'8','away_team_id':'14'}) is None
