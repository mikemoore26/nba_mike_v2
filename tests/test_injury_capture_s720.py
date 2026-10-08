import hashlib
import json
from datetime import datetime, timezone
import pytest
from nba_mike.data.injury_capture import record_capture, validate_url

URL = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-03-27_06_30AM.pdf"


def test_url_allowlist():
    validate_url(URL)
    for bad in ["http://ak-static.cms.nba.com/referee/injury/Injury-Report_a.pdf", "https://example.com/referee/injury/Injury-Report_a.pdf", "https://ak-static.cms.nba.com/other.pdf", URL + "?x=1"]:
        with pytest.raises(ValueError):
            validate_url(bad)


def test_capture_preserves_bytes_and_audit_event(tmp_path):
    data = b"%PDF-1.4\nexample"
    t = datetime(2026, 10, 8, 20, 0, tzinfo=timezone.utc)
    event = record_capture(data, URL, tmp_path, t)
    assert (tmp_path / event["object_path"]).read_bytes() == data
    assert event["sha256"] == hashlib.sha256(data).hexdigest()
    assert event["captured_at_utc"] == "2026-10-08T20:00:00Z"
    assert not event["historical_publication_verified"]
    assert not event["eligible_for_asof_training"]


def test_repeat_capture_appends_event_not_object(tmp_path):
    for _ in range(2):
        record_capture(b"%PDF-1.4\ntest", URL, tmp_path)
    assert len(list((tmp_path / "objects").glob("*.pdf"))) == 1
    assert len((tmp_path / "capture_events.jsonl").read_text().splitlines()) == 2


def test_invalid_bytes_and_naive_timestamp_rejected(tmp_path):
    with pytest.raises(ValueError):
        record_capture(b"not pdf", URL, tmp_path)
    with pytest.raises(ValueError):
        record_capture(b"%PDF-1.4", URL, tmp_path, datetime(2026, 3, 27))
