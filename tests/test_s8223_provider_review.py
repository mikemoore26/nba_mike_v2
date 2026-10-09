import csv
import importlib.util
import json
from pathlib import Path

P=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_3/run_s8_22_3.py'
spec=importlib.util.spec_from_file_location('s8223',P); mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def test_candidate_count(): assert len(mod.SOURCES)==3
def test_preferred(): assert mod.decide_provider(mod.SOURCES)=='balldontlie'
def test_no_candidate(): assert mod.decide_provider([mod.SOURCES[-1]])=='NONE'
def test_no_approved(): assert all(s['live_validation']!='APPROVED' for s in mod.SOURCES)
def test_blocked_cdn(): assert mod.SOURCES[-1]['recommendation']=='DO_NOT_RETRY'
def test_no_secrets(): assert all('key' not in s for s in mod.SOURCES)
def test_gates(): assert len(mod.GATES)==9
def test_report(tmp_path):
 r=mod.audit(tmp_path);assert r['decision']=='BLOCK_TRAINING' and r['live_network_requests']==0
 assert r['approved_live_providers']==[]
def test_csv(tmp_path):
 mod.audit(tmp_path)
 p=tmp_path/'research/p0_s8/s8_22_3/results/s8_22_3_provider_matrix.csv'
 with p.open(newline='') as f: assert len(list(csv.DictReader(f)))==3
def test_all_gates_pending(tmp_path):
 mod.audit(tmp_path)
 p=tmp_path/'research/p0_s8/s8_22_3/results/s8_22_3_acceptance_gates.csv'
 with p.open(newline='') as f: assert all(x['status']=='PENDING_EVIDENCE' for x in csv.DictReader(f))
def test_report_serializable(tmp_path):
 mod.audit(tmp_path);p=tmp_path/'research/p0_s8/s8_22_3/results/s8_22_3_report.json'
 assert json.loads(p.read_text())['status']=='RESEARCH_ONLY'
