import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import pytest

SOURCE = Path(__file__).resolve().parents[1]/'research/p0_s8/s8_22_7_3/run_s8_22_7_3.py'
spec = importlib.util.spec_from_file_location('s82273', SOURCE)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


def sample(game_id, home, away, start):
    url=f'https://www.nba.com/game/example-{game_id}'
    event={'@type':'SportsEvent','startDate':start,'homeTeam':{'alternateName':home},'awayTeam':{'alternateName':away}}
    return url, f'<html><head><link rel="canonical" href="{url}"><script type="application/ld+json">{json.dumps(event)}</script></head></html>'.encode()


def receipt(root, date, game_id, home, away, start):
    url, content = sample(game_id, home, away, start)
    folder=root/'research/p0_s8/s8_22_7_2/evidence'/date/game_id
    folder.mkdir(parents=True)
    source=folder/'source.bin';source.write_bytes(content)
    metadata=dict(date=date,source_url=url,retrieved_utc='2026-10-10T00:00:00+00:00',sha256=hashlib.sha256(content).hexdigest(),bytes=len(content),evidence_path=source.relative_to(root).as_posix())
    p=folder/'receipt.json';p.write_text(json.dumps(metadata));return p


def two(root):
    a=receipt(root,'2023-10-24','0022300061','DEN','LAL','2023-10-24T19:30:00-04:00')
    b=receipt(root,'2023-10-24','0022300062','GSW','PHX','2023-10-24T22:00:00-04:00')
    return a,b


def test_two_game_build(tmp_path):
    a,b=two(tmp_path);result=mod.build(tmp_path,'2023-10-24',[a,b]);assert result['official_games']==2
    assert result['date_completeness']=='NOT_CERTIFIED';assert not result['training_eligible']
    import csv
    with (tmp_path/result['reference_path']).open() as f:rows=list(csv.DictReader(f))
    assert [r['official_nba_game_id'] for r in rows]==['0022300061','0022300062']
    assert rows[0]['evidence_sha256']!=rows[1]['evidence_sha256']
    assert rows[1]['tipoff_utc']=='2023-10-25T02:00:00Z'


def test_duplicate_rejected(tmp_path):
    a,b=two(tmp_path)
    with pytest.raises(ValueError,match='DUPLICATE'):mod.build(tmp_path,'2023-10-24',[a,a])


def test_tamper_rejected(tmp_path):
    a,b=two(tmp_path);(a.parent/'source.bin').write_bytes(b'altered')
    with pytest.raises(ValueError,match='HASH_MISMATCH'):mod.build(tmp_path,'2023-10-24',[a,b])


def test_wrong_date_rejected(tmp_path):
    a,b=two(tmp_path)
    with pytest.raises(ValueError,match='RECEIPT_DATE'):mod.build(tmp_path,'2023-10-25',[a,b])


def test_bad_game_date_in_source_rejected(tmp_path):
    a=receipt(tmp_path,'2023-10-24','0022300061','DEN','LAL','2023-10-25T19:30:00-04:00')
    with pytest.raises(ValueError,match='STRUCTURED_GAME'):mod.build(tmp_path,'2023-10-24',[a])


def test_non_nba_url_rejected():
    with pytest.raises(ValueError,match='NBA_OFFICIAL'):mod.nba_url('https://nba.com.evil.org/game/x')


def test_no_receipts_rejected(tmp_path):
    with pytest.raises(ValueError,match='NO_RECEIPTS'):mod.build(tmp_path,'2023-10-24',[])


def test_outside_receipt_rejected(tmp_path):
    other=tmp_path.parent/'outside_receipt.json';other.write_text('{}')
    try:
        with pytest.raises(ValueError,match='RECEIPT_OUTSIDE'):mod.build(tmp_path,'2023-10-24',[other])
    finally:other.unlink()


def test_no_automatic_manifest_update(tmp_path):
    a,b=two(tmp_path);mod.build(tmp_path,'2023-10-24',[a,b])
    assert not (tmp_path/'research/p0_s8/s8_22_7/date_manifest.csv').exists()


def test_multiple_sources_are_distinct(tmp_path):
    a,b=two(tmp_path);r=mod.build(tmp_path,'2023-10-24',[a,b]);assert r['source_receipts']==2


def test_missing_structured_event(tmp_path):
    a=receipt(tmp_path,'2023-10-24','0022300061','DEN','LAL','2023-10-24T19:30:00-04:00')
    content=b'<html><link rel="canonical" href="https://www.nba.com/game/example-0022300061"></html>'
    (a.parent/'source.bin').write_bytes(content)
    meta=json.loads(a.read_text());meta['sha256']=hashlib.sha256(content).hexdigest();meta['bytes']=len(content);a.write_text(json.dumps(meta))
    with pytest.raises(ValueError,match='STRUCTURED_GAME_MISSING'):mod.build(tmp_path,'2023-10-24',[a])
