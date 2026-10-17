import importlib.util,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_9/run_s8_22_10_9.py'
spec=importlib.util.spec_from_file_location('s822109',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def sample(gid='0022300192',away=1610612742,home=1610612764,date='2023-11-15'):
 return json.dumps({'game':{'gameId':gid,'gameDate':date,'awayTeam':{'teamId':away},'homeTeam':{'teamId':home}}}).encode()
def test_match():assert m.inspect(sample(),'0022300192','2023-11-15','DAL@WAS')[0]=='CONTENT_MATCH'
def test_wrong_game_id():assert m.inspect(sample(gid='0022300193'),'0022300192','2023-11-15','DAL@WAS')[0]=='GAME_ID_MISMATCH'
def test_wrong_teams():assert m.inspect(sample(away=1610612738),'0022300192','2023-11-15','DAL@WAS')[0]=='TEAM_MISMATCH'
def test_wrong_date():assert m.inspect(sample(date='2023-11-16'),'0022300192','2023-11-15','DAL@WAS')[0]=='DATE_MISMATCH'
def test_missing_date():
 obj=json.loads(sample());del obj['game']['gameDate'];assert m.inspect(json.dumps(obj).encode(),'0022300192','2023-11-15','DAL@WAS')[0]=='DATE_NOT_CHECKED'
def test_invalid_json():assert m.inspect(b'bad','0022300192','2023-11-15','DAL@WAS')[0]=='INVALID_JSON'
def test_missing_schema():assert m.inspect(b'{}','0022300192','2023-11-15','DAL@WAS')[0]=='INVALID_SCHEMA'
def test_offline_eight(tmp_path):
 cw=[{'game_date':'2023-11-15','away_at_home':k,'provisional_nba_game_id':f'002230019{i}','game_id_status':'UNVERIFIED_PROVISIONAL'} for i,k in enumerate(['DAL@WAS','NYK@ATL','BOS@PHI','MIL@TOR','ORL@CHI','MIN@PHX','SAC@LAL','CLE@POR'],2)]
 rows=m.process(cw,tmp_path,False,2)
 assert len(rows)==8 and all(x['acquisition_status']=='NOT_ATTEMPTED' for x in rows)
def test_existing_snapshot(tmp_path):
 d=tmp_path/'0022300192';d.mkdir();(d/'nba_cdn_boxscore.json').write_bytes(sample())
 cw=[{'game_date':'2023-11-15','away_at_home':k,'provisional_nba_game_id':f'002230019{i}','game_id_status':'UNVERIFIED_PROVISIONAL'} for i,k in enumerate(['DAL@WAS','NYK@ATL','BOS@PHI','MIL@TOR','ORL@CHI','MIN@PHX','SAC@LAL','CLE@POR'],2)]
 rows=m.process(cw,tmp_path,False,2);assert rows[0]['content_status']=='CONTENT_MATCH'
