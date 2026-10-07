"""Leakage-safe helpers for P0-S3 S8 historical reconstruction."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Iterable, Mapping, Sequence


class HistoricalReconstructionError(ValueError):
    """Raised when historical evidence violates the reconstruction contract."""


def _iso_date(value: object) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%b %d, %Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except ValueError as exc:
        raise HistoricalReconstructionError(f"Unparseable event date: {value!r}") from exc


def canonicalize_player_game_rows(rows: Iterable[Mapping[str, object]]) -> list[dict]:
    """Convert source-shaped player-game rows to the minimum S8 canonical shape.

    Accepted aliases intentionally cover common nba_api PlayerGameLogs fields.
    No outcome is converted into a pregame feature here; this function only
    normalizes historical evidence for the reconstruction audit.
    """
    out: list[dict] = []
    for row in rows:
        game_id = row.get("GAME_ID", row.get("game_id"))
        player_id = row.get("PLAYER_ID", row.get("player_id"))
        team_id = row.get("TEAM_ID", row.get("team_id"))
        event_date = row.get("GAME_DATE", row.get("event_date"))
        if game_id in (None, "") or player_id in (None, "") or team_id in (None, "") or event_date in (None, ""):
            raise HistoricalReconstructionError(
                "Each row requires game_id/GAME_ID, player_id/PLAYER_ID, "
                "team_id/TEAM_ID, and event_date/GAME_DATE."
            )
        out.append(
            {
                "game_id": str(game_id),
                "event_date": _iso_date(event_date),
                "player_id": str(player_id),
                "team_id": str(team_id),
            }
        )
    out.sort(key=lambda r: (r["event_date"], r["game_id"], r["player_id"]))
    keys = [(r["game_id"], r["player_id"]) for r in out]
    if len(keys) != len(set(keys)):
        raise HistoricalReconstructionError("Duplicate canonical (game_id, player_id) row detected.")
    return out


def choose_representative_target_date(rows: Sequence[Mapping[str, object]], fraction: float = 0.35) -> str:
    """Choose a deterministic in-season game date away from the season boundary."""
    dates = sorted({_iso_date(r.get("GAME_DATE", r.get("event_date"))) for r in rows})
    if len(dates) < 3:
        raise HistoricalReconstructionError("At least three distinct game dates are required.")
    if not 0.0 < fraction < 1.0:
        raise HistoricalReconstructionError("fraction must be strictly between 0 and 1.")
    idx = round((len(dates) - 1) * fraction)
    idx = max(1, min(len(dates) - 2, idx))
    return dates[idx]


def reconstruct_d1_rows(rows: Sequence[Mapping[str, object]], target_date: str) -> list[dict]:
    """Return only statistical evidence dated <= D-1 (equivalently < D)."""
    target = _iso_date(target_date)
    canonical = canonicalize_player_game_rows(rows)
    rebuilt = [r for r in canonical if r["event_date"] < target]
    if any(r["event_date"] >= target for r in rebuilt):
        raise HistoricalReconstructionError("D-1 reconstruction contains target-day/future evidence.")
    return rebuilt


def summarize_target_date_delta(rows: Sequence[Mapping[str, object]], target_date: str) -> dict:
    """Audit D-1 vs D counts.

    Players appearing on D must gain exactly one player-game row. Players not
    appearing on D must gain zero. This mirrors the successful P0-S2 POC-09
    boundary test without using D rows as predictive features.
    """
    target = _iso_date(target_date)
    canonical = canonicalize_player_game_rows(rows)
    before = Counter(r["player_id"] for r in canonical if r["event_date"] < target)
    through_d = Counter(r["player_id"] for r in canonical if r["event_date"] <= target)
    target_players = {r["player_id"] for r in canonical if r["event_date"] == target}

    deltas = {pid: through_d[pid] - before[pid] for pid in set(before) | set(through_d)}
    wrong_target = sorted(pid for pid in target_players if deltas.get(pid) != 1)
    wrong_non_target = sorted(pid for pid, delta in deltas.items() if pid not in target_players and delta != 0)

    return {
        "target_date": target,
        "target_player_count": len(target_players),
        "wrong_target_player_deltas": wrong_target,
        "wrong_non_target_player_deltas": wrong_non_target,
        "pass": bool(target_players) and not wrong_target and not wrong_non_target,
    }
