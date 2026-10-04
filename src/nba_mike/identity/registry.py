from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable

ENTITY_TYPES = ("player", "team", "game")
PREFIX = {"player": "P", "team": "T", "game": "G"}

class IdentityConflictError(ValueError):
    """Raised when an operation would silently change established identity."""

@dataclass(frozen=True)
class Resolution:
    status: str
    entity_type: str
    canonical_id: str | None = None
    candidates: tuple[str, ...] = ()
    reason: str | None = None

@dataclass
class Entity:
    canonical_id: str
    entity_type: str
    display_name: str
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass
class Membership:
    player_id: str
    team_id: str
    valid_from: str
    valid_to: str | None = None
    provenance: str | None = None

class IdentityRegistry:
    schema_version = "1.0"

    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.source_mappings: dict[str, str] = {}
        self.aliases: dict[str, set[str]] = {}
        self.memberships: list[Membership] = []
        self._counters = {t: 0 for t in ENTITY_TYPES}

    @staticmethod
    def _source_key(entity_type: str, source_name: str, source_id: str) -> str:
        if entity_type not in ENTITY_TYPES:
            raise ValueError(f"unsupported entity_type: {entity_type}")
        if not str(source_name).strip() or not str(source_id).strip():
            raise ValueError("source_name and source_id are required")
        return f"{entity_type}|{str(source_name).strip()}|{str(source_id)}"

    def _new_id(self, entity_type: str) -> str:
        if entity_type not in ENTITY_TYPES:
            raise ValueError(f"unsupported entity_type: {entity_type}")
        self._counters[entity_type] += 1
        return f"{PREFIX[entity_type]}{self._counters[entity_type]:08d}"

    def create_entity(self, entity_type: str, display_name: str, **attributes: Any) -> str:
        if not str(display_name).strip():
            raise ValueError("display_name is required")
        cid = self._new_id(entity_type)
        self.entities[cid] = Entity(cid, entity_type, str(display_name).strip(), dict(attributes))
        return cid

    def create_team(self, display_name: str, **attributes: Any) -> str:
        return self.create_entity("team", display_name, **attributes)

    def create_player(self, display_name: str, **attributes: Any) -> str:
        return self.create_entity("player", display_name, **attributes)

    def create_game(self, event_date: str, home_team_id: str, away_team_id: str, **attributes: Any) -> str:
        self._require_type(home_team_id, "team")
        self._require_type(away_team_id, "team")
        if home_team_id == away_team_id:
            raise ValueError("home and away teams must differ")
        date.fromisoformat(event_date)
        attrs = {"event_date": event_date, "home_team_id": home_team_id, "away_team_id": away_team_id, **attributes}
        return self.create_entity("game", f"{away_team_id} at {home_team_id} {event_date}", **attrs)

    def _require_type(self, canonical_id: str, entity_type: str) -> Entity:
        ent = self.entities.get(canonical_id)
        if ent is None:
            raise KeyError(f"unknown canonical_id: {canonical_id}")
        if ent.entity_type != entity_type:
            raise ValueError(f"{canonical_id} is {ent.entity_type}, expected {entity_type}")
        return ent

    def add_source_mapping(self, entity_type: str, source_name: str, source_id: str, canonical_id: str) -> None:
        self._require_type(canonical_id, entity_type)
        key = self._source_key(entity_type, source_name, source_id)
        existing = self.source_mappings.get(key)
        if existing is not None and existing != canonical_id:
            raise IdentityConflictError(f"source identity {key} already maps to {existing}; refusing remap to {canonical_id}")
        self.source_mappings[key] = canonical_id

    def resolve_source(self, entity_type: str, source_name: str, source_id: str) -> Resolution:
        key = self._source_key(entity_type, source_name, source_id)
        cid = self.source_mappings.get(key)
        if cid is None:
            return Resolution("UNRESOLVED", entity_type, reason="no exact source mapping")
        return Resolution("RESOLVED", entity_type, canonical_id=cid)

    def add_alias(self, canonical_id: str, alias: str) -> None:
        ent = self.entities.get(canonical_id)
        if ent is None:
            raise KeyError(f"unknown canonical_id: {canonical_id}")
        norm = self._normalize_alias(alias)
        if not norm:
            raise ValueError("alias is required")
        key = f"{ent.entity_type}|{norm}"
        self.aliases.setdefault(key, set()).add(canonical_id)

    @staticmethod
    def _normalize_alias(value: str) -> str:
        return " ".join(str(value).casefold().split())

    def resolve_alias(self, entity_type: str, alias: str) -> Resolution:
        if entity_type not in ENTITY_TYPES:
            raise ValueError(f"unsupported entity_type: {entity_type}")
        candidates = tuple(sorted(self.aliases.get(f"{entity_type}|{self._normalize_alias(alias)}", set())))
        if not candidates:
            return Resolution("UNRESOLVED", entity_type, reason="alias not registered")
        if len(candidates) > 1:
            return Resolution("AMBIGUOUS", entity_type, candidates=candidates, reason="alias maps to multiple canonical entities")
        return Resolution("RESOLVED", entity_type, canonical_id=candidates[0])

    def add_membership(self, player_id: str, team_id: str, valid_from: str, valid_to: str | None = None, provenance: str | None = None) -> None:
        self._require_type(player_id, "player")
        self._require_type(team_id, "team")
        start = date.fromisoformat(valid_from)
        if valid_to is not None and date.fromisoformat(valid_to) <= start:
            raise ValueError("valid_to must be after valid_from")
        self.memberships.append(Membership(player_id, team_id, valid_from, valid_to, provenance))

    def teams_for_player_on(self, player_id: str, event_date: str) -> tuple[str, ...]:
        self._require_type(player_id, "player")
        d = date.fromisoformat(event_date)
        teams = []
        for m in self.memberships:
            if m.player_id != player_id:
                continue
            start = date.fromisoformat(m.valid_from)
            end = date.fromisoformat(m.valid_to) if m.valid_to else None
            if d >= start and (end is None or d < end):
                teams.append(m.team_id)
        return tuple(sorted(set(teams)))

    @staticmethod
    def player_game_key(game_id: str, player_id: str) -> tuple[str, str]:
        return (str(game_id), str(player_id))

    @staticmethod
    def assert_unique_player_games(rows: Iterable[dict[str, Any]]) -> None:
        seen: set[tuple[str, str]] = set()
        for row in rows:
            key = (str(row["game_id"]), str(row["player_id"]))
            if key in seen:
                raise IdentityConflictError(f"duplicate player-game key: {key}")
            seen.add(key)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "counters": dict(self._counters),
            "entities": [asdict(self.entities[k]) for k in sorted(self.entities)],
            "source_mappings": dict(sorted(self.source_mappings.items())),
            "aliases": {k: sorted(v) for k, v in sorted(self.aliases.items())},
            "memberships": [asdict(m) for m in self.memberships],
        }

    def save_json(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "IdentityRegistry":
        if payload.get("schema_version") != cls.schema_version:
            raise ValueError("unsupported identity registry schema_version")
        obj = cls()
        obj._counters.update({k: int(v) for k, v in payload.get("counters", {}).items()})
        for raw in payload.get("entities", []):
            ent = Entity(**raw)
            obj.entities[ent.canonical_id] = ent
        obj.source_mappings = {str(k): str(v) for k, v in payload.get("source_mappings", {}).items()}
        obj.aliases = {str(k): set(map(str, v)) for k, v in payload.get("aliases", {}).items()}
        obj.memberships = [Membership(**raw) for raw in payload.get("memberships", [])]
        obj.validate()
        return obj

    @classmethod
    def load_json(cls, path: str | Path) -> "IdentityRegistry":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def validate(self) -> None:
        for key, cid in self.source_mappings.items():
            if cid not in self.entities:
                raise IdentityConflictError(f"mapping {key} references missing {cid}")
            entity_type = key.split("|", 1)[0]
            if self.entities[cid].entity_type != entity_type:
                raise IdentityConflictError(f"mapping type mismatch for {key}")
        for key, ids in self.aliases.items():
            entity_type = key.split("|", 1)[0]
            for cid in ids:
                self._require_type(cid, entity_type)
        for m in self.memberships:
            self._require_type(m.player_id, "player")
            self._require_type(m.team_id, "team")
