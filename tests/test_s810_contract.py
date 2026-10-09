import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

MODULE = Path(__file__).resolve().parents[1] / 'research/p0_s8/s8_10/contract.py'
spec = importlib.util.spec_from_file_location('s810_contract', MODULE)
import sys
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_allowlist_returns_only_approved_columns():
    df = pd.DataFrame({'minutes_last5_avg': [21.0], 'target_minutes': [33.0], 'pts': [12]})
    assert module.validate_predictors(df, ['minutes_last5_avg']).columns.tolist() == ['minutes_last5_avg']


@pytest.mark.parametrize('name', ['min', 'pts', 'reb', 'ast', 'fg3m', 'target_minutes', 'target_points', 'actual_pts', 'realized_ast', 'player_id', 'game_id', 'event_date', 'Target Minutes', 'points_target'])
def test_forbidden_columns(name):
    with pytest.raises(module.ContractViolation):
        module.validate_predictors(pd.DataFrame({name: [1]}), [name])


@pytest.mark.parametrize('values', [[np.nan], [np.inf], [-np.inf]])
def test_nonfinite(values):
    with pytest.raises(module.ContractViolation):
        module.validate_predictors(pd.DataFrame({'safe_feature': values}), ['safe_feature'])


def test_missing_and_duplicate_columns():
    with pytest.raises(module.ContractViolation):
        module.validate_predictors(pd.DataFrame({'a': [1]}), ['b'])
    with pytest.raises(module.ContractViolation):
        module.validate_predictors(pd.DataFrame([[1, 2]], columns=['a', 'a']), ['a'])
    with pytest.raises(module.ContractViolation):
        module.validate_predictors(pd.DataFrame({'a': [1]}), ['a', 'a'])


def test_nonnumeric_and_bool():
    for value in ['abc', True]:
        with pytest.raises(module.ContractViolation):
            module.validate_predictors(pd.DataFrame({'safe_feature': [value]}), ['safe_feature'])


@pytest.mark.parametrize('train,test', [
    (['2024-01-01'], ['2024-01-01']),
    (['2024-01-04'], ['2024-01-02']),
    (['2024-01-01', '2024-01-05'], ['2024-01-04']),
    ([], ['2024-01-04']),
    (['2024-01-01'], ['bad']),
])
def test_bad_folds(train, test):
    with pytest.raises(module.ContractViolation):
        module.validate_chronological_fold(train, test)


def test_valid_fold():
    x = module.validate_chronological_fold(['2024-01-01'], ['2024-01-02'])
    assert x.train_end < x.test_start


def test_training_not_authorized():
    with pytest.raises(module.ContractViolation, match='BLOCK_TRAINING'):
        module.assert_research_only()
