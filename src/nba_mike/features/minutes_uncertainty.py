"""D-1 safe, prequential calibration of EWM-5 minutes intervals (research only)."""
import numpy as np
import pandas as pd

REQUIRED = ("event_date","player_id","game_id","target_minutes","ewm_5","prior_dates","role_change_flag")

def uncertainty_frame(form, *, warmup_dates=30, min_calibration=100, alpha=0.1):
    if not 0 < alpha < 1: raise ValueError("alpha must be between 0 and 1")
    missing=set(REQUIRED)-set(form.columns)
    if missing: raise ValueError(f"missing columns: {sorted(missing)}")
    f=form.copy()
    f["event_date"]=pd.to_datetime(f["event_date"],errors="coerce").dt.normalize()
    if f.event_date.isna().any(): raise ValueError("invalid dates")
    if f.duplicated(["player_id","game_id"]).any(): raise ValueError("duplicate player-game")
    f=f.sort_values(["event_date","player_id","game_id"],kind="stable")
    dates=sorted(f.event_date.unique())
    residuals=[]
    output=[]
    for day_index,day in enumerate(dates):
        today=f[f.event_date==day]
        # Calibration uses only earlier dates, including all previous player outcomes.
        if day_index>=warmup_dates and len(residuals)>=min_calibration:
            scores=np.sort(np.asarray(residuals,dtype=float))
            rank=min(len(scores),int(np.ceil((len(scores)+1)*(1-alpha))))
            radius=float(scores[rank-1])
            for r in today.itertuples(index=False):
                if r.prior_dates<5 or not np.isfinite(r.ewm_5):continue
                estimate=float(r.ewm_5)
                lo=max(0.,estimate-radius);hi=min(60.,estimate+radius)
                actual=float(r.target_minutes)
                output.append({"event_date":pd.Timestamp(day),"player_id":r.player_id,
                    "game_id":r.game_id,"actual":actual,"estimate":estimate,
                    "lower":lo,"upper":hi,"radius":radius,"covered":int(lo<=actual<=hi),
                    "abs_error":abs(actual-estimate),"role_change_flag":int(r.role_change_flag),
                    "prior_dates":int(r.prior_dates),"calibration_n":len(residuals)})
        # Update only after every same-date forecast has been evaluated.
        for r in today.itertuples(index=False):
            if r.prior_dates>=5 and np.isfinite(r.ewm_5):
                residuals.append(abs(float(r.target_minutes)-float(r.ewm_5)))
    return pd.DataFrame(output,columns=["event_date","player_id","game_id","actual","estimate","lower",
        "upper","radius","covered","abs_error","role_change_flag","prior_dates","calibration_n"])

def summarize(frame):
    if frame.empty:return {"n":0,"coverage":None,"mean_width":None,"mae":None,"error_over_5":None,"error_over_10":None,"error_over_15":None}
    e=frame.abs_error
    return {"n":int(len(frame)),"coverage":float(frame.covered.mean()),
        "mean_width":float((frame.upper-frame.lower).mean()),"mae":float(e.mean()),
        "error_over_5":float((e>5).mean()),"error_over_10":float((e>10).mean()),
        "error_over_15":float((e>15).mean())}
