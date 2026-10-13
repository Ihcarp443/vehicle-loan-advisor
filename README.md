# Vehicle Loan Advisor

An ML-powered vehicle loan eligibility and advisory application that combines loan approval prediction, estimated loan-amount analysis, and policy-grounded explanations to make the loan assessment process more transparent.


## Overview

Traditional loan assessment can be difficult for applicants to understand. A prediction alone does not explain which financial factors influenced the outcome or what eligibility considerations may matter.

Vehicle Loan Advisor explores an end-to-end approach to this problem by combining machine learning with an application layer that communicates model outcomes and relevant policy information.

The project includes a Jupyter notebook for exploratory data analysis and model development, trained ML artifacts, a backend, a frontend, and supporting policy documents.

## Key Features

- **Loan eligibility prediction:** Classifies an application as approved or rejected using a trained classification pipeline.
- **Loan amount estimation:** Uses a separate regression pipeline to estimate a loan amount for eligible applicants.
- **Data preprocessing:** Handles numerical and categorical features through reusable preprocessing pipelines.
- **Model evaluation:** Explores classification metrics, cross-validation, hyperparameter tuning, and feature importance.
- **Policy-grounded explanations:** Uses policy information to help explain an assessment, with deterministic checks forming the basis of the decision.
- **Application architecture:** Organizes the ML artifacts, backend, frontend, and supporting documents into a single repository.

## Technology Stack

| Component | Technologies |
|---|---|
| Programming language | Python |
| Data analysis | Pandas, NumPy |
| Visualization | Matplotlib, Seaborn |
| Machine learning | Scikit-learn |
| Gradient boosting experiments | XGBoost |
| Model persistence | Joblib |
| Application backend | See `backend/` |
| User interface | See `frontend/` |
| Container configuration | Docker Compose configuration |

## Machine Learning Workflow

### 1. Exploratory Data Analysis

The analysis notebook, [`notebooks/analyse.ipynb`](notebooks/analyse.ipynb), explores the loan approval dataset and examines the data before model development.

The dataset contains 4,269 records and 13 columns, including the loan identifier, applicant attributes, financial information, and loan status.

The analysis covers:

- Dataset dimensions, data types, and missing-value checks.
- Distribution of loan approval outcomes.
- Relationships between financial attributes and loan status.
- Correlation analysis and feature exploration.
- Preparation of numerical and categorical input features.

### 2. Feature Preparation

The classification pipeline separates preprocessing according to feature type.

**Numerical features**
- Missing-value imputation using the median.
- Feature scaling where configured in the preprocessing pipeline.

**Categorical features**
- Missing-value imputation using the most frequent value.
- One-hot encoding with support for previously unseen categories.

The preprocessing and estimator are combined into a Scikit-learn pipeline so that inference uses the same transformations as model training.

### 3. Model Development and Evaluation

The notebook explores multiple classification approaches, including:

- Logistic Regression
- Decision Tree
- Random Forest
- Gradient Boosting
- XGBoost experiments

Model selection should be based on held-out test performance and appropriate validation rather than accuracy alone.

Evaluation considers metrics such as:

- Accuracy
- Precision and recall
- F1-score
- Confusion matrix
- ROC-AUC where applicable
- Cross-validation and out-of-bag performance where applicable

For loan assessment, false approvals and false rejections have different business implications. Precision, recall, and class-specific error analysis therefore provide important context beyond overall accuracy.

### 4. Two-Stage Prediction Architecture

The notebook implements a two-stage Random Forest approach.

**Stage 1 — Eligibility classification**

A trained classification pipeline predicts the loan status.

**Stage 2 — Loan amount estimation**

For applications classified as approved, a separate regression pipeline estimates the loan amount.

Conceptually:

```text
Applicant Information
        |
        v
Feature Preprocessing
        |
        v
Loan Eligibility Classifier
        |
        +---- Rejected
        |       |
        |       v
        |   Return Decision
        |
        +---- Approved
                |
                v
       Loan Amount Regressor
                |
                v
       Return Estimated Amount
```

The regression stage is conditional on the classification outcome. Its estimate should not be interpreted as a guaranteed sanction amount.

### 5. Policy-Grounded Explanations

The application also incorporates policy-grounded explanation logic.

The intended separation of responsibilities is:

- **ML model:** Produces the prediction.
- **Policy and business logic:** Applies defined checks and identifies relevant considerations.
- **Generative AI:** Helps express supported findings in natural language.

The language model should not independently determine eligibility or invent policy rules. If an explanation-generation call fails or the required API configuration is unavailable, a deterministic fallback can help preserve basic explanation functionality.

## Repository Structure

```text
vehicle-loan-advisor/
├── backend/                 # Backend application
├── frontend/                # User interface
├── data/
│   └── documents/           # Supporting policy documents
├── models/                  # Saved ML artifacts
├── notebooks/
│   └── analyse.ipynb        # EDA, model training and evaluation
├── docker-compose.yml       # Container orchestration configuration
├── requirements.txt         # Python dependencies
└── try.py                   # Supporting script
```

## Getting Started

### Prerequisites

- Python 3.10 or a compatible version supported by the project dependencies.
- Git.
- The dataset required by the analysis notebook.
- Any API credentials required by optional AI-powered explanation functionality.

### Create a Virtual Environment


```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure the Dataset

The analysis notebook currently references the dataset at:

```text
../data/raw/loan_approval_dataset.csv
```

### 4. Configure the Application

Review the files in `backend/`, `frontend/`, and `models/` to identify the application entry points, required environment variables, and expected model artifact paths.

Configure any required API credentials through environment variables rather than hardcoding secrets.

To run frontend from inside the frontend folder 
```bash
streamlit run app.py
```                                                 

To run backend from inside backend folder
```bash
uvicorn main:app --reload  
```


## Model Artifacts

The notebook saves separate artifacts for the classification and regression stages:

```text
models/
├── stage_1_eligibility_pipeline.pkl
└── stage_2_loan_amount_pipeline.pkl
```