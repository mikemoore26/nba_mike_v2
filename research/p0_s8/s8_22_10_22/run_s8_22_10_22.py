"""S8.22.10.22: third-party nba_api registry capture and identity candidate bridge.

Never certify historical teams, injuries, publication time, or training eligibility.
"""
import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SOURCE = 'https://raw.githubusercontent.com/swar/nba_api/master/src/nba_api/stats/static/data/players.json'
MAX_BYTES = 8_000_000

def sha256(blob):
    return hashlib.sha256(blob).hexdigest()

def validate(blob):
    data = json.loads(blob.decode('utf-8-sig'))
    if not isinstance(data, list) or not data:
        raise ValueError('Expected nonempty nba_api players list')
    ids = set()
    out = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f'Row {i}: not an object')
        pid, name = item.get('id'), item.get('full_name')
        if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
            raise ValueError(f'Row {i}: invalid integer id')
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f'Row {i}: invalid full_name')
        if pid in ids:
            raise ValueError(f'Duplicate player id {pid}')
        ids.add(pid)
        out.append((pid, name.strip()))
    return out

def fetch(timeout):
    req = urllib.request.Request(SOURCE, headers={'User-Agent':'NBA-MIKE-v2-research/1.0','Accept':'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        final = urllib.parse.urlsplit(resp.geturl())
        if final.scheme != 'https' or final.hostname != 'raw.githubusercontent.com':
            raise ValueError('Unexpected redirect target')
        if resp.status != 200:
            raise ValueError(f'Unexpected HTTP status {resp.status}')
        blob = resp.read(MAX_BYTES + 1)
        if len(blob) > MAX_BYTES:
            raise ValueError('Source exceeds size limit')
        return blob, {'status':resp.status,'final_url':resp.geturl(),'content_type':resp.headers.get('Content-Type')}

def write_immutable(path, data):
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f'Immutable capture conflict: {path}')
    else:
        path.write_bytes(data)

def run(root, offline=None, timeout=15, reconcile=False):
    root = Path(root).resolve()
    if offline:
        blob = Path(offline).resolve().read_bytes()
        transport = {'status':None,'final_url':None,'content_type':None}
        mode = 'USER_SUPPLIED_UNVERIFIED_SOURCE'
    else:
        blob, transport = fetch(timeout)
        mode = 'LIVE_THIRD_PARTY_GITHUB_RAW'
    if len(blob) > MAX_BYTES:
        raise ValueError('Source exceeds size limit')
    players = validate(blob)
    digest = sha256(blob)
    dest = root/'research/p0_s8/s8_22_10_22/results/2023-11-15'/digest[:16]
    dest.mkdir(parents=True,exist_ok=True)
    raw = dest/'nba_api_players_raw.json'
    write_immutable(raw, blob)
    # Adapter is intentionally NOT official NBA Stats data. No historical team assigned.
    adapter = {'resultSets':[{'name':'CommonAllPlayers','headers':['PERSON_ID','DISPLAY_FIRST_LAST','TEAM_ABBREVIATION'],
                               'rowSet':[[pid,name,''] for pid,name in players]}]}
    bridge = dest/'third_party_name_only_registry_adapter.json'
    write_immutable(bridge,(json.dumps(adapter,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
    manifest = {
        'milestone':'S8.22.10.22','target_game_date':'2023-11-15','registry_source':'nba_api GitHub static players.json',
        'source_class':'THIRD_PARTY_NOT_OFFICIAL_NBA_REGISTRY','source_url':SOURCE,
        'retrieved_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'capture_mode':mode,'transport':transport,'raw_sha256':digest,'raw_bytes':len(blob),
        'players_count':len(players),'unique_ids':len(players),
        'adapter_sha256':sha256(bridge.read_bytes()),
        'source_snapshot_is_historical_2023_11_15':False,
        'historical_team_membership_certified':False,'player_ids_certified':0,
        'injury_statuses_certified':0,'historical_asof_certified':0,
        'research_status':'RESEARCH_ONLY','training_decision':'BLOCK_TRAINING',
        'note':'Name/ID candidates only. Mutable GitHub master and current static player directory cannot prove historical date or team. Offline files are not authenticated by this workflow.'
    }
    manifest_file = dest/'capture_manifest.json'
    # Manifest contains time-dependent metadata; do not overwrite earlier capture.
    if not manifest_file.exists():
        manifest_file.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    else:
        prior=json.loads(manifest_file.read_text(encoding='utf-8'))
        if prior.get('raw_sha256')!=digest or prior.get('adapter_sha256')!=manifest['adapter_sha256']:
            raise ValueError('Existing manifest mismatch')
    print('RAW:',raw)
    print('ADAPTER:',bridge)
    print('MANIFEST:',manifest_file)
    print('PLAYERS:',len(players))
    print('MODE:',mode)
    print('GOVERNANCE: RESEARCH_ONLY / BLOCK_TRAINING')
    if reconcile:
        script=root/'research/p0_s8/s8_22_10_20/run_s8_22_10_20.py'
        if not script.is_file():
            raise ValueError('S8.22.10.20 reconciliation script missing')
        cmd=[sys.executable,str(script),'--project-root',str(root),'--registry-json',str(bridge)]
        print('RUNNING NAME-ONLY CANDIDATE RECONCILIATION',flush=True)
        result=subprocess.run(cmd,check=False)
        if result.returncode:
            raise ValueError(f'Existing reconciliation returned {result.returncode}')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--project-root',type=Path,default=Path('.'))
    p.add_argument('--offline-json',type=Path)
    p.add_argument('--timeout',type=int,default=15)
    p.add_argument('--reconcile',action='store_true')
    a=p.parse_args()
    try:
        if not 1<=a.timeout<=60:
            raise ValueError('Timeout must be 1-60 seconds')
        run(a.project_root,a.offline_json,a.timeout,a.reconcile)
    except (ValueError,OSError,UnicodeError,urllib.error.URLError,TimeoutError,json.JSONDecodeError) as e:
        p.exit(2,'FAIL CLOSED: '+str(e)+'\n')
