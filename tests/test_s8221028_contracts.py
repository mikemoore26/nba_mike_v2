import importlib.util
from pathlib import Path
import pytest

FILE=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_28/audit_contracts.py'
spec=importlib.util.spec_from_file_location('contract_audit_28',FILE)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def test_static_no_execution(tmp_path):
 root=tmp_path;src=root/'src/nba_mike/features';src.mkdir(parents=True)
 (src/'opportunity.py').write_text('raise RuntimeError("MUST NOT EXECUTE")\n\ndef build(x):\n return x\n')
 (root/'tests').mkdir();(root/'tests/test_opportunity.py').write_text('def test_ok(): pass')
 result=mod.run(root,root/'audit',6)
 assert result['selected_count']==1
 assert result['components'][0]['functions'][0]['parameters']==['x']
 assert result['real_money_approval']=='DENIED'

def test_outside_root_denied(tmp_path):
 with pytest.raises(ValueError):mod.run(tmp_path,tmp_path.parent/'outside',6)

def test_skips_sensitive_dirs(tmp_path):
 (tmp_path/'.venv').mkdir();(tmp_path/'.venv/secret.py').write_text('pass')
 (tmp_path/'data').mkdir();(tmp_path/'data/secret.py').write_text('pass')
 assert mod.run(tmp_path,tmp_path/'audit',6)['total_python_files_in_scope']==0

def test_parse_failure_is_nonfatal(tmp_path):
 p=tmp_path/'src/nba_mike/models';p.mkdir(parents=True)
 (p/'predict.py').write_text('def broken(:')
 assert mod.run(tmp_path,tmp_path/'audit',6)['components'][0]['parse_status']=='PARSE_FAILED'

def test_limit_guard(tmp_path):
 with pytest.raises(ValueError):mod.run(tmp_path,tmp_path/'audit',101)
