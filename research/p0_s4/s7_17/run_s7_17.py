import json
from pathlib import Path
from nba_mike.data.injury_reason_recovery import run

if __name__=='__main__':
    root=Path(__file__).resolve().parents[3]
    result=run(root/'research/p0_s4/s7_14/input_pdfs',
               root/'research/p0_s4/s7_14/results',
               root/'research/p0_s4/s7_17/results')
    print(json.dumps(result,indent=2))
