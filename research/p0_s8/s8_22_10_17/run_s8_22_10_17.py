"""S8.22.10.17: offline, read-only player identity and injury provenance audit.

Candidate names and PDF excerpts are NOT authenticated player identities, statuses,
or historical-as-of publication timestamps. No automatic certifications.
"""
import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import unicodedata

DATE = '2023-11-15'
SOURCE_SHA = '70cc499b1c35cd65cde2ce0c8836e1db13e9194a43ac290450755f067ff3c3db'
TRIAGE_SHA = 'a39093fadb1f7ba1ff533bf968cfa2bd681ca1217c19c90e4e04863bf6e17817'
FIELDS = ['record_id','game_date_candidate','matchup_candidate','nba_game_id','team_candidate','raw_player_name','normalized_player_name','status_candidate','reason_candidate','source_page','source_y','source_pdf_context','game_id_evidence','name_collision','name_quality','source_excerpt_check','publication_time_evidence','player_id_evidence','player_identity_status','injury_status_evidence','historical_asof','disposition','reasons','training_eligible']

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def read_csv(path):
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames: raise ValueError(f'CSV missing header: {path}')
        return list(reader)

def normalize_name(value):
    value = unicodedata.normalize('NFKC', value or '')
    value = ' '.join(value.strip().split())
    return value.casefold()

def candidate_quality(value):
    if not value or not value.strip(): return 'EMPTY'
    if any(ch.isdigit() for ch in value): return 'DIGIT_IN_NAME'
    if not re.fullmatch(r"[\w\s.'’\-]+", value, flags=re.UNICODE): return 'UNUSUAL_CHARACTERS'
    if len(value.split()) < 2: return 'SINGLE_TOKEN_REVIEW'
    return 'PLAUSIBLE_FORMAT_ONLY'

def locate(root, milestone, filename, expected_sha):
    folder = root / f'research/p0_s8/{milestone}/results/{DATE}'
    matches = [p for p in folder.glob(f'*/{filename}') if digest(p) == expected_sha]
    if len(matches) != 1:
        raise ValueError(f'Expected exactly one SHA-verified {filename} under {folder}, found {len(matches)}; supply explicit path if necessary')
    return matches[0]

def analyze(ledger_rows, triage_rows):
    if len(ledger_rows) != 54 or len(triage_rows) != 54: raise ValueError('Expected exactly 54 source and triage rows')
    source = {r['record_id']: r for r in ledger_rows}
    triage = {r['record_id']: r for r in triage_rows}
    if len(source) != 54 or len(triage) != 54 or source.keys() != triage.keys(): raise ValueError('Duplicate/missing or mismatched record IDs')
    players = [r for r in ledger_rows if r.get('record_type') == 'PLAYER']
    if len(players) != 44: raise ValueError(f'Expected 44 PLAYER rows; found {len(players)}')
    counts = Counter((normalize_name(r.get('name_or_notice_candidate')), r.get('team_candidate','').strip().upper()) for r in players)
    output = []
    for r in players:
        t = triage[r['record_id']]
        if t.get('record_type') != 'PLAYER' or t.get('name_or_notice_candidate') != r.get('name_or_notice_candidate') or t.get('matchup_candidate') != r.get('matchup_candidate') or t.get('team_candidate') != r.get('team_candidate'):
            raise ValueError(f'Triage/source disagreement: {r["record_id"]}')
        name = r.get('name_or_notice_candidate','')
        norm = normalize_name(name)
        collision = counts[(norm, r.get('team_candidate','').strip().upper())] > 1
        excerpt = r.get('pdf_context_excerpt','')
        # A literal match to a locally extracted excerpt is NOT an independent PDF validation.
        excerpt_check = 'CANDIDATE_NAME_PRESENT' if norm and norm in normalize_name(excerpt) else 'CANDIDATE_NAME_NOT_FOUND'
        reasons = ['PLAYER_IDENTITY_NOT_CERTIFIED','INJURY_STATUS_NOT_CERTIFIED','HISTORICAL_ASOF_NOT_CERTIFIED']
        if collision: reasons.append('DUPLICATE_NAME_TEAM_CANDIDATE')
        quality = candidate_quality(name)
        if quality != 'PLAUSIBLE_FORMAT_ONLY': reasons.append('NAME_FORMAT_REVIEW')
        if excerpt_check != 'CANDIDATE_NAME_PRESENT': reasons.append('SOURCE_EXCERPT_NAME_MISMATCH')
        if t.get('game_id_evidence') != 'AUTOMATED_VERIFIED': reasons.append('GAME_MAPPING_UNVERIFIED')
        output.append({'record_id':r['record_id'],'game_date_candidate':r.get('game_date_candidate',''), 'matchup_candidate':r.get('matchup_candidate',''), 'nba_game_id':t.get('nba_game_id',''), 'team_candidate':r.get('team_candidate',''), 'raw_player_name':name,'normalized_player_name':norm,'status_candidate':r.get('status_candidate',''), 'reason_candidate':r.get('reason_candidate',''), 'source_page':r.get('page',''), 'source_y':r.get('y',''), 'source_pdf_context':excerpt,'game_id_evidence':t.get('game_id_evidence',''), 'name_collision':'YES' if collision else 'NO', 'name_quality':quality,'source_excerpt_check':excerpt_check,'publication_time_evidence':'NOT_PROVIDED_IN_TRUSTED_SOURCE', 'player_id_evidence':'NO_INDEPENDENT_ID_SOURCE', 'player_identity_status':'NOT_CERTIFIED','injury_status_evidence':'NOT_CERTIFIED','historical_asof':'NOT_CERTIFIED','disposition':'REVIEW_PRIORITY' if len(reasons)>3 else 'EVIDENCE_ACQUISITION_REQUIRED','reasons':'|'.join(reasons),'training_eligible':'NO'})
    return output

def write_csv(path, rows, fields):
    with path.open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=fields);w.writeheader();w.writerows(rows)

def run(root, ledger=None, triage=None):
    root = root.resolve()
    ledger = Path(ledger).resolve() if ledger else locate(root, 's8_22_10_7', 'player_and_team_manual_review.csv', SOURCE_SHA)
    triage = Path(triage).resolve() if triage else locate(root, 's8_22_10_14', 'injury_evidence_triage.csv', TRIAGE_SHA)
    for path in (ledger,triage):
        if not path.is_file() or not path.is_relative_to(root): raise ValueError(f'Input missing or outside project: {path}')
    if digest(ledger)!=SOURCE_SHA or digest(triage)!=TRIAGE_SHA: raise ValueError('Source evidence SHA-256 mismatch; stop')
    rows=analyze(read_csv(ledger),read_csv(triage))
    token=hashlib.sha256((digest(ledger)+digest(triage)+'S8.22.10.17-v1').encode()).hexdigest()[:16]
    output=root/f'research/p0_s8/s8_22_10_17/results/{DATE}/{token}'
    output.mkdir(parents=True,exist_ok=True)
    write_csv(output/'player_identity_evidence_audit.csv',rows,FIELDS)
    write_csv(output/'review_priority_queue.csv',[r for r in rows if r['disposition']=='REVIEW_PRIORITY'],FIELDS)
    report={'milestone':'S8.22.10.17','game_date':DATE,'source_ledger':str(ledger),'source_ledger_sha256':digest(ledger),'source_triage':str(triage),'source_triage_sha256':digest(triage),'player_candidates':len(rows),'team_notices_excluded':10,'disposition_counts':dict(Counter(r['disposition'] for r in rows)),'reason_counts':dict(Counter(reason for r in rows for reason in r['reasons'].split('|'))),'independent_player_ids_verified':0,'injury_statuses_certified':0,'historical_asof_certified':0,'research_status':'RESEARCH_ONLY','training_decision':'BLOCK_TRAINING','next_action':'Acquire authoritative dated player identity and injury-report source records; validate against original PDF and publication-time evidence before certification.','note':'Name normalization and local excerpt matching are candidate diagnostics only. No live NBA API, no remote authentication, no inferred publication timestamps, and no source ledger edits.'}
    (output/'review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',output/'review.json');print(json.dumps(report,indent=2));return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project-root',default='.');p.add_argument('--ledger');p.add_argument('--triage');a=p.parse_args()
    try: run(Path(a.project_root),a.ledger,a.triage)
    except (ValueError,FileNotFoundError,KeyError) as e: p.exit(2,'FAIL CLOSED: '+str(e)+'\n')
if __name__=='__main__': main()
