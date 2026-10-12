from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class Applicant(BaseModel):
    no_of_dependents: int = Field(ge=0, le=10, description="People financially dependent on the applicant")
    education: Literal["Graduate", "Not Graduate"]
    self_employed: Literal["Yes", "No"]
    income_annum: float = Field(gt=0, description="Annual income in INR")
    loan_amount: float = Field(gt=0, description="Requested loan amount in INR")
    loan_term: int = Field(ge=1, le=20, description="Requested tenure in years")
    cibil_score: int = Field(ge=300, le=900, description="Credit score (300-900)")
    residential_assets_value: float = Field(ge=0, description="INR")
    commercial_assets_value: float = Field(ge=0, description="INR")
    luxury_assets_value: float = Field(ge=0, description="INR")
    bank_asset_value: float = Field(ge=0, description="INR")
    existing_emi: float = Field(default=0, ge=0, description="Total monthly EMIs already being paid, INR")

    model_config = {"json_schema_extra": {"example": {
        "no_of_dependents": 1, "education": "Graduate", "self_employed": "No",
        "income_annum": 1800000, "loan_amount": 800000, "loan_term": 5, "cibil_score": 760,
        "residential_assets_value": 2000000, "commercial_assets_value": 0,
        "luxury_assets_value": 300000, "bank_asset_value": 400000, "existing_emi": 0}}}


class ExplainRequest(BaseModel):
    applicant: Applicant
    topic: Literal["decision", "amount"] = Field(
        default="decision", description="'decision' explains approve/reject; 'amount' explains the sanctioned amount")



class Reason(BaseModel):
    rule: str
    section: str = Field(description="Policy section that contains the rule")
    applicant_value: Union[str, int, float]
    policy_threshold: str


class Source(BaseModel):
    document: str
    section: str
    title: str
    text: str


# ---------- responses ----------

class PredictResponse(BaseModel):
    decision: Literal["Approved", "Rejected"]
    probability_approved: float = Field(description="Model confidence that the applicant is approved (0-1)")
    threshold: float = Field(description="Minimum model score needed for approval")
    reasons: List[Reason] = Field(description="Empty when approved")


class LoanAmountResponse(BaseModel):
    offer_made: bool
    sanctioned_amount: int
    tenure_years: int
    interest_rate_pa: float
    emi: float
    ml_estimate: int
    binding_constraint: str = Field(description="The limit that set the final amount")
    binding_section: Optional[str] = None
    limits: Dict[str, int] = Field(description="Every limit that was considered")
    sections_used: List[str]
    trace: List[str] = Field(description="Step-by-step working of how the amount was reached")


class ExplainResponse(BaseModel):
    decision: Literal["Approved", "Rejected"]
    topic: str
    explanation: str
    generated_by: Literal["gemini", "template"]
    gaps: List[str] = Field(description="Reasons the policy could not support")
    sources: List[Source]


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    gemini_configured: bool


# ================= vehicles =================


class VehicleFilters(BaseModel):
    body_types: List[str] = Field(default_factory=list, description="e.g. ['Hatchback', 'SUV']; empty = any")
    fuel_types: List[str] = Field(default_factory=list, description="e.g. ['Petrol', 'Electric']; empty = any")
    transmissions: List[str] = Field(default_factory=list, description="'Manual' and/or 'Automatic'; empty = any")
    min_seats: Optional[int] = Field(default=None, ge=2, le=10)
    min_safety_rating: Optional[int] = Field(default=None, ge=0, le=5)
    colour: Optional[str] = Field(default=None, description="Only vehicles offered in this colour")
    max_on_road_price: Optional[float] = Field(default=None, gt=0)


class VehicleSearchRequest(BaseModel):
    sanctioned_amount: float = Field(gt=0, description="From /loan-amount")
    down_payment: float = Field(default=0, ge=0)
    tenure_years: int = Field(default=5, ge=1, le=7, description="Use the tenure returned by /loan-amount")
    filters: VehicleFilters = Field(default_factory=VehicleFilters)
    sort_by: Literal["emi", "price", "safety"] = "emi"

    model_config = {"json_schema_extra": {"example": {
        "sanctioned_amount": 800000, "down_payment": 150000, "tenure_years": 5,
        "filters": {"body_types": ["Hatchback"]}, "sort_by": "emi"}}}


class AffordableVariant(BaseModel):
    variant_name: str
    transmission: str
    ex_showroom: int
    on_road_price: int
    loan_needed: int
    emi: int


class VehicleSummary(BaseModel):
    vehicle_id: str
    name: str
    body_type: str
    fuel_type: str
    seats: Optional[int] = None
    safety_rating: Optional[int] = None
    mileage: Optional[float] = None
    mileage_unit: Optional[str] = None
    tagline: Optional[str] = None
    colours: List[str]
    total_variants: int
    from_on_road_price: int
    from_emi: int
    affordable_variants: List[AffordableVariant]


class NoMatchHelp(BaseModel):
    message: str
    cheapest_option: Optional[Dict[str, Union[str, int]]] = None
    extra_down_payment_needed: Optional[int] = None
    matches_without_filters: int


class VehicleSearchResponse(BaseModel):
    count: int
    vehicles: List[VehicleSummary]
    affordable_price_limit: int = Field(description="Highest on-road price that fits the amount and the 15% down payment rule")
    sort_by: str
    no_match: Optional[NoMatchHelp] = None
    assumptions: Dict[str, Union[str, int, float]]


class VariantDetail(BaseModel):
    variant_name: str
    transmission: str
    ex_showroom: int
    on_road_price: int
    features: List[str]


class VehicleDetail(BaseModel):
    vehicle_id: str
    name: str
    make: str
    model: str
    body_type: str
    fuel_type: str
    engine_cc: Optional[float] = None
    power_ps: Optional[float] = None
    torque_nm: Optional[float] = None
    mileage: Optional[float] = None
    mileage_unit: Optional[str] = None
    battery_kwh: Optional[float] = None
    ev_range_km: Optional[float] = None
    fuel_tank_l: Optional[float] = None
    seats: Optional[int] = None
    boot_litres: Optional[float] = None
    ground_clearance_mm: Optional[float] = None
    safety_rating: Optional[int] = None
    warranty_years: Optional[float] = None
    warranty_km: Optional[float] = None
    colours: List[str]
    tagline: Optional[str] = None
    source: Optional[str] = None
    description: Optional[str] = None
    variants: List[VariantDetail]


class FilterOptions(BaseModel):
    body_types: List[str]
    fuel_types: List[str]
    transmissions: List[str]
    colours: List[str]
    seats: List[int]
    min_ex_showroom: float
    max_ex_showroom: float


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=300)


class AskSource(BaseModel):
    type: Literal["catalogue", "brochure"]
    reference: str
    text: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    answerable: bool = Field(description="False when the catalogue does not contain the answer")
    generated_by: Literal["gemini", "retrieval_only"]
    sources: List[AskSource]