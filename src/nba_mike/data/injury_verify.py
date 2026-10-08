"""S7.12 structural checks of S7.11 injury candidates. Research-only."""
from __future__ import annotations
import csv, hashlib, json, re
from collections import Counter
from pathlib import Path

ABBR = {'ATL':'Atlanta Hawks','BKN':'Brooklyn Nets','BOS':'Boston Celtics','CHA':'Charlotte Hornets','CHI':'Chicago Bulls','CLE':'Cleveland Cavaliers','DAL':'Dallas Mavericks','DEN':'Denver Nuggets','DET':'Detroit Pistons','GSW':'Golden State Warriors','HOU':'Houston Rockets','IND':'Indiana Pacers','LAC':'Los Angeles Clippers','LAL':'Los Angeles Lakers','MEM':'Memphis Grizzlies','MIA':'Miami Heat','MIL':'Milwaukee Bucks','MIN':'Minnesota Timberwolves','NOP':'New Orleans Pelicans','NYK':'New York Knicks','OKC':'Oklahoma City Thunder','ORL':'Orlando Magic','PHI':'Philadelphia 76ers','PHX':'Phoenix Suns','POR':'Portland Trail Blazers','SAC':'Sacramento Kings','SAS':'San Antonio Spurs','TOR':'Toronto Raptors','UTA':'Utah Jazz','WAS':'Washington Wizards'}
# Canonical 30-team identifiers and source-document name aliases.
# Keep ABBR canonical for compatibility with S7.12 callers.
TEAM_ALIASES = {
    'LAC': ('LA Clippers', 'Los Angeles Clippers'),
    'BKN': ('Brooklyn Nets', 'Brooklyn Nets'),
    'NYK': ('New York Knicks', 'NY Knicks'),
    'GSW': ('Golden State Warriors',),
    'SAS': ('San Antonio Spurs',),
}

def normalize_team_name(name):
    """Return canonical team abbreviation or None; never infer from a player name."""
    cleaned = re.sub(r'\s+', ' ', str(name or '').strip()).casefold()
    if not cleaned:
        return None
    for abbr, canonical in ABBR.items():
        if cleaned == canonical.casefold() or cleaned == abbr.casefold():
            return abbr
        if any(cleaned == alias.casefold() for alias in TEAM_ALIASES.get(abbr, ())):
            return abbr
    return None

def team_in_matchup(team, matchup):
    m = MATCH.fullmatch(str(matchup or '').strip())
    if not m:
        return False
    return normalize_team_name(team) in m.groups()

MATCH = re.compile(r'^([A-Z]{3})@([A-Z]{3})$')
PROV = re.compile(r'^EXPLICIT:p(\d+):y([0-9]+(?:\.[0-9]+)?)$')
FIELDS=('source_page','player','status','game_date','matchup','team','issues','risk','date_provenance','matchup_provenance','team_provenance')

def verify(rows, events):
    problems=[]; count=Counter(); seen=Counter((str(r.get('source_page','')),r.get('player',''),r.get('status','')) for r in rows)
    dates=[(int(e['page']),float(e['y']),e['value']) for e in events if e['type']=='DATE' and str(e.get('y','')).strip()]
    dates.sort()
    for r in rows:
        issues=[]
        page=int(r['source_page']); y=float(r.get('source_y') or 0)
        matchup=r.get('matchup',''); team=r.get('team',''); date=r.get('game_date','')
        m=MATCH.fullmatch(matchup)
        if not m: issues.append('MATCHUP_MISSING_OR_INVALID')
        elif not team_in_matchup(team,matchup):issues.append('TEAM_NOT_IN_MATCHUP')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',date):issues.append('DATE_MISSING_OR_INVALID')
        latest=next((v for p,yy,v in reversed(dates) if (p,yy)<=(page,y)),None)
        if latest:
            mm,dd,yyyy=latest.split('/') if '/' in latest else ('','','')
            normalized=f'{yyyy}-{mm}-{dd}' if yyyy else latest
            if date!=normalized:issues.append('DATE_CONTRADICTS_EXPLICIT_EVENT')
        else: issues.append('NO_PRIOR_EXPLICIT_DATE_EVENT')
        for field in ('date','matchup','team'):
            prov=r.get(f'{field}_provenance','')
            pm=PROV.fullmatch(prov)
            if not pm:issues.append(f'{field.upper()}_PROVENANCE_INVALID');continue
            pp,py=int(pm.group(1)),float(pm.group(2))
            if (pp,py)>(page,y):issues.append(f'{field.upper()}_PROVENANCE_IN_FUTURE')
            expected_type={'date':'DATE','matchup':'MATCHUP','team':'TEAM'}[field]
            if not any(e['type']==expected_type and int(e['page'])==pp and abs(float(e['y'])-py)<0.015 and (e['value']==(date if field=='date' else r[field])) for e in events if str(e.get('y','')).strip()):
                issues.append(f'{field.upper()}_PROVENANCE_EVENT_MISMATCH')
        if seen[(str(page),r.get('player',''),r.get('status',''))]>1:issues.append('DUPLICATE_PAGE_PLAYER_STATUS')
        if r.get('parse_status')!='REVIEW_REQUIRED' or str(r.get('eligible_for_asof_training','')).lower() not in ('false','0'):
            issues.append('UNSAFE_TRAINING_LABEL')
        risk='FLAGGED' if issues else ('CROSS_PAGE_REVIEW' if any((PROV.fullmatch(r.get(f'{k}_provenance','') or '') and int(PROV.fullmatch(r[f'{k}_provenance']).group(1))<page) for k in ('date','matchup','team')) else 'SPOT_CHECK')
        for issue in issues:count[issue]+=1
        problems.append({**{k:r.get(k,'') for k in FIELDS},'issues':'|'.join(issues),'risk':risk})
    return problems,{'records':len(rows),'flagged_records':sum(bool(r['issues']) for r in problems),'issues_by_type':dict(count),'cross_page_review':sum(r['risk']=='CROSS_PAGE_REVIEW' for r in problems),'spot_check':sum(r['risk']=='SPOT_CHECK' for r in problems)}

def _load(path):
    with Path(path).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def run(pdf,candidates,events,out):
    pdf=Path(pdf); raw=pdf.read_bytes()
    if not raw.startswith(b'%PDF-'):raise ValueError('Not a PDF')
    sha=hashlib.sha256(raw).hexdigest()
    rows=_load(candidates); ev=_load(events)
    if not rows or any(r.get('source_sha256')!=sha for r in rows):raise ValueError('Source SHA mismatch')
    checked,summary=verify(rows,ev)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    cp=out/f'{sha}.s7_12_checks.csv'; sp=out/f'{sha}.s7_12_review_sample.csv'; jp=out/f'{sha}.s7_12_report.json'
    def write(path,rs):
        with path.open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction='ignore');w.writeheader();w.writerows(rs)
    write(cp,checked)
    prioritized=sorted(checked,key=lambda r: (0 if r['risk']=='FLAGGED' else 1 if r['risk']=='CROSS_PAGE_REVIEW' else 2,int(r['source_page']),r['player']))
    write(sp,prioritized[:min(16,len(prioritized))])
    report={'status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','source_sha256':sha,**summary,'records_modified':0,'historical_publication_verified':False,'eligible_for_asof_training':False,'checks_csv':str(cp),'review_sample_csv':str(sp),'limitations':['Consistency checks are not independent visual ground truth','Provenance refers to parser-generated section events','Additional distinct PDFs and human-reviewed samples required before parser promotion','Publication-time verification remains outstanding']}
    jp.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report
