"""S8.22.5 independent schedule comparison; research only, no automatic source approval."""
from __future__ import annotations
import argparse
import csv
import importlib.util
import json
from datetime import date, datetime, timezone
from pathlib import Path

FIELDS=['provider','provider_game_id','official_nba_game_id','game_date','home_provider_team_id','away_provider_team_id','tipoff_utc','tipoff_status','game_status']


def rows(path, required):
    with Path(path).open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not set(required).issubset(reader.fieldnames):
            raise ValueError(f'MISSING_COLUMNS: {sorted(set(required)-set(reader.fieldnames or []))}')
        return list(reader)


def utc(s):
    if not s or not isinstance(s,str): return None
    try:
        v=datetime.fromisoformat(s.replace('Z','+00:00'))
        return v.astimezone(timezone.utc) if v.tzinfo else None
    except ValueError: return None


def audit(provider_csv, game_date, official_csv=None, team_map_csv=None, official_source=None):
    if date.fromisoformat(game_date).isoformat()!=game_date: raise ValueError('INVALID_DATE')
    games=rows(provider_csv,FIELDS)
    relevant=[g for g in games if g['game_date']==game_date]
    other_dates=len(games)-len(relevant)
    report={'milestone':'S8.22.5','mode':'OFFLINE_INDEPENDENT_SCHEDULE_AUDIT','requested_date':game_date,
            'provider_rows':len(relevant),'other_date_rows':other_dates,
            'schedule_state':'EMPTY_SCHEDULE_UNVERIFIED' if not relevant else 'PROVIDER_GAMES_PRESENT_UNVERIFIED',
            'independent_comparison':'NOT_PERFORMED','source_provenance':'NOT_PROVIDED',
            'official_nba_id_mapping':'UNVERIFIED','tipoff_accuracy':'UNVERIFIED',
            'coverage':'UNVERIFIED','provider_entitlement':'NOT_INDEPENDENTLY_VERIFIED',
            'pregame_player_eligibility_verified':False,'training_eligible':False,
            'status':'RESEARCH_ONLY','decision':'BLOCK_TRAINING','findings':[]}
    comparisons=[]
    if bool(official_csv)!=bool(team_map_csv): raise ValueError('OFFICIAL_AND_TEAM_MAP_REQUIRED_TOGETHER')
    if official_csv:
        if not official_source or not official_source.strip(): raise ValueError('OFFICIAL_SOURCE_PROVENANCE_REQUIRED')
        official=rows(official_csv,['official_nba_game_id','game_date','home_team','away_team','tipoff_utc'])
        mapping=rows(team_map_csv,['provider_team_id','official_team'])
        mp={}
        for r in mapping:
            if not r['provider_team_id'] or not r['official_team'] or r['provider_team_id'] in mp:
                raise ValueError('INVALID_TEAM_CROSSWALK')
            mp[r['provider_team_id']]=r['official_team'].strip().upper()
        official=[r for r in official if r['game_date']==game_date]
        by_match={}
        for r in official:
            if not r['official_nba_game_id'] or not r['home_team'] or not r['away_team']:
                raise ValueError('INVALID_OFFICIAL_ROW')
            k=(r['home_team'].strip().upper(),r['away_team'].strip().upper())
            if k in by_match: raise ValueError('DUPLICATE_OFFICIAL_MATCHUP')
            by_match[k]=r
        seen=set(); verified=0; time_match=0
        for g in relevant:
            k=(mp.get(g['home_provider_team_id']),mp.get(g['away_provider_team_id']))
            match=by_match.get(k) if all(k) else None
            state='UNMAPPED_TEAM' if not all(k) else 'NO_OFFICIAL_MATCH'
            diff=None
            if match:
                if match['official_nba_game_id'] in seen: raise ValueError('DUPLICATE_PROVIDER_MATCH')
                seen.add(match['official_nba_game_id']);verified+=1
                a,b=utc(g['tipoff_utc']),utc(match['tipoff_utc'])
                diff=round(abs((a-b).total_seconds())/60,2) if a and b else None
                state='MATCH_TIME_WITHIN_5_MIN' if diff is not None and diff<=5 else ('TIME_UNVERIFIED' if diff is None else 'TIME_DISAGREES')
                if diff is not None and diff<=5:time_match+=1
            comparisons.append({'provider_game_id':g['provider_game_id'],
                'official_nba_game_id_candidate':match['official_nba_game_id'] if match else '',
                'match_status':state,'tipoff_difference_minutes':diff if diff is not None else ''})
        report.update(independent_comparison='COMPLETED_OFFLINE',source_provenance=official_source,
                      official_rows=len(official),matched_matchups=verified,
                      tipoff_matches_within_5min=time_match,unmatched_provider=len(relevant)-verified,
                      unmatched_official=len(official)-len(seen),
                      official_nba_id_mapping='CANDIDATE_ONLY_REQUIRES_REVIEW' if verified else 'UNVERIFIED',
                      tipoff_accuracy='CANDIDATE_WITHIN_5_MIN_REQUIRES_REVIEW' if time_match else 'UNVERIFIED')
        if not relevant and official:
            report['schedule_state']='EMPTY_SCHEDULE_CONTRADICTED_BY_REFERENCE'
        elif relevant and len(official)==len(relevant)==verified and time_match==verified:
            report['schedule_state']='CANDIDATE_DATE_COVERAGE_MATCH_REQUIRES_REVIEW'
        elif relevant:
            report['schedule_state']='PARTIAL_OR_UNVERIFIED_COVERAGE'
        report['findings'].append('Reference is user-supplied; provenance and independent acquisition must be reviewed.')
    else:
        report['findings'].append('No independent official schedule supplied; cannot certify empty or populated coverage.')
    report['findings'].append('No provider IDs promoted to official IDs; no training or automated schedule approval.')
    return report,comparisons


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root',type=Path,default=Path('.'))
    p.add_argument('--date',required=True)
    p.add_argument('--provider-csv',type=Path)
    p.add_argument('--official-csv',type=Path)
    p.add_argument('--team-map-csv',type=Path)
    p.add_argument('--official-source',help='Independent source name, URL and acquisition date')
    a=p.parse_args();root=a.project_root.resolve()
    path=a.provider_csv or root/'research/p0_s8/s8_22_4/results/s8_22_4_games.csv'
    report,comparison=audit(path,a.date,a.official_csv,a.team_map_csv,a.official_source)
    out=root/'research/p0_s8/s8_22_5/results';out.mkdir(parents=True,exist_ok=True)
    (out/'s8_22_5_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    with (out/'s8_22_5_comparison.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['provider_game_id','official_nba_game_id_candidate','match_status','tipoff_difference_minutes'])
        writer.writeheader();writer.writerows(comparison)
    print(json.dumps({k:report[k] for k in ('schedule_state','provider_rows','independent_comparison','decision')},indent=2))

if __name__=='__main__': main()
