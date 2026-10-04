from __future__ import annotations

import csv
import hashlib
import json
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any, Iterable


class SnapshotError(ValueError):
    pass


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(str(value)[:10])
    except Exception as exc:
        raise SnapshotError(f"Invalid ISO event/game date: {value!r}") from exc


def _json_sha(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _parent_fields(parent_manifest: dict[str, Any]) -> tuple[str, str, str]:
    status = str(parent_manifest.get("validation_status", "")).upper()
    if status != "PASS":
        raise SnapshotError(f"Parent validation_status must be PASS, got {status or 'MISSING'}")
    artifact_id = str(parent_manifest.get("artifact_id", "")).strip()
    sha256 = str(parent_manifest.get("sha256", "")).strip().lower()
    relative_path = str(parent_manifest.get("relative_path", "")).strip()
    if not artifact_id or not sha256 or not relative_path:
        raise SnapshotError("Parent manifest missing artifact_id, sha256, or relative_path")
    return artifact_id, sha256, relative_path


def verify_parent(parent_manifest: dict[str, Any], artifact_path: str | Path) -> None:
    _, expected, _ = _parent_fields(parent_manifest)
    actual = _file_sha(Path(artifact_path))
    if actual != expected:
        raise SnapshotError("Parent SHA-256 verification failed")


def build_d1_snapshot(
    rows: Iterable[dict[str, Any]],
    *,
    target_game_date: str,
    parent_manifest: dict[str, Any],
    parent_artifact_path: str | Path,
    expected_entities: Iterable[dict[str, Any]] | None = None,
    code_git_commit: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    target = _parse_date(target_game_date)
    cutoff = target.fromordinal(target.toordinal() - 1)
    verify_parent(parent_manifest, parent_artifact_path)
    parent_id, parent_sha, _ = _parent_fields(parent_manifest)

    materialized = [dict(r) for r in rows]
    required = {"game_id", "event_date", "player_id", "team_id"}
    seen: set[tuple[str, str]] = set()

    for row in materialized:
        missing = sorted(c for c in required if not str(row.get(c, "")).strip())
        if missing:
            raise SnapshotError(f"Canonical row missing required fields: {missing}")
        key = (str(row["game_id"]), str(row["player_id"]))
        if key in seen:
            raise SnapshotError(f"Duplicate canonical player-game key: {key}")
        seen.add(key)
        _parse_date(str(row["event_date"]))

    eligible = [
        r for r in materialized
        if _parse_date(str(r["event_date"])) <= cutoff
    ]
    eligible.sort(key=lambda r: (
        str(r["event_date"]), str(r["game_id"]), str(r["team_id"]), str(r["player_id"])
    ))

    entity_history: list[dict[str, Any]] = []
    if expected_entities is not None:
        for ent in expected_entities:
            pid = str(ent.get("player_id", "")).strip()
            tid = str(ent.get("team_id", "")).strip()
            if not pid or not tid:
                raise SnapshotError("Expected entity requires player_id and team_id")
            count = sum(1 for r in eligible if str(r["player_id"]) == pid)
            entity_history.append({
                "player_id": pid,
                "team_id": tid,
                "eligible_game_count": count,
                "history_status": "AVAILABLE" if count else "ZERO_HISTORY",
            })
        entity_history.sort(key=lambda x: (x["team_id"], x["player_id"]))

    logical = {
        "contract": "D-1",
        "target_game_date": target.isoformat(),
        "cutoff_date": cutoff.isoformat(),
        "parent_artifact_id": parent_id,
        "parent_sha256": parent_sha,
        "rows": eligible,
        "entity_history": entity_history,
    }
    logical_sha = _json_sha(logical)
    snapshot_id = f"d1-{target.isoformat()}-{logical_sha[:16]}"
    as_of = datetime.combine(cutoff, time(23, 59, 59), tzinfo=timezone.utc).isoformat()

    metadata = {
        "snapshot_version": "1",
        "snapshot_id": snapshot_id,
        "contract": "D-1",
        "target_game_date": target.isoformat(),
        "cutoff_date": cutoff.isoformat(),
        "as_of_time": as_of,
        "parent_artifact_id": parent_id,
        "parent_sha256": parent_sha,
        "row_count": len(eligible),
        "logical_sha256": logical_sha,
        "code_git_commit": code_git_commit,
        "entity_history": entity_history,
    }
    return eligible, metadata


def write_snapshot(
    rows: list[dict[str, Any]],
    metadata: dict[str, Any],
    output_dir: str | Path,
) -> tuple[Path, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / f"{metadata['snapshot_id']}.csv"
    manifest_path = out / f"{metadata['snapshot_id']}.manifest.json"

    fields = sorted({k for row in rows for k in row})
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        if fields:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
        else:
            f.write("")

    payload = dict(metadata)
    payload["snapshot_file_sha256"] = _file_sha(csv_path)
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return csv_path, manifest_path
