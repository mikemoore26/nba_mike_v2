"""Append-only prospective evidence capture; never marks historical publication verified."""
from __future__ import annotations
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ALLOWED_HOST = "ak-static.cms.nba.com"
MAX_BYTES = 20 * 1024 * 1024


def validate_url(url: str) -> None:
    p = urlparse(url)
    if p.scheme != "https" or p.hostname != ALLOWED_HOST or p.username or p.password or p.port is not None:
        raise ValueError("Only HTTPS official NBA static host URLs are accepted")
    if not p.path.startswith("/referee/injury/Injury-Report_") or not p.path.endswith(".pdf") or p.query or p.fragment:
        raise ValueError("Expected an official injury-report PDF path without query/fragment")


def record_capture(data: bytes, url: str, root: Path, captured_at: datetime | None = None) -> dict:
    validate_url(url)
    if not data.startswith(b"%PDF-") or len(data) > MAX_BYTES:
        raise ValueError("Invalid or oversized PDF")
    now = captured_at or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Capture time must have timezone")
    captured = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    sha = hashlib.sha256(data).hexdigest()
    root = Path(root)
    objects = root / "objects"
    objects.mkdir(parents=True, exist_ok=True)
    target = objects / (sha + ".pdf")
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest() != sha:
            raise RuntimeError("Existing object has unexpected hash")
    else:
        import tempfile
        with tempfile.NamedTemporaryFile(dir=objects, prefix=".incoming_", delete=False) as temp:
            temp.write(data)
            temp.flush()
            os.fsync(temp.fileno())
            tmp = Path(temp.name)
        try:
            if target.exists():
                if hashlib.sha256(target.read_bytes()).hexdigest() != sha:
                    raise RuntimeError("Existing object has unexpected hash")
            else:
                os.replace(tmp, target)
        finally:
            tmp.unlink(missing_ok=True)
    event = {
        "schema_version": 1, "source_url": url, "captured_at_utc": captured,
        "sha256": sha, "size_bytes": len(data), "object_path": "objects/" + sha + ".pdf",
        "evidence_type": "local_retrieval", "historical_publication_verified": False,
        "eligible_for_asof_training": False, "decision": "BLOCK_TRAINING",
    }
    root.mkdir(parents=True, exist_ok=True)
    with (root / "capture_events.jsonl").open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return event


def fetch_and_capture(url: str, root: Path, timeout: float = 20) -> dict:
    validate_url(url)
    req = Request(url, headers={"User-Agent": "NBA-MIKE-Research/0.1", "Accept": "application/pdf"})
    with urlopen(req, timeout=timeout) as response:
        final_url = response.geturl()
        validate_url(final_url)
        if final_url != url:
            raise ValueError("Redirected URL differs from requested URL")
        data = response.read(MAX_BYTES + 1)
        # Clock recorded immediately after bytes received, never backdated to the report label.
        at = datetime.now(timezone.utc)
    return record_capture(data, url, root, at)
