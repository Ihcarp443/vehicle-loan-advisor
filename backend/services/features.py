import numpy as np

ASSET_COLS = ["residential_assets_value", "commercial_assets_value",
              "luxury_assets_value", "bank_asset_value"]


def add_basic_features(df):
    """Features that do not use loan_amount (safe for the loan amount model)."""
    df = df.copy()
    df["total_assets"] = df[ASSET_COLS].sum(axis=1)
    df["income_per_dependent"] = df["income_annum"] / (df["no_of_dependents"] + 1)
    return df


def add_loan_features(df):
    """Features for the eligibility model (uses the requested loan_amount)."""
    df = add_basic_features(df)
    income = df["income_annum"].clip(lower=1)
    loan = df["loan_amount"].clip(lower=1)
    term = df["loan_term"].clip(lower=1)
    df["loan_to_income"] = df["loan_amount"] / income
    df["assets_to_loan"] = df["total_assets"] / loan
    # interest-free yearly repayment as a share of income (a rough burden indicator)
    df["annual_repayment_to_income"] = (df["loan_amount"] / term) / income
    return df
