import importlib.util
from pathlib import Path

P=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_7_12/run_s8_22_7_12.py'
spec=importlib.util.spec_from_file_location('s822712',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
GAMES=[('Dallas','Washington'),('Boston','Philadelphia'),('Milwaukee','Toronto'),('New York','Atlanta'),('Orlando','Chicago'),('Minnesota','Phoenix'),('Sacramento','LA Lakers'),('Cleveland','Portland')]
def html(games=GAMES):
    return ('<table><tr><td>NBA REGULAR SEASON</td><td>TIME ET</td></tr>'+''.join(f'<tr><td>{a} at {b}</td><td>7:30pm</td></tr>' for a,b in games)+'<tr><td>NHL REGULAR SEASON</td></tr></table>').encode()
def prior():
    return {'date':'2023-11-15','game_agreement':'PASS','reconstructed_matches':[{'away_team':m.CITY[a],'home_team':m.CITY[b]} for a,b in GAMES]}
def test_eight_match():
    r=m.audit(html(),prior()); assert r['matchups_agree'] and not r['issues']
    assert r['date_completeness']=='NOT_CERTIFIED' and r['decision']=='BLOCK_TRAINING'
def test_missing_match_blocked():
    r=m.audit(html(GAMES[:-1]),prior()); assert 'EIGHT_GAME_COUNT_MISMATCH' in r['issues']
def test_wrong_team_blocked():
    g=GAMES.copy();g[0]=('Boston','Washington'); assert 'MATCHUP_SET_MISMATCH' in m.audit(html(g),prior())['issues']
def test_missing_section_blocked():
    r=m.audit(b'<table><tr><td>Dallas at Washington</td></tr></table>',prior()); assert 'NBA_SECTION_NOT_FOUND' in r['issues']
def test_bad_prior_blocked():
    p=prior();p['game_agreement']='FAIL';assert 'PRIOR_GOVERNANCE_NOT_VALID' in m.audit(html(),p)['issues']
