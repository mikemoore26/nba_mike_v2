import csv,hashlib
import pytest
from nba_mike.data.injury_ground_truth import choose,grade,build_packet,REVIEW

def row(sha,page,name):
    return {'sha256':sha,'source_page':str(page),'player':name,'date_provenance':'EXPLICIT:p1:y2','matchup_provenance':'EXPLICIT:p1:y2','team_provenance':'EXPLICIT:p1:y2'}

def test_choose_deterministic():
    a=[row('a',1,'A'),row('a',2,'B'),row('a',2,'C'),row('b',1,'D')]
    assert choose(a,2)==choose(list(reversed(a)),2)
def test_choose_coverage():
    assert len(choose([row('a',1,'A'),row('a',2,'B'),row('a',3,'C')],2))==2
def test_choose_per_report():
    assert len(choose([row('a',1,'A'),row('b',1,'B')],1))==2
def test_choose_invalid():
    with pytest.raises(ValueError):choose([],0)
def test_choose_empty():assert choose([])==[]
def write_csv(path,fields,rows):
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def test_grade_pending(tmp_path):
    a=tmp_path/'a.csv';b=tmp_path/'b.csv';write_csv(a,['sample_id'],[{'sample_id':'X'}]);write_csv(b,REVIEW,[{'sample_id':'X'}]);assert grade(a,b)['status']=='REVIEW_PENDING'
def test_grade_complete(tmp_path):
    a=tmp_path/'a.csv';b=tmp_path/'b.csv';write_csv(a,['sample_id'],[{'sample_id':'X'}]);write_csv(b,REVIEW,[{'sample_id':'X',**{k:'YES' for k in REVIEW if k.endswith('_correct')}}]);assert grade(a,b)['status']=='REVIEW_COMPLETE'
def test_grade_no(tmp_path):
    a=tmp_path/'a.csv';b=tmp_path/'b.csv';write_csv(a,['sample_id'],[{'sample_id':'X'}]);write_csv(b,REVIEW,[{'sample_id':'X',**{k:'NO' for k in REVIEW if k.endswith('_correct')}}]);assert grade(a,b)['field_counts']['player_correct']['NO']==1
def test_grade_mismatch(tmp_path):
    a=tmp_path/'a.csv';b=tmp_path/'b.csv';write_csv(a,['sample_id'],[{'sample_id':'X'}]);write_csv(b,REVIEW,[{'sample_id':'Y'}]);
    with pytest.raises(ValueError):grade(a,b)
def test_grade_invalid(tmp_path):
    a=tmp_path/'a.csv';b=tmp_path/'b.csv';write_csv(a,['sample_id'],[{'sample_id':'X'}]);write_csv(b,REVIEW,[{'sample_id':'X','player_correct':'MAYBE'}]);
    with pytest.raises(ValueError):grade(a,b)
def test_build_missing_dirs(tmp_path):
    with pytest.raises(ValueError):build_packet(tmp_path/'absent',tmp_path,tmp_path/'out')
def test_build_invalid_count(tmp_path):
    with pytest.raises(ValueError):build_packet(tmp_path,tmp_path,tmp_path/'out',0)
def test_build_one_pdf(tmp_path):
    pymupdf=pytest.importorskip('pymupdf')
    p=tmp_path/'pdf';p.mkdir();c=tmp_path/'c';c.mkdir();out=tmp_path/'out'
    doc=pymupdf.open();page=doc.new_page(width=842,height=595);page.insert_text((20,100),'Test Player');raw=doc.tobytes();doc.close()
    sha=hashlib.sha256(raw).hexdigest();(p/(sha+'.pdf')).write_bytes(raw)
    fields=['source_sha256','source_page','source_y','player','status','team','matchup','game_date','reason']
    write_csv(c/(sha+'.s7_14_candidates.csv'),fields,[{'source_sha256':sha,'source_page':1,'source_y':100,'player':'Test Player','status':'OUT','team':'Test','matchup':'AAA@BBB','game_date':'2026-03-27','reason':'Test'}])
    result=build_packet(p,c,out,2)
    assert result['sampled_records']==1 and (out/'GT001.png').exists()
    assert grade(out/'s7_16_samples.csv',out/'s7_16_blind_review.csv')['status']=='REVIEW_PENDING'
