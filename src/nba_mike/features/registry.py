"""P0-S4 feature-registry validation."""
from __future__ import annotations
import pandas as pd

class FeatureRegistryError(ValueError):
    """Raised when the feature registry violates governance."""

REQUIRED_COLUMNS = (
    "feature_name","feature_group","description","source_domain",
    "pregame_available","historical_available","today_available",
    "missing_value_policy","leakage_checked","coverage_status",
    "research_status","feature_version","notes",
)
VALID_STATUS={"APPROVED_BASELINE","RESEARCH_ONLY","BLOCKED","REJECTED"}
VALID_COVERAGE={"PASS","PARTIAL","UNPROVEN","FAIL"}

def validate_feature_registry(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df,pd.DataFrame):
        raise FeatureRegistryError("registry must be a pandas DataFrame")
    missing=[c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise FeatureRegistryError(f"missing required columns: {missing}")
    out=df.loc[:,REQUIRED_COLUMNS].copy()
    if out["feature_name"].isna().any() or (out["feature_name"].astype(str).str.strip()=="").any():
        raise FeatureRegistryError("feature_name cannot be blank")
    if out["feature_name"].duplicated().any():
        raise FeatureRegistryError("duplicate feature_name")
    if not set(out["research_status"]).issubset(VALID_STATUS):
        raise FeatureRegistryError("invalid research_status")
    if not set(out["coverage_status"]).issubset(VALID_COVERAGE):
        raise FeatureRegistryError("invalid coverage_status")

    bool_cols=["pregame_available","historical_available","today_available","leakage_checked"]
    for c in bool_cols:
        if not out[c].map(lambda x:isinstance(x,bool)).all():
            raise FeatureRegistryError(f"{c} must contain booleans")

    approved=out["research_status"].eq("APPROVED_BASELINE")
    if (approved & ~out["pregame_available"]).any():
        raise FeatureRegistryError("approved baseline must be pregame available")
    if (approved & ~out["historical_available"]).any():
        raise FeatureRegistryError("approved baseline must be historically available")
    if (approved & ~out["today_available"]).any():
        raise FeatureRegistryError("approved baseline must preserve training/today parity")
    if (approved & ~out["leakage_checked"]).any():
        raise FeatureRegistryError("approved baseline must be leakage checked")
    if (approved & ~out["coverage_status"].eq("PASS")).any():
        raise FeatureRegistryError("approved baseline must have PASS coverage")
    return out.sort_values(["feature_group","feature_name"],kind="stable").reset_index(drop=True)
