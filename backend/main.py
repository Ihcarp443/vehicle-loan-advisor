import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

load_dotenv()  
from db.setup import ensure_db  
from rag.retriever import get_retriever  
from schemas import (Applicant, AskRequest, AskResponse, ExplainRequest, ExplainResponse,  
                     FilterOptions, HealthResponse, LoanAmountResponse, PredictResponse,
                     VehicleDetail, VehicleSearchRequest, VehicleSearchResponse)
from services import eligibility, loan_amount  
from services import vehicles as vehicle_service  
from db import queries 
from services import explain as explain_service  

state = {"models_loaded": False}


@asynccontextmanager
async def lifespan(app: FastAPI):
    eligibility.get_classifier()      
    loan_amount.get_regressor()
    explain_service.load_chunks()
    ensure_db()                       
    get_retriever()                   
    state["models_loaded"] = True
    yield


app = FastAPI(
    title="Intelligent Vehicle Loan Advisor API",
    description="Eligibility, sanctioned amount and policy-grounded explanations for vehicle loans.",
    version="1.0.0",
    lifespan=lifespan,
)


def _split(applicant: Applicant):
    """Pydantic model -> (applicant dict for the models, existing_emi)."""
    data = applicant.model_dump()
    return data, data.pop("existing_emi")


def _not_eligible(decision):
    return HTTPException(status_code=409, detail={
        "message": "Applicant is not eligible, so no loan amount can be sanctioned.",
        "reasons": decision["reasons"]})


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    return {"status": "ok", "models_loaded": state["models_loaded"],
            "gemini_configured": bool(os.getenv("GEMINI_API_KEY"))}


@app.post("/predict", response_model=PredictResponse, tags=["loan"])
def predict(applicant: Applicant):
    """Approved or Rejected, with the model's confidence and any policy rules that were violated."""
    data, emi = _split(applicant)
    return eligibility.predict(data, emi)


@app.post("/loan-amount", response_model=LoanAmountResponse, tags=["loan"])
def loan_amount_endpoint(applicant: Applicant):
    """Sanctioned amount and terms for an approved applicant. Returns 409 if the applicant is rejected."""
    data, emi = _split(applicant)
    decision = eligibility.predict(data, emi)
    if decision["decision"] != "Approved":
        raise _not_eligible(decision)
    return loan_amount.sanction(data, emi)


@app.post("/explain", response_model=ExplainResponse, tags=["loan"])
def explain_endpoint(request: ExplainRequest):
    """Plain-language explanation of the decision or the sanctioned amount, with policy sources.
    The decision is recomputed on the server, never taken from the client."""
    data, emi = _split(request.applicant)
    decision = eligibility.predict(data, emi)
    sanction = None
    if request.topic == "amount":
        if decision["decision"] != "Approved":
            raise _not_eligible(decision)
        sanction = loan_amount.sanction(data, emi)
    result = explain_service.explain(decision, sanction, kind=request.topic)
    return {**result, "decision": decision["decision"], "topic": request.topic}


# ---------------------------------------------------------------- vehicles
@app.post("/vehicles", response_model=VehicleSearchResponse, tags=["vehicles"])
def vehicles(request: VehicleSearchRequest):
    """Vehicles the applicant can afford, with filters and sorting. If nothing fits, `no_match` explains what could change."""
    return vehicle_service.search_vehicles(request.sanctioned_amount, request.down_payment, request.tenure_years,
                                           request.filters.model_dump(), request.sort_by)


@app.get("/vehicles/filters", response_model=FilterOptions, tags=["vehicles"])
def vehicle_filters():
    """Values to show in the filter widgets (body types, fuels, colours, ...)."""
    return queries.filter_options()


@app.get("/vehicles/{vehicle_id}", response_model=VehicleDetail, tags=["vehicles"])
def vehicle_detail(vehicle_id: str):
    """Full details of one vehicle: specifications, colours, variants with prices and features."""
    detail = vehicle_service.get_vehicle_detail(vehicle_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
    return detail


@app.post("/vehicles/{vehicle_id}/ask", response_model=AskResponse, tags=["vehicles"])
def ask_vehicle(vehicle_id: str, request: AskRequest):
    """Answer a question about ONE vehicle from its data sheet and brochure. Says so when the catalogue has no answer."""
    result = vehicle_service.ask_about_vehicle(vehicle_id, request.question)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
    return result