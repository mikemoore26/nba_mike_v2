"""S8.13 tests; no training executed."""
import importlib.util
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'research/p0_s8/s8_13/boundary.py'
spec = importlib.util.spec_from_file_location('s813_boundary', P)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

@pytest.mark.parametrize('evidence', [None, {}, {'historical_asof_publication': {'status': 'VERIFIED', 'artifact': 'x'}},
    {k: {'status': 'VERIFIED', 'artifact': 'self-reported'} for k in mod.REQUIRED_GATES}])
def test_claims_never_authorize(evidence):
    result = mod.inspect_evidence(evidence)
    assert result.decision == 'BLOCK_TRAINING'
    assert not result.training_eligible
    assert len(result.gate_results) == len(mod.REQUIRED_GATES)

@pytest.mark.parametrize('kwargs', [{}, {'evidence': {}}, {'predictors': ['x']},
    {'evidence': {'all': True}, 'dates': [1, 2]}])
def test_training_always_denied(kwargs):
    with pytest.raises(mod.BoundaryDenied, match='BLOCK_TRAINING'):
        mod.require_training_authorization(**kwargs)

def test_claims_distinguished_from_verification():
    evidence = {k: {'status': 'VERIFIED', 'artifact': 'unverified reference'} for k in mod.REQUIRED_GATES}
    result = mod.inspect_evidence(evidence)
    assert all(g.state == 'CLAIMED_UNVALIDATED' for g in result.gate_results)

def test_missing_gates():
    result = mod.inspect_evidence({})
    assert all(g.state == 'MISSING' for g in result.gate_results)

def test_contract_input_rejected_without_real_contract():
    class FakeContract:
        @staticmethod
        def validate_predictors(frame, allowlist):
            raise ValueError('forbidden')
    result = mod.validate_research_inputs(None, ['pts'], [], [], FakeContract)
    assert result['status'] == 'REJECTED_INPUT'
    assert result['decision'] == 'BLOCK_TRAINING'
