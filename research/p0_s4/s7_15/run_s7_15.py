"""Download official injury PDFs from an explicit, editable manifest, then run S7.14."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'src'))
from nba_mike.data.injury_acquire import acquire
from nba_mike.data.injury_multi_report import audit_directory

p=argparse.ArgumentParser()
p.add_argument('--manifest',type=Path,default=ROOT/'research/p0_s4/s7_15/source_urls.json')
p.add_argument('--pdf-dir',type=Path,default=ROOT/'research/p0_s4/s7_14/input_pdfs')
p.add_argument('--results-dir',type=Path,default=ROOT/'research/p0_s4/s7_15/results')
p.add_argument('--audit-dir',type=Path,default=ROOT/'research/p0_s4/s7_14/results')
p.add_argument('--timeout',type=int,default=20)
p.add_argument('--skip-audit',action='store_true')
a=p.parse_args()
manifest=json.loads(a.manifest.read_text(encoding='utf-8'))
if not isinstance(manifest,dict) or not isinstance(manifest.get('urls'),list) or any(not isinstance(x,str) for x in manifest['urls']):
    p.error('Manifest must be an object containing a list of URL strings under "urls"')
acquisition=acquire(manifest['urls'],a.pdf_dir,a.results_dir,timeout=a.timeout)
print(json.dumps({k:v for k,v in acquisition.items() if k!='entries'},indent=2))
for entry in acquisition['entries']:
    print(entry['status'],entry['requested_url'],entry.get('error',''))
if not a.skip_audit:
    print(json.dumps(audit_directory(a.pdf_dir,a.audit_dir,min_distinct=3),indent=2))
