from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping
import hashlib


class ProvenanceError(RuntimeError):
    """Raised when an artifact cannot safely participate in a provenance chain."""


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_parent_manifests_usable(parent_manifests: Iterable[Mapping[str, Any]]) -> None:
    parents = list(parent_manifests)
    if not parents:
        raise ProvenanceError("A derived artifact requires at least one parent artifact")

    for parent in parents:
        artifact_id = parent.get("artifact_id")
        if not artifact_id:
            raise ProvenanceError("Parent manifest is missing artifact_id")

        status = parent.get("validation_status")
        if status != "PASS":
            raise ProvenanceError(
                f"Parent artifact {artifact_id!r} is not usable: validation_status={status!r}"
            )

        if not parent.get("sha256"):
            raise ProvenanceError(f"Parent artifact {artifact_id!r} is missing sha256")


def validate_parent_chain(
    parent_manifests: Iterable[Mapping[str, Any]],
    artifact_paths: Mapping[str, str | Path],
) -> dict[str, str]:
    parents = list(parent_manifests)
    assert_parent_manifests_usable(parents)

    verified: dict[str, str] = {}
    for parent in parents:
        artifact_id = str(parent["artifact_id"])
        if artifact_id not in artifact_paths:
            raise ProvenanceError(f"No artifact path supplied for parent {artifact_id!r}")

        path = Path(artifact_paths[artifact_id])
        if not path.exists():
            raise ProvenanceError(f"Parent artifact file does not exist: {path}")

        actual = sha256_file(path)
        expected = str(parent["sha256"])
        if actual.lower() != expected.lower():
            raise ProvenanceError(
                f"SHA-256 mismatch for parent {artifact_id!r}: expected {expected}, got {actual}"
            )
        verified[artifact_id] = actual

    return verified
