"""Governed canonical -> D-1 snapshot adapter (no API access, no model training).

The caller MUST pass a canonical artifact and its manifest. This adapter verifies
file integrity and strictly validates every row before invoking snapshot builder.
"""
from __future__ import annotations

import csv
import json
import math
from datetime import date
from pathlib import Path
from typing import Any

from nba_mike.snapshots.builder import build_d1_snapshot
from nba_mike.validation.invariants import (
    assert_d1_boundary, assert_team_opponent_consistency,
    assert_unique_keys, assert_snapshot_metadata,
)
from nba_mike.validation.provenance import sha256_file


class AdapterContractError(ValueError):
    """Input cannot be safely converted into a historical snapshot."""


CANONICAL_COLUMNS = (
    "game_id", "game_date", "player_id", "team_id", "opponent_team_id",
    "minutes", "points", "rebounds", "assists", "three_pointers_made",
)
NUMERIC = ("minutes", "points", "rebounds", "assists", "three_pointers_made")
FIELD_MAP = {
    "game_date": "event_date", "minutes": "min", "points": "pts",
    "rebounds": "reb", "assists": "ast", "three_pointers_made": "fg3m",
}


def _iso_date(value: str) -> str:
    try:
        result = date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise AdapterContractError(f"INVALID_GAME_DATE: {value!r}") from exc
    if result.isoformat() != value:
        raise AdapterContractError(f"NONCANONICAL_GAME_DATE: {value!r}")
    return result.isoformat()


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise AdapterContractError("MANIFEST_UNREADABLE") from exc
    if not isinstance(manifest, dict):
        raise AdapterContractError("MANIFEST_NOT_OBJECT")
    for field in ("artifact_id", "sha256", "relative_path", "validation_status"):
        if not isinstance(manifest.get(field), str) or not manifest[field].strip():
            raise AdapterContractError(f"MANIFEST_MISSING_{field.upper()}")
    if manifest["validation_status"].upper() != "PASS":
        raise AdapterContractError("PARENT_NOT_VALIDATED")
    if manifest.get("layer") != "canonical" or manifest.get("dataset_name") != "player_game_box":
        raise AdapterContractError("WRONG_PARENT_LAYER_OR_DATASET")
    return manifest


def adapt_canonical_rows(
    *, canonical_path: str | Path, canonical_manifest_path: str | Path,
    target_game_date: str, project_root: str | Path,
    expected_entities: list[dict[str, Any]] | None = None,
    code_git_commit: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return prior-date snapshot rows and metadata; never mutate input files.

    Note: A D-1 cutoff alone does not certify that each historical value was
    published by D-1. Source availability must be independently certified.
    """
    root = Path(project_root).resolve(strict=True)
    artifact = Path(canonical_path).resolve(strict=True)
    manifest_path = Path(canonical_manifest_path).resolve(strict=True)
    if not artifact.is_relative_to(root) or not manifest_path.is_relative_to(root):
        raise AdapterContractError("INPUT_OUTSIDE_PROJECT_ROOT")
    target = _iso_date(target_game_date)
    parent = _load_manifest(manifest_path)
    if (root / parent["relative_path"]).resolve() != artifact:
        raise AdapterContractError("MANIFEST_ARTIFACT_PATH_MISMATCH")
    if sha256_file(artifact).lower() != parent["sha256"].lower():
        raise AdapterContractError("PARENT_HASH_MISMATCH")
    try:
        with artifact.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None or len(set(reader.fieldnames)) != len(reader.fieldnames):
                raise AdapterContractError("INVALID_OR_DUPLICATE_HEADER")
            if set(reader.fieldnames) != set(CANONICAL_COLUMNS):
                raise AdapterContractError("CANONICAL_SCHEMA_MISMATCH")
            source_rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise AdapterContractError("CANONICAL_CSV_UNREADABLE") from exc
    if parent.get("row_count") != len(source_rows):
        raise AdapterContractError("MANIFEST_ROW_COUNT_MISMATCH")
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_rows, start=2):
        if None in row:
            raise AdapterContractError(f"EXTRA_CSV_VALUES_ROW_{index}")
        if any(value is None or not str(value).strip() for value in row.values()):
            raise AdapterContractError(f"NULL_CANONICAL_FIELD_ROW_{index}")
        result = {FIELD_MAP.get(key, key): value.strip() for key, value in row.items()}
        result["event_date"] = _iso_date(result["event_date"])
        for key in NUMERIC:
            mapped = FIELD_MAP[key]
            try:
                value = float(result[mapped])
            except (ValueError, TypeError) as exc:
                raise AdapterContractError(f"INVALID_NUMERIC_{mapped}_ROW_{index}") from exc
            if not math.isfinite(value) or value < 0 or (mapped == "min" and value > 60):
                raise AdapterContractError(f"OUT_OF_RANGE_{mapped}_ROW_{index}")
            result[mapped] = value
        rows.append(result)
    try:
        assert_unique_keys(rows)
        assert_team_opponent_consistency(rows)
        snapshot_rows, metadata = build_d1_snapshot(
            rows, target_game_date=target, parent_manifest=parent,
            parent_artifact_path=artifact, expected_entities=expected_entities,
            code_git_commit=code_git_commit,
        )
        assert_d1_boundary(snapshot_rows, target_game_date=target)
        assert_snapshot_metadata(metadata, target_game_date=target)
    except (ValueError, KeyError, TypeError) as exc:
        raise AdapterContractError(f"DOWNSTREAM_CONTRACT_REJECTED: {exc}") from exc
    metadata["adapter_contract"] = "canonical-player-game-box-to-d1-v1"
    metadata["adapter_field_map"] = dict(FIELD_MAP)
    metadata["research_status"] = "RESEARCH_ONLY"
    metadata["training_decision"] = "BLOCK_TRAINING"
    metadata["real_money_approval"] = "DENIED"
    return snapshot_rows, metadata
