from nba_mike.data.injury_layout import parse_word_pages

def w(x,y,s):return (x,y,x+max(8,len(s)*5),y+9,s,0,0,0)
def header():return [w(120,0,'Team'),w(220,0,'Player'),w(275,0,'Name'),w(380,0,'Current'),w(440,0,'Status'),w(530,0,'Reason')]
def record(y=20):return [w(220,y,'Smith,'),w(265,y,'Jane'),w(440,y,'Out'),w(530,y,'Injury/Illness'),w(610,y,'Knee')]
def ctx(y=20):return [w(10,y,'03/27/2026'),w(70,y,'LAC@IND'),w(120,y,'LA'),w(145,y,'Clippers')]
def pg(i,words,width=750):return {'page':i,'words':words,'width':width}

def test_reuse_header_columns_on_page_two():
 rows,d=parse_word_pages([pg(1,header()+ctx()+record()),pg(2,ctx()+record())],'abc')
 assert len(rows)==2
 assert d['pages_using_inherited_columns']==[2]
 assert rows[1]['player']=='Jane Smith'
 assert 'INHERITED_COLUMN_LAYOUT_UNVERIFIED' in rows[1]['flags']
 assert rows[1]['eligible_for_asof_training'] is False

def test_no_cross_page_team_carry():
 rows,_=parse_word_pages([pg(1,header()+ctx()+record()),pg(2,record())],'abc')
 assert rows[1]['team']=='' and rows[1]['game_date']==''
 assert 'TEAM_UNRESOLVED' in rows[1]['flags']

def test_width_mismatch_abstains():
 rows,d=parse_word_pages([pg(1,header()+ctx()+record()),pg(2,ctx()+record(),width=600)],'abc')
 assert len(rows)==1 and d['pages_layout_mismatch']==[2]

def test_orphan_reason_not_attached():
 words=header()+[w(530,12,'Unattached')]+ctx()+record()
 rows,d=parse_word_pages([pg(1,words)],'abc')
 assert d['orphan_continuations']>=1
 assert 'Unattached' not in rows[0]['reason']

def test_continuation_joins_nearby():
 words=header()+ctx()+record()+[w(530,31,'Soreness')]
 rows,d=parse_word_pages([pg(1,words)],'abc')
 assert 'Soreness' in rows[0]['reason'] and d['continuation_lines']>=1

def test_new_matchup_clears_team():
 words=header()+ctx()+record()+[w(10,45,'ATL@BOS')]+record(60)
 rows,_=parse_word_pages([pg(1,words)],'abc')
 assert len(rows)==2 and rows[1]['team']==''

def test_page_diagnostics_totals():
 rows,d=parse_word_pages([pg(1,header()+ctx()+record()),pg(2,ctx()+record())],'abc')
 assert sum(x['records'] for x in d['per_page'])==len(rows)
 assert len(d['per_page'])==2

def test_no_header_anywhere_abstains():
 rows,d=parse_word_pages([pg(1,record()),pg(2,record())],'abc')
 assert rows==[] and len(d['pages_without_header'])==2
