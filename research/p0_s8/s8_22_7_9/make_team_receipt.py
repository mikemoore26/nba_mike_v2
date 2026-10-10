"""Make a local receipt for manually saved, authorized BALLDONTLIE team JSON."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

URL='https://api.balldontlie.io/v1/teams'
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--project-root',required=True)
    p.add_argument('--source',required=True)
    p.add_argument('--retrieved-utc',required=True,help='Actual capture UTC time, ISO-8601 with timezone')
    a=p.parse_args()
    root=Path(a.project_root).resolve()
    source=Path(a.source)
    source=(source if source.is_absolute() else root/source).resolve()
    if not source.is_relative_to(root): p.error('Source must be inside project')
    dt=datetime.fromisoformat(a.retrieved_utc.replace('Z','+00:00'))
    if dt.tzinfo is None: p.error('UTC timestamp must include timezone')
    if not source.is_file(): p.error('Source file missing')
    raw=source.read_bytes()
    parsed=json.loads(raw)
    if not isinstance(parsed,dict) or not isinstance(parsed.get('data'),list): p.error('Expected JSON object with data array')
    receipt={'source_url':URL,'retrieved_utc':dt.astimezone(timezone.utc).isoformat(),
      'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),
      'evidence_path':source.relative_to(root).as_posix(),
      'source_kind':'USER_MANAGED_MANUAL_TEAM_DIRECTORY_SNAPSHOT',
      'historical_asof_verified':False,'training_eligible':False}
    path=source.parent/'receipt.json'
    if path.exists(): p.error('Receipt already exists: do not overwrite evidence')
    path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print('Receipt:',path)
    print('SHA256:',receipt['sha256'])
if __name__=='__main__':main()
