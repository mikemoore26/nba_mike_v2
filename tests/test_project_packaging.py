from __future__ import annotations

import importlib
import importlib.metadata
from pathlib import Path


def test_distribution_is_installed() -> None:
    assert importlib.metadata.version("nba-mike-v2") == "0.0.0"


def test_nba_mike_imports_from_src_tree() -> None:
    module = importlib.import_module("nba_mike")
    module_path = Path(module.__file__).resolve()
    assert module_path.name == "__init__.py"
    assert module_path.parent.name == "nba_mike"
    assert module_path.parent.parent.name == "src"


def test_completed_foundation_modules_import() -> None:
    for name in (
        "nba_mike.storage",
        "nba_mike.identity",
        "nba_mike.validation",
        "nba_mike.canonical",
        "nba_mike.snapshots",
    ):
        assert importlib.import_module(name) is not None
