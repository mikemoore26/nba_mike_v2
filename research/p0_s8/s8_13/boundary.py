"""S8.13 research-only training boundary architecture. NEVER trains or authorizes.

Evidence metadata is evaluated for completeness, NOT trusted as independent proof.
This module deliberately has no fit, predict, or training dispatch function.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Mapping, Sequence

REQUIRED_GATES = (
    'historical_asof_publication',
    'feature_lineage_asof',
    'pregame_player_population',
    'dnp_reconciliation',
    'calendar_restart_88_resolution',
    'chronological_folds',
    'fold_local_preprocessing',
    'fold_local_calibration',
    'predictor_allowlist_verified',
    'target_exclusion_verified',
)

class BoundaryDenied(RuntimeError):
    pass

@dataclass(frozen=True)
class GateResult:
    name: str
    state: str
    reason: str

@dataclass(frozen=True)
class BoundaryDecision:
    status: str
    decision: str
    training_eligible: bool
    gate_results: tuple[GateResult, ...]
    def as_dict(self) -> dict:
        result = asdict(self)
        result['gate_results'] = [asdict(x) for x in self.gate_results]
        return result


def inspect_evidence(evidence: Mapping[str, object] | None) -> BoundaryDecision:
    """Descriptive research audit; user-provided claims never confer authorization."""
    evidence = evidence if isinstance(evidence, Mapping) else {}
    gates = []
    for gate in REQUIRED_GATES:
        item = evidence.get(gate)
        if not isinstance(item, Mapping):
            gates.append(GateResult(gate, 'MISSING', 'No structured evidence supplied'))
        elif item.get('status') != 'VERIFIED':
            gates.append(GateResult(gate, 'UNVERIFIED', 'Evidence does not assert VERIFIED'))
        elif not isinstance(item.get('artifact'), str) or not item['artifact'].strip():
            gates.append(GateResult(gate, 'UNVERIFIED', 'No supporting artifact reference'))
        else:
            gates.append(GateResult(gate, 'CLAIMED_UNVALIDATED',
                'Evidence assertion is untrusted; independent verification required'))
    return BoundaryDecision('RESEARCH_ONLY', 'BLOCK_TRAINING', False, tuple(gates))


def require_training_authorization(*, evidence: Mapping[str, object] | None = None,
                                   predictors: Sequence[str] | None = None,
                                   dates: object = None) -> None:
    """Non-overridable denial: no runtime training path exists in S8.13."""
    raise BoundaryDenied('BLOCK_TRAINING: S8.13 is research-only; independent governance gates not certified')


def validate_research_inputs(frame, allowlist, train_dates, test_dates, contract_module):
    """Exercise S8.10 validations, then DENY authorization regardless of result.

    The returned dict only describes local checks; it cannot authorize training.
    """
    try:
        x = contract_module.validate_predictors(frame, allowlist)
        fold = contract_module.validate_chronological_fold(train_dates, test_dates)
    except Exception as exc:
        return {'status': 'REJECTED_INPUT', 'decision': 'BLOCK_TRAINING',
                'training_eligible': False, 'reason': f'{type(exc).__name__}: {exc}'}
    return {'status': 'SYNTHETIC_CONTRACT_PASS', 'decision': 'BLOCK_TRAINING',
            'training_eligible': False, 'predictor_columns': list(x.columns),
            'train_end': fold.train_end.isoformat(), 'test_start': fold.test_start.isoformat(),
            'reason': 'Valid synthetic input is not historical as-of authorization'}
