# AutoFin Vehicle Loan Lending Policy
**Document ID:** AF-VL-001  
**Version:** 1.0  
**Status:** Simulated policy for an academic capstone  
**Effective date:** 1 January 2026

## 1. Purpose and Scope

This policy defines the eligibility criteria, repayment capacity assessment, loan sanction limits and documentation requirements for vehicle loans offered by AutoFin.

This is a fictional policy created for demonstration and does not represent any real financial institution.

## 2. Applicant Eligibility

Applicants must satisfy all mandatory criteria below.

| Parameter | Policy requirement |
|---|---|
| Minimum age | 21 years |
| Minimum monthly income | ₹25,000 |
| Minimum credit score | 650 |
| Minimum employment experience | 2 years |
| Maximum FOIR | 50% |
| Maximum loan-to-value (LTV) | 90% |
| Maximum loan tenure | 7 years |
| Annual interest rate | 10% fixed for this simulation |

Failure to meet any mandatory eligibility criterion results in rejection under the standard policy.

## 3. Repayment Capacity Assessment

The Fixed Obligation to Income Ratio (FOIR) measures the proportion of monthly income committed to loan repayments.

**Formula:**

FOIR = (Existing monthly EMIs + Proposed vehicle EMI) / Monthly income × 100

The FOIR must not exceed 50%.

The maximum affordable vehicle EMI is calculated as:

Maximum vehicle EMI = (Monthly income × 0.50) − Existing monthly EMIs

If the calculated amount is zero or negative, the applicant cannot support a new loan under this policy.

## 4. Sanctioned Loan Amount

The sanctioned amount must satisfy all applicable limits:

1. **Repayment capacity:** The loan EMI must not exceed the maximum affordable vehicle EMI.
2. **LTV limit:** The loan must not exceed 90% of the eligible vehicle price.
3. **Requested amount:** The sanction must not exceed the amount requested by the applicant.
4. **Tenure:** The loan tenure must not exceed seven years.
5. **Interest rate:** The illustrative annual interest rate is fixed at 10%.

For a monthly interest rate `r` and tenure of `n` months, the principal supported by an affordable EMI `E` is:

Loan principal = E × [1 − (1 + r)^(-n)] / r

The final sanctioned amount is the minimum of the repayment-capacity limit, the LTV limit and the requested loan amount.

The final EMI must be recalculated using the sanctioned amount and verified against the FOIR limit.

If the applicant does not meet the eligibility criteria, no loan amount is sanctioned.

## 5. Loan Tenure and Down Payment

Applicants may request a tenure of up to 84 months.

The down payment is the applicant's contribution toward the vehicle purchase. The vehicle's eligible price minus the loan amount represents the required customer contribution.

The loan cannot exceed 90% of the eligible vehicle price. Any additional charges must be considered separately unless explicitly included in the eligible vehicle price.

## 6. Exceptions and Policy Overrides

The standard eligibility thresholds are mandatory for this simulated implementation. No discretionary exceptions are enabled.

A missing, invalid or inconsistent applicant field must be flagged for correction rather than silently assumed to satisfy the policy.

The system's final decision must comply with the policy even when the machine-learning model predicts approval.

## 7. Documentation Requirements

The applicant should provide or verify:

- Proof of identity and date of birth.
- Proof of monthly income.
- Employment or business information.
- Credit report or credit score.
- Details of existing loan obligations.
- Vehicle quotation and variant details.
- Down payment availability.

These documents are listed as requirements for the simulation; the capstone does not need to integrate actual document verification.

## 8. Decision and Explanation Requirements

Every decision must record:

- The machine-learning prediction.
- The final policy-compliant decision.
- The applicant values checked against the policy.
- Any failed mandatory conditions.
- The sanctioned amount and calculation breakdown, where applicable.
- The relevant policy section supporting each explanation.

Explanations must identify the applicable threshold and the applicant's actual value. If a policy passage does not support a claimed reason, the system must not invent one.

## 9. Document Limitations

This policy is synthetic and intended for educational use. Its thresholds, interest rate and formulas are illustrative. It is not a substitute for legal, regulatory or credit-risk review by a real lender.