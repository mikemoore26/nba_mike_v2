from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
import csv
import json
import subprocess


class BuildError(RuntimeError):
    """Raised when a canonical build cannot be proven safe."""


@dataclass(frozen=True)
class CanonicalBuildResult:
    output_path: Path
    manifest_path: Path
    row_count: int
    sha256: str
    parent_artifact_id: str


REQUIRED_OUTPUT = (
    "game_id", "game_date", "player_id", "team_id", "opponent_team_id",
    "minutes", "points", "rebounds", "assists", "three_pointers_made",
)
NUMERIC = ("minutes", "points", "rebounds", "assists", "three_pointers_made")


def _hash(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _schema_fingerprint(fieldnames: Iterable[str]) -> str:
    payload = "\n".join(fieldnames).encode("utf-8")
    return sha256(payload).hexdigest()


def _git_commit(project_root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=project_root, text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise BuildError(f"PARENT_MANIFEST_INVALID: {exc}") from exc
    for key in ("artifact_id", "sha256", "validation_status"):
        if key not in data:
            raise BuildError(f"PARENT_MANIFEST_MISSING_FIELD: {key}")
    return data


def _resolve(resolver: Any, entity_type: str, source_name: str, source_id: str) -> str:
    if callable(resolver):
        value = resolver(entity_type, source_name, source_id)
    elif isinstance(resolver, Mapping):
        value = resolver.get((entity_type, source_name, str(source_id)))
    elif hasattr(resolver, "resolve"):
        value = resolver.resolve(entity_type=entity_type, source_name=source_name, source_id=str(source_id))
    else:
        raise BuildError("IDENTITY_RESOLVER_UNSUPPORTED")
    if value is None:
        raise BuildError(f"IDENTITY_UNRESOLVED: {entity_type}:{source_name}:{source_id}")
    if isinstance(value, (list, tuple, set)):
        if len(value) != 1:
            raise BuildError(f"IDENTITY_AMBIGUOUS: {entity_type}:{source_name}:{source_id}")
        value = next(iter(value))
    if isinstance(value, Mapping):
        value = value.get("canonical_id") or value.get("id")
    if not value:
        raise BuildError(f"IDENTITY_UNRESOLVED: {entity_type}:{source_name}:{source_id}")
    return str(value)


def build_player_game_box(
    *, project_root: str | Path, raw_path: str | Path, parent_manifest_path: str | Path,
    output_path: str | Path, output_manifest_path: str | Path, source_name: str,
    column_map: Mapping[str, str], identity_resolver: Any,
) -> CanonicalBuildResult:
    project_root, raw_path = Path(project_root), Path(raw_path)
    parent_manifest_path, output_path = Path(parent_manifest_path), Path(output_path)
    output_manifest_path = Path(output_manifest_path)
    if not raw_path.is_file():
        raise BuildError("RAW_PARENT_MISSING")
    parent = _load_manifest(parent_manifest_path)
    if str(parent["validation_status"]).upper() != "PASS":
        raise BuildError(f"PARENT_NOT_PASS: {parent['validation_status']}")
    actual_parent_hash = _hash(raw_path)
    if actual_parent_hash.lower() != str(parent["sha256"]).lower():
        raise BuildError("PARENT_HASH_MISMATCH")

    missing_map = [c for c in REQUIRED_OUTPUT if c not in column_map]
    if missing_map:
        raise BuildError(f"COLUMN_MAP_INCOMPLETE: {missing_map}")

    with raw_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise BuildError("SOURCE_SCHEMA_EMPTY")
        required_source = [column_map[c] for c in REQUIRED_OUTPUT]
        missing_source = [c for c in required_source if c not in reader.fieldnames]
        if missing_source:
            raise BuildError(f"SOURCE_SCHEMA_MISSING: {missing_source}")
        rows = list(reader)

    canonical: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for i, row in enumerate(rows, start=2):
        def src(name: str) -> str:
            value = row.get(column_map[name])
            if value is None or str(value).strip() == "":
                raise BuildError(f"NULL_REQUIRED_VALUE: row={i} field={name}")
            return str(value).strip()
        game_id = src("game_id")
        player_id = _resolve(identity_resolver, "player", source_name, src("player_id"))
        team_id = _resolve(identity_resolver, "team", source_name, src("team_id"))
        opp_id = _resolve(identity_resolver, "team", source_name, src("opponent_team_id"))
        out: dict[str, Any] = {
            "game_id": game_id, "game_date": src("game_date"), "player_id": player_id,
            "team_id": team_id, "opponent_team_id": opp_id,
        }
        for name in NUMERIC:
            try:
                val = float(src(name))
            except ValueError as exc:
                raise BuildError(f"INVALID_NUMERIC_VALUE: row={i} field={name}") from exc
            if val < 0:
                raise BuildError(f"IMPOSSIBLE_NEGATIVE_VALUE: row={i} field={name}")
            out[name] = val
        if out["minutes"] > 60:
            raise BuildError(f"IMPOSSIBLE_MINUTES: row={i}")
        key = (game_id, player_id)
        if key in seen:
            raise BuildError(f"DUPLICATE_CANONICAL_KEY: {key}")
        seen.add(key)
        canonical.append(out)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temp = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        with temp.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(REQUIRED_OUTPUT))
            writer.writeheader(); writer.writerows(canonical)
        temp.replace(output_path)
        out_hash = _hash(output_path)
        manifest = {
            "manifest_version": 1,
            "artifact_id": f"canonical-player-game-box-{out_hash[:16]}",
            "layer": "canonical", "dataset_name": "player_game_box",
            "source_name": source_name, "relative_path": str(output_path.relative_to(project_root)).replace("\\", "/") if output_path.is_relative_to(project_root) else str(output_path),
            "row_count": len(canonical), "sha256": out_hash,
            "schema_fingerprint": _schema_fingerprint(REQUIRED_OUTPUT),
            "validation_status": "PASS",
            "parent_artifact_ids": [str(parent["artifact_id"])],
            "parent_sha256": [actual_parent_hash], "code_git_commit": _git_commit(project_root),
            "notes": "P0-S3 S5 governed canonical build; historical outcome data, not a pregame feature snapshot.",
        }
        output_manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    except Exception:
        temp.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        output_manifest_path.unlink(missing_ok=True)
        raise
    return CanonicalBuildResult(output_path, output_manifest_path, len(canonical), out_hash, str(parent["artifact_id"]))
