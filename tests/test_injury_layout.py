from nba_mike.data.injury_layout import word_lines,infer_columns,cells,parse_word_pages

def w(x,y,s):return (x,y,x+max(8,len(s)*5),y+9,s,0,0,0)
def header(y=0):return [w(120,y,'Team'),w(220,y,'Player'),w(275,y,'Name'),w(380,y,'Current'),w(440,y,'Status'),w(530,y,'Reason')]
def base(y=20):return [w(220,y,'Smith,'),w(265,y,'Jane'),w(440,y,'Out'),w(530,y,'Injury/Illness'),w(600,y,'-'),w(620,y,'Knee;')]
def page(words):return [{'page':1,'words':words}]
def test_group():assert len(word_lines([w(10,1,'a'),w(40,1,'b'),w(10,20,'c')]))==2
def test_header():assert infer_columns(word_lines(header())) is not None
def test_cells():
 c=cells(word_lines(base())[0],{'team':120,'player':220,'status':440,'reason':530});assert 'Smith' in c['player']
def test_no_header_abstains():
 rows,d=parse_word_pages(page(base()),'x');assert rows==[] and d['pages_without_header']==[1]
def test_parse_row():
 words=header()+[w(10,20,'03/27/2026'),w(70,20,'LAC@IND'),w(120,20,'LA'),w(145,20,'Clippers')]+base()
 rows,d=parse_word_pages(page(words),'x');assert len(rows)==1;assert rows[0]['player']=='Jane Smith';assert rows[0]['eligible_for_asof_training'] is False
def test_missing_reason():
 words=header()+[w(220,20,'Smith,'),w(265,20,'Jane'),w(440,20,'Out')]
 rows,_=parse_word_pages(page(words),'x');assert 'REASON_UNRESOLVED' in rows[0]['flags']
def test_reason_continuation():
 words=header()+base()+[w(530,31,'Soreness')]
 rows,d=parse_word_pages(page(words),'x');assert 'Soreness' in rows[0]['reason'] and d['continuation_lines']==1
def test_page_context_reset():
 words=header()+[w(10,20,'03/27/2026'),w(70,20,'LAC@IND'),w(120,20,'LA'),w(145,20,'Clippers')]+base()
 rows,_=parse_word_pages([{'page':1,'words':words},{'page':2,'words':header()+base()}],'x')
 assert len(rows)==2 and rows[1]['team']==''
