"""Pregame-safe candidate minutes forecasts, keyed by player and calendar date.

S5 research only: windows count prior distinct dates, not necessarily games.
"""
import numpy as np
import pandas as pd

WINDOWS = (2, 3, 4, 5, 6, 8, 10, 15)
CANDIDATES = tuple(f"last_{n}" for n in WINDOWS) + ("season", "ewm_3", "ewm_5", "ewm_10")
REQUIRED = ("game_id", "event_date", "player_id", "min")


def make_form_frame(source: pd.DataFrame) -> pd.DataFrame:
    """Return one outcome row per player-game, with strict prior-calendar-day forecasts."""
    missing = set(REQUIRED) - set(source.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    x = source.copy()
    x["event_date"] = pd.to_datetime(x.event_date, errors="coerce").dt.normalize()
    x["min"] = pd.to_numeric(x["min"], errors="coerce")
    if x.event_date.isna().any() or x["min"].isna().any() or not np.isfinite(x["min"]).all():
        raise ValueError("invalid dates/minutes")
    if (x["min"] < 0).any() or (x["min"] > 60).any():
        raise ValueError("minutes outside [0,60]")
    if x.duplicated(["player_id", "game_id"]).any():
        raise ValueError("duplicate player-game")
    x = x.sort_values(["player_id", "event_date", "game_id"], kind="stable")
    day = (x.groupby(["player_id", "event_date"], as_index=False)
             .agg(day_minutes=("min", "mean"), day_games=("game_id", "size")))
    day = day.sort_values(["player_id", "event_date"], kind="stable")
    g = day.groupby("player_id", sort=False)
    day["prior_games"] = g.day_games.cumsum() - day.day_games
    day["prior_dates"] = g.cumcount()
    for n in WINDOWS:
        day[f"last_{n}"] = g.day_minutes.transform(lambda s: s.shift(1).rolling(n, min_periods=1).mean())
    day["season"] = g.day_minutes.transform(lambda s: s.shift(1).expanding(min_periods=1).mean())
    for span in (3, 5, 10):
        day[f"ewm_{span}"] = g.day_minutes.transform(
            lambda s: s.shift(1).ewm(span=span, adjust=False, ignore_na=True).mean()
        )
    day["recent_delta"] = (day["last_3"] - day["season"]).abs()
    day["role_change_flag"] = (day.recent_delta >= 6).astype(int)
    fields = ["player_id", "event_date", "prior_games", "prior_dates", "recent_delta", "role_change_flag", *CANDIDATES]
    out = x.merge(day[fields], on=["player_id", "event_date"], how="left", validate="many_to_one")
    return out.rename(columns={"min": "target_minutes"})


def score_forecasts(frame: pd.DataFrame, mask=None) -> pd.DataFrame:
    """Per-candidate MAE on identical eligible rows (>=5 prior dates)."""
    eligible = frame.loc[frame.prior_dates >= 5]
    if mask is not None:
        eligible = eligible.loc[mask.reindex(eligible.index, fill_value=False)]
    rows = []
    for name in CANDIDATES:
        good = eligible[[name, "target_minutes"]].dropna()
        rows.append({"candidate": name, "n": len(good),
                     "mae": float((good[name] - good.target_minutes).abs().mean()) if len(good) else None})
    return pd.DataFrame(rows)


def expanding_prequential(frame: pd.DataFrame, min_train_dates=30, min_prior_dates=5):
    """Chronological day-level evaluation of a *fixed* baseline vs adaptive selection.

    Adaptive candidate selected using ONLY previous days' pooled absolute errors.
    No future error is used to select a candidate. Returns predictions and selections.
    """
    f = frame.sort_values(["event_date", "player_id", "game_id"], kind="stable").copy()
    history = {c: [] for c in CANDIDATES}
    result = []
    dates = f.event_date.drop_duplicates().sort_values().tolist()
    for i, date in enumerate(dates):
        today = f.loc[f.event_date == date]
        if i >= min_train_dates:
            for _, r in today.iterrows():
                if r.prior_dates < min_prior_dates or pd.isna(r.last_5):
                    continue
                eligible = [c for c in CANDIDATES if len(history[c]) >= 100 and pd.notna(r[c])]
                selected = min(eligible, key=lambda c: (np.mean(history[c]), CANDIDATES.index(c))) if eligible else "last_5"
                result.append({"event_date": date, "player_id": r.player_id, "game_id": r.game_id,
                               "actual": float(r.target_minutes), "baseline": float(r.last_5),
                               "adaptive": float(r[selected]), "selected": selected,
                               "role_change_flag": int(r.role_change_flag)})
        # Update only after predictions for the whole date have been issued.
        for _, r in today.iterrows():
            if r.prior_dates < min_prior_dates:
                continue
            for c in CANDIDATES:
                if pd.notna(r[c]):
                    history[c].append(abs(float(r[c]) - float(r.target_minutes)))
    return pd.DataFrame(result, columns=["event_date", "player_id", "game_id", "actual", "baseline", "adaptive", "selected", "role_change_flag"])
