"""Regression tests against S7.17.1 PDF-coordinate diagnostic evidence."""
import json
from pathlib import Path
import pytest
from nba_mike.data.injury_reason_recovery import recover_page

FIXTURES=json.loads((Path(__file__).parent/'fixtures/s7171_reason_geometry.json').read_text())

@pytest.mark.parametrize('case',FIXTURES,ids=[f"{i:02d}_{r['player'].replace(' ','_')}" for i,r in enumerate(FIXTURES)])
def test_actual_pdf_geometry(case):
    y=case['y']
    words=[(x,wy-1,x+len(t)*3,wy+1,t,0,0,0) for x,wy,t in case['words']]
    rows=[{'record_id':'sample','source_sha256':'fixture','source_page':1,
           'source_y':y,'player':case['player'],'status':'OUT','reason':''}]
    result=recover_page(rows,words,case['width'])[0]
    assert result['decision']=='PROPOSED_REVIEW_REQUIRED', result
    assert result['proposed_reason'].startswith('Injury/Illness - ')
    assert result['evidence_y_min']!=''

def test_neighbor_prefix_not_borrowed():
    def w(x,y,t): return (x,y-1,x+len(t)*3,y+1,t,0,0,0)
    rows=[{'record_id':str(y),'source_sha256':'x','source_page':1,
           'source_y':y,'player':p,'status':'OUT','reason':''} for y,p in [(100,'A'),(120,'B')]]
    words=[w(667,113,'Injury/Illness'),w(722,113,'-'),w(727,113,'Knee')]
    result=recover_page(rows,words)
    assert result[0]['decision']=='UNRESOLVED'
    assert result[1]['decision']=='PROPOSED_REVIEW_REQUIRED'

def test_outside_reason_lane_unresolved():
    r={'record_id':'1','source_sha256':'x','source_page':1,'source_y':100,
       'player':'A','status':'OUT','reason':''}
    words=[(600,92,630,94,'Injury/Illness',0,0,0)]
    assert recover_page([r],words)[0]['decision']=='UNRESOLVED'
