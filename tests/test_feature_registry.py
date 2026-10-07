import pandas as pd
import pytest
from nba_mike.features import FeatureRegistryError, validate_feature_registry

def valid():
    return pd.DataFrame([{
      "feature_name":"x","feature_group":"player_history","description":"x",
      "source_domain":"canonical","pregame_available":True,
      "historical_available":True,"today_available":True,
      "missing_value_policy":"flag","leakage_checked":True,
      "coverage_status":"PASS","research_status":"APPROVED_BASELINE",
      "feature_version":"v1","notes":""
    }])

def test_valid_registry(): assert len(validate_feature_registry(valid()))==1
def test_duplicate_rejected():
    x=valid()
    with pytest.raises(FeatureRegistryError,match="duplicate"): validate_feature_registry(pd.concat([x,x],ignore_index=True))
@pytest.mark.parametrize("field",["pregame_available","historical_available","today_available","leakage_checked"])
def test_approved_requires_safety(field):
    x=valid(); x.loc[0,field]=False
    with pytest.raises(FeatureRegistryError): validate_feature_registry(x)
def test_approved_requires_pass_coverage():
    x=valid(); x.loc[0,"coverage_status"]="PARTIAL"
    with pytest.raises(FeatureRegistryError,match="PASS coverage"): validate_feature_registry(x)
def test_blocked_can_remain_unproven():
    x=valid(); x.loc[0,["research_status","coverage_status","pregame_available","historical_available","leakage_checked"]]=["BLOCKED","UNPROVEN",False,False,False]
    assert validate_feature_registry(x).loc[0,"research_status"]=="BLOCKED"
def test_invalid_status_rejected():
    x=valid(); x.loc[0,"research_status"]="KEEP"
    with pytest.raises(FeatureRegistryError,match="research_status"): validate_feature_registry(x)
