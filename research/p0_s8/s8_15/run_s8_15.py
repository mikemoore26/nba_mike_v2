"""S8.15 offline official injury report evidence pilot. No training or source certification."""
import argparse,csv,hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path

GAME='0022300061'
URL='https://ak-static.cms.nba.com/referee/injury/Injury-Report_2023-10-24_05PM.pdf'
CUTOFF='2023-10-24T19:30:00-04:00'

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def iso(s):
    try:
        dt=datetime.fromisoformat(s.replace('Z','+00:00'))
        return dt if dt.tzinfo is not None else None
    except (ValueError,TypeError,AttributeError):return None

def inspect(root):
    base=root/'research/p0_s8/s8_15'
    intake=base/'evidence_intake.csv'
    artifacts=base/'artifacts'
    out=base/'results';out.mkdir(parents=True,exist_ok=True)
    rows=list(csv.DictReader(intake.open(newline='',encoding='utf-8-sig'))) if intake.exists() else []
    findings=[]
    for i,row in enumerate(rows,1):
        path_str=row.get('artifact_relative_path','').strip()
        path=(artifacts/path_str).resolve() if path_str else None
        safe=bool(path and path.is_relative_to(artifacts.resolve()) and path.is_file())
        sha=digest(path) if safe else ''
        expected=row.get('sha256','').strip().lower()
        checksum_ok=bool(sha and re.fullmatch('[0-9a-f]{64}',expected) and sha==expected)
        doc_time=iso(row.get('document_claimed_timestamp',''))
        archive_time=iso(row.get('independent_capture_timestamp',''))
        before=bool(archive_time and archive_time.astimezone(timezone.utc)<iso(CUTOFF).astimezone(timezone.utc))
        independent=row.get('independent_capture_url','').strip()
        # An operator's CSV cannot independently establish a historical capture timestamp.
        status='CANDIDATE_REVIEW_ONLY' if safe and checksum_ok and doc_time and independent and archive_time and before else 'INSUFFICIENT_EVIDENCE'
        reasons=[]
        if not safe:reasons.append('MISSING_OR_UNSAFE_ARTIFACT_PATH')
        if not checksum_ok:reasons.append('SHA256_MISSING_OR_MISMATCH')
        if not doc_time:reasons.append('INVALID_DOCUMENT_CLAIMED_TIMESTAMP')
        if not independent or not archive_time:reasons.append('NO_INDEPENDENT_CAPTURE_REFERENCE_AND_TIMESTAMP')
        elif not before:reasons.append('CAPTURE_NOT_BEFORE_TIPOFF')
        reasons.append('INDEPENDENT_ARCHIVE_CONTENT_AND_TIME_NOT_EXTERNALLY_VERIFIED')
        findings.append(dict(row=i,source_url=row.get('source_url',''),artifact_relative_path=path_str,sha256_computed=sha,status=status,reasons=';'.join(reasons)))
    report=dict(milestone='S8.15',mode='OFFLINE_OFFICIAL_INJURY_EVIDENCE_PILOT',game_id=GAME,matchup='LAL@DEN',scheduled_tipoff_et=CUTOFF,official_pdf_url=URL,document_label='10/24/23 05:30 PM ET',source_discovery='OFFICIAL_NBA_PDF_IDENTIFIED_PUBLIC_WEB_SEARCH',official_pdf_downloaded_by_runner=False,submitted_artifacts=len(rows),candidate_manual_review=sum(x['status']=='CANDIDATE_REVIEW_ONLY' for x in findings),independently_verified_artifacts=0,independently_verified_games=0,full_pregame_population_verified=False,publication_time_independently_verified=False,decision='BLOCK_TRAINING',status='RESEARCH_ONLY',outcome='OFFICIAL_ARTIFACT_DISCOVERED_NOT_ASOF_CERTIFIED',limitations=['Printed PDF time is not independent proof of public availability','CSV capture metadata is a claim requiring independent archival verification','Injury report is not a complete eligible-player roster','No historical data sources or games are approved for training','Restart 88 games remain separately blocked'])
    (out/'s8_15_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    with (out/'s8_15_evidence_review.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['row','source_url','artifact_relative_path','sha256_computed','status','reasons']);w.writeheader();w.writerows(findings)
    with (out/'s8_15_source_candidates.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['source','url','scope','independent_pregame_capture','decision']);w.writeheader();w.writerows([
            dict(source='NBA official 5PM injury PDF',url=URL,scope='LAL@DEN 2023-10-24; 05:30 PM document label',independent_pregame_capture='NOT_VERIFIED',decision='CANDIDATE_ONLY'),
            dict(source='NBA official 7PM injury PDF',url='https://ak-static.cms.nba.com/referee/injury/Injury-Report_2023-10-24_07PM.pdf',scope='LAL@DEN 2023-10-24; 07:30 PM document label at scheduled tipoff',independent_pregame_capture='NOT_VERIFIED',decision='DO_NOT_USE_AS_PREGAME_PROOF'),
            dict(source='NBA 2023-24 schedule',url='https://www.nba.com/news/2023-24-nba-regular-season-schedule',scope='Scheduled tipoff 7:30 PM ET',independent_pregame_capture='SCHEDULE_PUBLISHED_BEFORE_GAME',decision='SCHEDULE_CONTEXT_ONLY'),
            dict(source='NBA opening-night roster announcement',url='https://www.nba.com/news/nba-rosters-regular-season-2023-24',scope='Opening-night rosters, publication shown 5:03 PM ET',independent_pregame_capture='HISTORICAL_PUBLICATION_NOT_INDEPENDENTLY_ARCHIVED',decision='ROSTER_CANDIDATE_ONLY')])
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',default='.');args=p.parse_args()
    print(json.dumps(inspect(Path(args.project_root).resolve()),indent=2))
if __name__=='__main__':main()
