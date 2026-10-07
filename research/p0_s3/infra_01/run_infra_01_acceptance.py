from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESULTS = Path(__file__).resolve().parent / "results"


def check(name: str, condition: bool, detail: str = "") -> dict[str, object]:
    return {"check": name, "status": "PASS" if condition else "FAIL", "detail": detail}


def main() -> int:
    results: list[dict[str, object]] = []
    results.append(check("pyproject_exists", (ROOT / "pyproject.toml").is_file()))
    results.append(check("manual_pythonpath_absent", "PYTHONPATH" not in os.environ, os.environ.get("PYTHONPATH", "")))

    try:
        version = importlib.metadata.version("nba-mike-v2")
        results.append(check("distribution_installed", version == "0.0.0", version))
    except importlib.metadata.PackageNotFoundError:
        results.append(check("distribution_installed", False, "nba-mike-v2 not installed"))

    try:
        package = importlib.import_module("nba_mike")
        package_path = Path(package.__file__).resolve()
        expected = (ROOT / "src" / "nba_mike" / "__init__.py").resolve()
        results.append(check("standalone_import", package_path == expected, str(package_path)))
    except Exception as exc:
        results.append(check("standalone_import", False, repr(exc)))

    modules = ["storage", "identity", "validation", "canonical", "snapshots"]
    failures: list[str] = []
    for module in modules:
        try:
            importlib.import_module(f"nba_mike.{module}")
        except Exception as exc:
            failures.append(f"{module}: {exc!r}")
    results.append(check("foundation_module_imports", not failures, "; ".join(failures)))

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    tail = "\n".join((proc.stdout + "\n" + proc.stderr).strip().splitlines()[-8:])
    results.append(check("full_regression_suite", proc.returncode == 0, tail))

    overall = all(item["status"] == "PASS" for item in results)
    RESULTS.mkdir(parents=True, exist_ok=True)
    report = {"milestone": "P0-S3 INFRA-01", "overall": "PASS" if overall else "FAIL", "checks": results}
    (RESULTS / "infra_01_acceptance_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary_lines = ["P0-S3 INFRA-01 — Project Packaging & Execution Acceptance"]
    for item in results:
        summary_lines.append(f"  {item['check']}: {item['status']}")
    summary_lines.append(f"OVERALL: {'PASS' if overall else 'FAIL'}")
    (RESULTS / "infra_01_acceptance_summary.txt").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print("\n".join(summary_lines))
    if not overall:
        print("\nFailure details:")
        for item in results:
            if item["status"] == "FAIL":
                print(f"- {item['check']}: {item['detail']}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
