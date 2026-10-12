"""Checks an applicant against the written policy and reports which rules are violated.
Numbers come from policy_rules.json (same numbers as vehicle_loan_policy.md)."""
import json
from pathlib import Path

RULES_PATH = Path(__file__).parent / "policy_rules.json"
POLICY_MD = Path(__file__).resolve().parents[2] / "data" / "documents" / "policy" / "vehicle_loan_policy.md"

CONFIG = json.loads(RULES_PATH.read_text())
RULES = CONFIG["rules"]


def _violation(rule_id, value, threshold_text):
    return {
        "rule": rule_id,
        "section": RULES[rule_id]["section"],
        "applicant_value": value,
        "policy_threshold": threshold_text,
    }


def check_policy(applicant, existing_emi=0.0):
    """Hard rules that can reject an applicant. Returns a list of violations (empty = none)."""
    violations = []

    # 3.2 minimum credit score
    min_score = RULES["minimum_credit_score"]["threshold"]
    if applicant["cibil_score"] < min_score:
        violations.append(_violation("minimum_credit_score", applicant["cibil_score"], f">= {min_score}"))

    # 4.1 / 4.2 obligation limit (self-employed has a stricter limit)
    monthly_income = applicant["income_annum"] / 12
    if applicant.get("self_employed", "No").strip() == "Yes":
        rule_id = "obligation_limit_self_employed"
    else:
        rule_id = "obligation_limit"
    limit = RULES[rule_id]["threshold"]
    ratio = existing_emi / monthly_income
    if ratio > limit:
        violations.append(_violation(rule_id, f"{ratio:.0%}", f"<= {limit:.0%} of monthly income"))

    return violations


def check_ltv(vehicle_price, down_payment):
    """Section 7.1, used in the vehicle step. Returns a violation or None."""
    max_ltv = RULES["max_ltv"]["threshold"]
    ltv = (vehicle_price - down_payment) / vehicle_price
    if ltv > max_ltv:
        return _violation("max_ltv", f"{ltv:.0%}", f"<= {max_ltv:.0%} of vehicle price")
    return None


def verify_policy_text():
    """Test helper: every section ID in the config must exist as a heading in the policy file."""
    text = POLICY_MD.read_text()
    missing = [r["section"] for r in RULES.values() if f"{r['section']} " not in text]
    return missing


if __name__ == "__main__":
    print("Missing sections in policy file:", verify_policy_text())
    a = {"cibil_score": 480, "income_annum": 264000, "self_employed": "Yes"}
    for v in check_policy(a, existing_emi=9000):
        print(v)
    print(check_ltv(1_000_000, 100_000))
