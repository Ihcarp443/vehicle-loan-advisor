"""Stage 1: approve / reject. Loads the saved classifier once and applies the policy rules on top."""
import json
import os
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from services.features import add_loan_features
from services.policy_check import check_policy

MODELS_DIR = Path(os.getenv("MODELS_DIR", Path(__file__).resolve().parents[2] / "models"))
CLF_FILE = os.getenv("CLF_FILE", "stage_1_eligibility_pipeline.pkl")
REG_FILE = os.getenv("REG_FILE", "stage_2_loan_amount_pipeline.pkl")

RAW_COLUMNS = ["no_of_dependents", "education", "self_employed", "income_annum", "loan_amount",
               "loan_term", "cibil_score", "residential_assets_value", "commercial_assets_value",
               "luxury_assets_value", "bank_asset_value"]


@lru_cache(maxsize=1)
def get_meta():
    path = MODELS_DIR / "model_metadata.json"
    return json.loads(path.read_text()) if path.exists() else {}


@lru_cache(maxsize=1)
def get_classifier():
    return joblib.load(MODELS_DIR / CLF_FILE)


def get_threshold():
    return get_meta().get("classifier", {}).get("threshold", 0.5)


def prepare_row(applicant):
    """One applicant dict -> one-row DataFrame with the same cleaning as training."""
    row = pd.DataFrame([applicant])
    for col in ["education", "self_employed"]:
        row[col] = row[col].astype(str).str.strip()
    return row[RAW_COLUMNS]


def predict(applicant, existing_emi=0.0):
    clf = get_classifier()
    row = prepare_row(applicant)
    features = add_loan_features(row)[list(clf.feature_names_in_)]   # works for 11 or 16 input columns

    prob = float(clf.predict_proba(features)[0, 1])
    threshold = get_threshold()
    model_says_approve = prob >= threshold

    violations = check_policy(applicant, existing_emi)
    reasons = list(violations)
    if not model_says_approve:
        reasons.append({"rule": "model_risk_score", "section": "9.1", "applicant_value": round(prob, 3),
                        "policy_threshold": f"model score >= {threshold}"})

    return {
        "decision": "Approved" if not reasons else "Rejected",
        "probability_approved": round(prob, 4),
        "threshold": threshold,
        "reasons": reasons,          # empty when approved
    }
