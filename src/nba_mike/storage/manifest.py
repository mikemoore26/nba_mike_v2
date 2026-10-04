from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any
import uuid

LAYERS = ("raw", "validated", "canonical", "snapshots", "features", "targets", "quarantine", "manifests", "cache")
VALIDATION_STATES = {"UNVALIDATED", "PASS", "QUARANTINED", "FAILED"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_sha256(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

@dataclass
class ArtifactManifest:
    artifact_id: str
    layer: str
    source_name: str
    dataset_name: str
    endpoint: str | None
    request_parameters: dict[str, Any]
    requested_scope: dict[str, Any]
    retrieved_at_utc: str
    relative_path: str
    media_type: str
    byte_size: int
    sha256: str
    request_status: str = "SUCCESS"
    validation_status: str = "UNVALIDATED"
    quarantine_reason: str | None = None
    row_count: int | None = None
    schema_fingerprint: str | None = None
    event_time: str | None = None
    published_time: str | None = None
    ingested_time: str | None = None
    as_of_time: str | None = None
    parent_artifact_ids: list[str] = field(default_factory=list)
    code_git_commit: str | None = None
    notes: str | None = None
    manifest_version: str = "1.0"

    def validate(self) -> None:
        if self.layer not in LAYERS: raise ValueError(f"invalid layer: {self.layer}")
        if self.validation_status not in VALIDATION_STATES: raise ValueError("invalid validation_status")
        if self.validation_status == "QUARANTINED" and not self.quarantine_reason:
            raise ValueError("quarantine_reason required")
        if len(self.sha256) != 64: raise ValueError("invalid sha256")

class StorageManager:
    def __init__(self, project_root: str | Path):
        self.root = Path(project_root).resolve()
        self.data = self.root / "data"

    def ensure_tree(self) -> None:
        for layer in LAYERS:
            (self.data / layer).mkdir(parents=True, exist_ok=True)

    def _manifest_path(self, artifact_id: str) -> Path:
        return self.data / "manifests" / f"{artifact_id}.json"

    def register_bytes(self, *, content: bytes, source_name: str, dataset_name: str,
                       extension: str, endpoint: str | None = None,
                       request_parameters: dict[str, Any] | None = None,
                       requested_scope: dict[str, Any] | None = None,
                       media_type: str = "application/octet-stream",
                       code_git_commit: str | None = None) -> ArtifactManifest:
        self.ensure_tree()
        artifact_id = uuid.uuid4().hex
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        safe_source = source_name.lower().replace(" ", "-")
        safe_dataset = dataset_name.lower().replace(" ", "-")
        ext = extension.lstrip(".")
        filename = f"{safe_source}__{safe_dataset}__retrieved-{stamp}__{artifact_id}.{ext}"
        path = self.data / "raw" / filename
        if path.exists(): raise FileExistsError(path)
        path.write_bytes(content)
        manifest = ArtifactManifest(
            artifact_id=artifact_id, layer="raw", source_name=source_name,
            dataset_name=dataset_name, endpoint=endpoint,
            request_parameters=request_parameters or {}, requested_scope=requested_scope or {},
            retrieved_at_utc=utc_now(), relative_path=path.relative_to(self.root).as_posix(),
            media_type=media_type, byte_size=path.stat().st_size, sha256=file_sha256(path),
            ingested_time=utc_now(), code_git_commit=code_git_commit,
        )
        self.write_manifest(manifest)
        return manifest

    def write_manifest(self, manifest: ArtifactManifest) -> Path:
        self.ensure_tree(); manifest.validate()
        p = self._manifest_path(manifest.artifact_id)
        p.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True), encoding="utf-8")
        return p

    def read_manifest(self, artifact_id: str) -> ArtifactManifest:
        obj = json.loads(self._manifest_path(artifact_id).read_text(encoding="utf-8"))
        m = ArtifactManifest(**obj); m.validate(); return m

    def verify(self, manifest: ArtifactManifest) -> bool:
        p = self.root / manifest.relative_path
        return p.exists() and p.stat().st_size == manifest.byte_size and file_sha256(p) == manifest.sha256

    def set_validation(self, artifact_id: str, status: str, reason: str | None = None) -> ArtifactManifest:
        m = self.read_manifest(artifact_id)
        if status not in VALIDATION_STATES: raise ValueError("invalid validation status")
        if status == "QUARANTINED" and not reason: raise ValueError("quarantine reason required")
        if m.validation_status != "UNVALIDATED": raise ValueError("validation state is already terminal")
        m.validation_status = status; m.quarantine_reason = reason
        self.write_manifest(m); return m
