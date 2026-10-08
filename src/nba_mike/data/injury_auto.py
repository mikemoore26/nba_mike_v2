"""S7.4 exploratory NBA injury report row parsing; never training eligible.

This parser intentionally abstains when layout is ambiguous. The parsed records
are NOT ground truth and historical publication remains unverified.
"""
from __future__ import annotations
import csv, hashlib, json, re
from pathlib import Path

TEAMS = ('Atlanta Hawks','Boston Celtics','Brooklyn Nets','Charlotte Hornets','Chicago Bulls',
'Cleveland Cavaliers','Dallas Mavericks','Denver Nuggets','Detroit Pistons','Golden State Warriors',
'Houston Rockets','Indiana Pacers','LA Clippers','Los Angeles Lakers','Memphis Grizzlies',
'Miami Heat','Milwaukee Bucks','Minnesota Timberwolves','New Orleans Pelicans','New York Knicks',
'Oklahoma City Thunder','Orlando Magic','Philadelphia 76ers','Phoenix Suns','Portland Trail Blazers',
'Sacramento Kings','San Antonio Spurs','Toronto Raptors','Utah Jazz','Washington Wizards')
STATUS = re.compile(r'\b(Out|Doubtful|Questionable|Probable|Available)\b',re.I)
DATE = re.compile(r'\b(\d{2}/\d{2}/\d{4})\b')
MATCHUP = re.compile(r'\b([A-Z]{2,3})@([A-Z]{2,3})\b')
PLAYER = re.compile(r"(?<!\w)([A-Za-z][A-Za-z'’.-]+(?:\s+[A-Za-z][A-Za-z'’.-]+)*),\s*([A-Za-z][A-Za-z'’.-]+(?:\s+[A-Za-z][A-Za-z'’.-]+)*)")
FIELDS = ('record_id','source_sha256','source_page','source_line','raw_text','game_date','matchup',
          'team','player','status','reason','parse_status','flags','eligible_for_asof_training')

def parse_lines(pages, sha):
    records=[]; abstentions=[]
    for page in pages:
        # Reset context at each page: never infer a team across page breaks.
        ctx={'game_date':'','matchup':'','team':''}
        for number, raw in enumerate(page['text'].splitlines(),1):
            line=raw.strip()
            if not line:continue
            dm=DATE.search(line)
            if dm:
                mm,dd,yyyy=dm.group(1).split('/')
                ctx['game_date']=f'{yyyy}-{mm}-{dd}'
            match=MATCHUP.search(line)
            if match:ctx['matchup']=match.group(0)
            teams=[t for t in TEAMS if re.search(r'(?<!\w)'+re.escape(t)+r'(?!\w)',line)]
            if len(teams)==1:ctx['team']=teams[0]
            sm=STATUS.search(line)
            if not sm:continue
            before=line[:sm.start()].strip(); after=line[sm.end():].strip(' -')
            # Player must appear immediately before the status (no intervening prose).
            name_area=before
            if teams and len(teams)==1:
                # Exclude team and matchup tokens before looking for the player.
                marker=before.rfind(teams[0])
                if marker>=0:name_area=before[marker+len(teams[0]):].strip()
            names=list(PLAYER.finditer(name_area))
            name=names[-1] if names else None
            if name and name_area[name.end():].strip():name=None
            player=(name.group(2)+' '+name.group(1)) if name else ''
            flags=[]
            if not player:flags.append('PLAYER_UNRESOLVED')
            if not ctx['game_date']:flags.append('DATE_UNRESOLVED')
            if not ctx['matchup']:flags.append('MATCHUP_UNRESOLVED')
            if not ctx['team']:flags.append('TEAM_UNRESOLVED')
            if not after:flags.append('REASON_UNRESOLVED')
            # Lines with a status and no reason, or obvious wrapped/truncated
            # reasons, are NOT automatically trusted.
            if after and not (after.startswith('Injury/Illness') or after.startswith('Personal Reasons') or
                              after.startswith('Not With Team') or after.startswith('G League') or
                              after.startswith('Rest') or after.startswith('League Suspension') or
                              after.startswith('Return to Competition') or after.startswith('Health')):
                flags.append('REASON_FORMAT_UNVERIFIED')
            rid=hashlib.sha256(f'{sha}|{page["page"]}|{number}|{line}'.encode()).hexdigest()[:20]
            rec={'record_id':rid,'source_sha256':sha,'source_page':page['page'],
                 'source_line':number,'raw_text':line,'game_date':ctx['game_date'],
                 'matchup':ctx['matchup'],'team':ctx['team'],'player':player,
                 'status':sm.group(1).upper(),'reason':after,
                 'parse_status':'REVIEW_REQUIRED' if flags else 'AUTO_CANDIDATE',
                 'flags':'|'.join(flags),'eligible_for_asof_training':False}
            records.append(rec)
            if flags:abstentions.append(rec)
    return records,abstentions

def process_pdf(pdf_path, source_url, output_dir):
    from .injury_asof import parse_official_url,verify_pdf_bytes
    from .injury_pdf import extract_pdf_text
    parse_official_url(source_url)
    data=Path(pdf_path).read_bytes();sha=verify_pdf_bytes(data)
    rows,abstentions=parse_lines(extract_pdf_text(data),sha)
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    csvpath=out/(sha+'.auto_candidates.csv')
    with csvpath.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    report={'status':'RESEARCH_ONLY','source_sha256':sha,'source_url':source_url,
        'total_status_lines':len(rows),'auto_candidates':len(rows)-len(abstentions),
        'review_required':len(abstentions),'output_csv':str(csvpath),
        'historical_publication_verified':False,'eligible_for_asof_training':False,
        'warnings':['Auto-candidate is not verified truth','Carry-forward context is heuristic',
                    'Wrapped reason text may be incomplete','No historical as-of authorization']}
    (out/(sha+'.auto_manifest.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report
