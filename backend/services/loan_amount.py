"""Stage 2: sanctioned amount = lowest of the ML estimate and the policy limits."""
import os
from functools import lru_cache

import joblib

from services.eligibility import MODELS_DIR, REG_FILE, prepare_row
from services.features import add_basic_features
from services.policy_check import RULES

ROUND_TO = 10_000   # sanctioned amount is rounded down (policy 5.1)


@lru_cache(maxsize=1)
def get_regressor():
    return joblib.load(MODELS_DIR / REG_FILE)


def emi_for(principal, annual_rate, years):
    r = annual_rate / 12
    n = int(round(years * 12))
    return principal * r * (1 + r) ** n / ((1 + r) ** n - 1)


def loan_for_emi(emi, annual_rate, years):
    """Largest loan whose EMI is <= emi."""
    r = annual_rate / 12
    n = int(round(years * 12))
    return emi * ((1 + r) ** n - 1) / (r * (1 + r) ** n)


def ml_estimate(applicant):
    reg = get_regressor()
    row = add_basic_features(prepare_row(applicant).drop(columns=["loan_amount"]))
    if "loan_status" in reg.feature_names_in_:        # older pickle expects this constant column
        row["loan_status"] = "Approved"
    return float(reg.predict(row[list(reg.feature_names_in_)])[0])


def sanction(applicant, existing_emi=0.0):
    trace, sections = [], []
    rate = RULES["interest_rate"]["annual_rate"]

    # tenure (6.1)
    asked = int(applicant["loan_term"])
    lo, hi = RULES["tenure_range"]["min_years"], RULES["tenure_range"]["max_years"]
    tenure = min(max(asked, lo), hi)
    if tenure != asked:
        trace.append(f"Requested tenure of {asked} years is outside the allowed {lo}-{hi} years; {tenure} years used.")
        sections.append("6.1")

    # repayment capacity (4.1 / 4.2)
    obligation_rule = "obligation_limit_self_employed" if str(applicant["self_employed"]).strip() == "Yes" else "obligation_limit"
    foir = RULES[obligation_rule]["threshold"]
    obligation_section = RULES[obligation_rule]["section"]
    monthly_income = applicant["income_annum"] / 12
    room = max(foir * monthly_income - existing_emi, 0)
    capacity = loan_for_emi(room, rate, tenure)
    trace.append(f"Monthly income {monthly_income:,.0f}; EMIs may be up to {foir:.0%} = {foir * monthly_income:,.0f}; "
                 f"existing EMIs {existing_emi:,.0f}; room for new EMI {room:,.0f} -> affordable loan {capacity:,.0f}.")

    # all limits, each tied to a policy section
    limits = {
        "requested_amount": (float(applicant["loan_amount"]), None),
        "ml_estimate": (ml_estimate(applicant), "5.1"),
        "repayment_capacity": (capacity, obligation_section),
        "income_multiple_cap": (RULES["income_multiple_cap"]["threshold"] * applicant["income_annum"], RULES["income_multiple_cap"]["section"]),
        "policy_maximum": (float(RULES["loan_amount_limits"]["max"]), RULES["loan_amount_limits"]["section"]),
    }
    for name, (value, _) in limits.items():
        trace.append(f"Limit {name}: {value:,.0f}")

    binding = min(limits, key=lambda k: limits[k][0])
    binding_section = limits[binding][1]
    amount = int(limits[binding][0] // ROUND_TO * ROUND_TO)
    trace.append(f"Lowest limit is {binding}; sanctioned {amount:,} after rounding down to {ROUND_TO:,}.")
    if binding_section:
        sections.append(binding_section)

    result = {
        "sanctioned_amount": amount, "tenure_years": tenure, "interest_rate_pa": rate,
        "emi": 0.0, "ml_estimate": round(limits["ml_estimate"][0]),
        "binding_constraint": binding, "binding_section": binding_section,
        "limits": {k: round(v[0]) for k, v in limits.items()},
        "sections_used": sorted(set(sections)), "trace": trace, "offer_made": True,
    }

    min_loan = RULES["loan_amount_limits"]["min"]
    if amount < min_loan:
        result.update({"sanctioned_amount": 0, "offer_made": False})
        result["trace"].append(f"Amount is below the minimum loan of {min_loan:,}; no offer can be made.")
        result["sections_used"] = sorted(set(sections + [RULES["loan_amount_limits"]["section"]]))
    else:
        result["emi"] = round(emi_for(amount, rate, tenure))
        result["trace"].append(f"EMI on the sanctioned amount: {result['emi']:,}.")
    return result
