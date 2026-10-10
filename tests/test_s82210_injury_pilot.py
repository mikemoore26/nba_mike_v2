import importlib.util
from pathlib import Path
from datetime import datetime, timezone
import pytest

PATH=Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_10/run_s8_22_10.py'
spec=importlib.util.spec_from_file_location('pilot',PATH)
pilot=importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)

def test_eight_games():
    assert len(pilot.GAME_TIPOFFS)==8

def test_edition_et_to_utc():
    dt=pilot.edition_from_text('Injury Report: 11/15/23 05:30 PM')
    assert dt==datetime(2023,11,15,22,30,tzinfo=timezone.utc)

def test_edition_no_header():
    assert pilot.edition_from_text('no matching report') is None

def test_sha():
    assert pilot.sha256(b'abc')=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'

def test_bad_pdf():
    with pytest.raises(ValueError,match='Not a PDF'):
        pilot.inspect_pdf(b'not a pdf')

def test_empty_pdf_rejected():
    with pytest.raises(ValueError,match='Not a PDF'):
        pilot.inspect_pdf(b'')

def test_status_constants():
    assert 'QUESTIONABLE' in pilot.VALID_STATUSES
