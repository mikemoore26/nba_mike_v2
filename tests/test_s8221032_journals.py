"""Check journal updater formatting, idempotency and missing-file safety."""
import importlib.util
from pathlib import Path
import pytest

SCRIPT=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10_32/update_journals.py'
spec=importlib.util.spec_from_file_location('s832_journals',SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def test_appends_without_whitespace_error(tmp_path):
    p=tmp_path/'journal.md'
    p.write_text('Prior entry\n\n\n')
    assert module.update(p,'## New\nLine\n')=='APPENDED'
    assert p.read_text()=='Prior entry\n\n'+module.MARKER+'\n## New\nLine\n'

def test_idempotent(tmp_path):
    p=tmp_path/'journal.md';p.write_text('Prior entry\n')
    module.update(p,'## New\n');original=p.read_bytes()
    assert module.update(p,'## New\n')=='ALREADY_PRESENT'
    assert p.read_bytes()==original

def test_missing_file_fails_closed(tmp_path):
    with pytest.raises(FileNotFoundError): module.update(tmp_path/'missing.md','New')
