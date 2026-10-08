import csv,hashlib,json
import pytest
from nba_mike.data.injury_table_diagnostic import group_lines,summarize_page,analyze_rows,run,DATE,MATCHUP

def w(x,y,t):return (x,y,x+max(10,len(t)*5),y+10,t,0,0,0)

def test_empty_lines():assert group_lines([])==[]
def test_group_same_row():assert len(group_lines([w(1,10,'A'),w(40,10,'B')]))==1
def test_separate_rows():assert len(group_lines([w(1,10,'A'),w(1,30,'B')]))==2
def test_words_sorted():assert group_lines([w(30,10,'B'),w(1,10,'A')])[0]['text']=='A B'
def test_page_context_tokens():
 p=summarize_page(1,612,792,[w(1,10,'MIA@CLE'),w(1,30,'QUESTIONABLE')]);assert p['matchup_lines']==1 and p['status_lines']==1
def test_header_detected():assert summarize_page(1,612,792,[w(1,10,'Player Name')])['header_lines']==1
def test_nearest_matchup_not_assignment():
 p=summarize_page(2,612,792,[w(1,10,'MIA@CLE'),w(1,30,'Some Player')]);r=[{'source_page':'2','source_y':'35','player':'Some Player','status':'OUT','team':'','matchup':'','game_date':''}]
 f=analyze_rows(r,[p]);assert f[0]['nearby_matchup_text']=='MIA@CLE' and f[0]['diagnosis'].endswith('REQUIRES_VISUAL_REVIEW')
def test_no_matchup():
 p=summarize_page(2,612,792,[w(1,10,'Player')]);r=[{'source_page':'2','source_y':'15','player':'P','team':'','matchup':'','game_date':''}]
 assert analyze_rows(r,[p])[0]['diagnosis']=='NO_PAGE_MATCHUP_TOKEN'
def test_complete_record_skipped():
 p=summarize_page(1,612,792,[]);r=[{'source_page':'1','source_y':'10','game_date':'2026-03-27','matchup':'MIA@CLE','team':'Miami Heat'}]
 assert analyze_rows(r,[p])==[]
def test_invalid_row_coordinates_skipped():
 p=summarize_page(1,612,792,[]);assert analyze_rows([{'source_page':'x','source_y':'?','team':''}],[p])==[]
def test_trace_count():
 p=summarize_page(1,612,792,[]);r=[{'source_page':'1','source_y':'10','game_date':'','matchup':'','team':''}]
 assert analyze_rows(r,[p],[{'source_page':'1','source_y':'15'}])[0]['candidate_reason_lines']==1
def test_hash_mismatch_blocks(tmp_path):
 import pymupdf
 pdf=tmp_path/'a.pdf';d=pymupdf.open();d.new_page();d.save(pdf);d.close()
 csvpath=tmp_path/'rows.csv';csvpath.write_text('source_sha256,source_page,source_y,player\nwrong,1,1,X\n')
 with pytest.raises(ValueError,match='hash'):run(pdf,csvpath,tmp_path/'out')
def test_real_synthetic_pdf_end_to_end(tmp_path):
 import pymupdf
 pdf=tmp_path/'a.pdf';d=pymupdf.open();p=d.new_page();p.insert_text((30,50),'MIA@CLE');p.insert_text((30,75),'QUESTIONABLE');d.save(pdf);d.close()
 sha=hashlib.sha256(pdf.read_bytes()).hexdigest();csvpath=tmp_path/'rows.csv'
 with csvpath.open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=['source_sha256','source_page','source_y','player','status','game_date','matchup','team']);writer.writeheader();writer.writerow(dict(source_sha256=sha,source_page=1,source_y=72,player='Test Player',status='QUESTIONABLE',game_date='',matchup='',team=''))
 result=run(pdf,csvpath,tmp_path/'out',render_pages=True)
 assert result['missing_context_records']==1 and result['original_records_modified']==0
 assert len(result['rendered_pages'])==1 and (tmp_path/'out'/f'{sha}.s7_10_context_findings.csv').exists()
 assert result['eligible_for_asof_training'] is False
