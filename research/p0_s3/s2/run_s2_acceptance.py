from pathlib import Path
import shutil, sys, tempfile
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"src"))
from nba_mike.storage import StorageManager

def main():
    t=Path(tempfile.mkdtemp(prefix="nba_mike_s2_"))
    try:
        s=StorageManager(t); s.ensure_tree()
        m=s.register_bytes(content=b"player_id,minutes\n1,32\n",source_name="NBA",dataset_name="acceptance",extension="csv",request_parameters={"DateTo":"2026-01-01"},requested_scope={"rule":"D-1"},media_type="text/csv",code_git_commit="TEST")
        checks={"tree":all((t/"data"/x).exists() for x in ("raw","validated","canonical","snapshots","features","targets","quarantine","manifests","cache")),"hash_verify":s.verify(m),"roundtrip":s.read_manifest(m.artifact_id).request_parameters.get("DateTo")=="2026-01-01"}
        (t/m.relative_path).write_bytes(b"tampered")
        checks["tamper_detected"]=not s.verify(m)
        q=s.register_bytes(content=b"bad",source_name="NBA",dataset_name="bad",extension="txt")
        checks["quarantine"] = s.set_validation(q.artifact_id,"QUARANTINED","acceptance-test").validation_status=="QUARANTINED"
        print("P0-S3 S2 — Storage & Manifest Acceptance")
        for k,v in checks.items(): print(f"  {k}: {'PASS' if v else 'FAIL'}")
        ok=all(checks.values()); print(f"OVERALL: {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1
    finally: shutil.rmtree(t,ignore_errors=True)
if __name__=='__main__': raise SystemExit(main())
