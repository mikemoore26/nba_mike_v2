"""Prospective capture CLI; no backfilled availability claims."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from nba_mike.data.injury_capture import fetch_and_capture


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="Exact official injury PDF URL to retrieve now")
    parser.add_argument("--capture-dir", type=Path, default=ROOT / "research/p0_s4/s7_20/captures")
    args = parser.parse_args()
    if not args.url:
        print(json.dumps({"status": "READY_FOR_PROSPECTIVE_CAPTURE", "decision": "BLOCK_TRAINING", "capture_dir": str(args.capture_dir), "historical_publication_verified": False}, indent=2))
        return
    print(json.dumps(fetch_and_capture(args.url, args.capture_dir), indent=2))


if __name__ == "__main__":
    main()
