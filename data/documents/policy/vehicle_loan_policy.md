# Vehicle Loan Policy (Synthetic, for capstone use)

Document: vehicle_loan_policy.md | Version 1.0
Note: this is a fictional policy written for a training project. Values marked (assumption) are chosen by the lender, not learned from data.

## 1. Purpose and Scope
This policy sets the rules for approving and sizing vehicle loans for individual applicants. It applies to new four-wheeler purchases financed through the lender.

## 2. Definitions
- **Monthly income**: annual income divided by 12.
- **EMI**: the fixed monthly instalment of a loan.
- **Obligation ratio**: total monthly EMIs (existing plus the new loan) divided by monthly income.
- **Loan-to-value (LTV)**: loan amount divided by the vehicle price.
- **Credit score**: the applicant's CIBIL score, from 300 to 900.

## 3. Eligibility
### 3.1 Basic Requirements
The applicant must declare a positive annual income and provide the details listed in Section 10.

### 3.2 Minimum Credit Score
An applicant must have a credit score of at least 550. Applications below this score are rejected. The cut-off was set at the point where historical approvals change sharply in the lender's loan data.

## 4. Existing Obligations
### 4.1 Obligation Limit (Salaried and General)
Total monthly EMIs, including the new loan, must not exceed 50% of monthly income. (assumption)

### 4.2 Obligation Limit (Self-Employed)
For self-employed applicants, total monthly EMIs, including the new loan, must not exceed 45% of monthly income, because income is less predictable. (assumption) This rule applies only to self-employed applicants.

## 5. Loan Amount
### 5.1 How the Sanctioned Amount Is Set
The sanctioned amount is the lowest of: the requested amount; the amount typical for similar approved applicants (statistical estimate); the amount the applicant can repay under Section 4; the income multiple in Section 5.2; and the maximum in Section 5.3. The result is rounded down to the nearest 10,000.

### 5.2 Income Multiple Cap
The loan amount must not exceed 5.17 times the applicant's annual income. This limit was taken from the 95th percentile of historical approved loans.

### 5.3 Minimum and Maximum Loan
The maximum vehicle loan is 50,00,000 (assumption). The minimum loan is 1,00,000 (assumption). If the amount the applicant qualifies for is below the minimum, no offer is made.

## 6. Tenure
### 6.1 Tenure Range
The tenure must be between 1 and 7 years. If an applicant requests a longer tenure, the loan is sized using 7 years. (assumption)

## 7. Down Payment and Loan-to-Value
### 7.1 Maximum LTV
The loan may not exceed 85% of the vehicle price, so the applicant must pay at least 15% of the price as down payment. (assumption)

## 8. Interest Rate
### 8.1 Rate Used for EMI
EMIs are calculated at 9.5% per year on a reducing balance. (assumption)

## 9. Statistical Risk Assessment and Exceptions
### 9.1 Risk Score
Every application is also scored by a statistical model trained on historical loan data. If the score is below the lender's approval threshold, the application is rejected even when all rules above are met. The policy does not list a separate rule for this outcome; the main factors influencing the score are the credit score, loan term and loan amount.

### 9.2 Exceptions
Exceptions to the rules above are not handled by this system and require manual review by a credit officer.

## 10. Documentation
Applicants must provide proof of identity, proof of address, income proof (salary slips or tax returns for the last two years), and bank statements for the last six months. Self-employed applicants must additionally provide business registration proof.
