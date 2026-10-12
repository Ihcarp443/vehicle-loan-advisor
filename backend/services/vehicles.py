"""Vehicle shortlist (affordability), vehicle details, and questions about one vehicle."""
from db import queries
from rag.embeddings import gemini_available, generate_text
from rag.retriever import get_retriever
from services.loan_amount import emi_for
from services.policy_check import RULES

# the brochures state: road tax about 10% and insurance about 3.5% of the ex-showroom price
ROAD_TAX = 0.10
INSURANCE = 0.035
DONT_KNOW = "I don't have that information in the catalogue."


def on_road_price(ex_showroom):
    return int(round(ex_showroom * (1 + ROAD_TAX + INSURANCE)))


# ---------------------------------------------------------------- shortlist
def _vehicle_ok(v, f):
    if f["body_types"] and v["body_type"].lower() not in [x.lower() for x in f["body_types"]]:
        return False
    if f["fuel_types"] and v["fuel_type"].lower() not in [x.lower() for x in f["fuel_types"]]:
        return False
    if f["min_seats"] and (v["seats"] or 0) < f["min_seats"]:
        return False
    if f["min_safety_rating"] and (v["safety_rating"] or 0) < f["min_safety_rating"]:
        return False
    if f["colour"] and f["colour"].lower() not in [c.lower() for c in v["colours"]]:
        return False
    return True


def _variant_ok(var, f):
    if f["transmissions"] and not any(t.lower() in var["transmission"].lower() for t in f["transmissions"]):
        return False
    if f["max_on_road_price"] and on_road_price(var["ex_showroom"]) > f["max_on_road_price"]:
        return False
    return True


def _evaluate(var, sanctioned, down_payment, tenure, rate, max_ltv):
    price = on_road_price(var["ex_showroom"])
    loan = max(price - down_payment, 0)
    fits = loan <= sanctioned and loan <= max_ltv * price      # policy 7.1 and the sanctioned amount
    return {
        "variant_name": var["variant_name"], "transmission": var["transmission"],
        "ex_showroom": int(var["ex_showroom"]), "on_road_price": price, "loan_needed": int(round(loan)),
        "emi": round(emi_for(loan, rate, tenure)) if loan > 0 else 0, "fits": fits,
    }


def _shortlist(vehicles, variants_by, sanctioned, down_payment, tenure, f, rate, max_ltv):
    result, candidates = [], []
    for v in vehicles:
        if not _vehicle_ok(v, f):
            continue
        evaluated = [_evaluate(var, sanctioned, down_payment, tenure, rate, max_ltv)
                     for var in variants_by.get(v["vehicle_id"], []) if _variant_ok(var, f)]
        candidates += [(v, e) for e in evaluated]
        fitting = sorted([e for e in evaluated if e["fits"]], key=lambda e: e["on_road_price"])
        if fitting:
            result.append({
                "vehicle_id": v["vehicle_id"], "name": f"{v['make']} {v['model']}", "body_type": v["body_type"],
                "fuel_type": v["fuel_type"], "seats": v["seats"], "safety_rating": v["safety_rating"],
                "mileage": v["mileage"], "mileage_unit": v["mileage_unit"], "tagline": v["tagline"],
                "colours": v["colours"], "total_variants": len(variants_by.get(v["vehicle_id"], [])),
                "from_on_road_price": fitting[0]["on_road_price"], "from_emi": fitting[0]["emi"],
                "affordable_variants": [{k: x[k] for k in x if k != "fits"} for x in fitting],
            })
    return result, candidates


def search_vehicles(sanctioned_amount, down_payment, tenure_years, filters, sort_by="emi"):
    rate = RULES["interest_rate"]["annual_rate"]
    max_ltv = RULES["max_ltv"]["threshold"]
    vehicles = queries.all_vehicles()
    variants_by = {}
    for r in queries.get_variants():
        variants_by.setdefault(r["vehicle_id"], []).append(r)

    result, candidates = _shortlist(vehicles, variants_by, sanctioned_amount, down_payment, tenure_years, filters, rate, max_ltv)
    keys = {"emi": lambda x: (x["from_emi"], x["from_on_road_price"]),
            "price": lambda x: x["from_on_road_price"],
            "safety": lambda x: (-(x["safety_rating"] or 0), x["from_emi"])}
    result.sort(key=keys[sort_by])

    # highest on-road price that satisfies both the amount limit and the 15% minimum down payment
    price_limit = min(sanctioned_amount + down_payment, down_payment / (1 - max_ltv) if max_ltv < 1 else float("inf"))

    no_match = None
    if not result:
        no_match = _no_match_help(candidates, vehicles, variants_by, sanctioned_amount, down_payment,
                                  tenure_years, filters, rate, max_ltv)
    return {"count": len(result), "vehicles": result, "affordable_price_limit": int(price_limit),
            "sort_by": sort_by, "no_match": no_match,
            "assumptions": {"price_used": "estimated on-road price (ex-showroom + 10% road tax + 3.5% insurance)",
                            "interest_rate_pa": rate, "tenure_years": tenure_years,
                            "max_loan_to_value": max_ltv}}


def _no_match_help(candidates, vehicles, variants_by, sanctioned, down, tenure, f, rate, max_ltv):
    if not candidates:
        return {"message": "No vehicle matches the selected filters. Try removing some filters.",
                "cheapest_option": None, "extra_down_payment_needed": None, "matches_without_filters": 0}
    v, cheapest = min(candidates, key=lambda c: c[1]["on_road_price"])
    price = cheapest["on_road_price"]
    needed_down = max(price - sanctioned, price * (1 - max_ltv))
    extra = int(round(max(needed_down - down, 0)))
    empty = {"body_types": [], "fuel_types": [], "transmissions": [], "min_seats": None,
             "min_safety_rating": None, "colour": None, "max_on_road_price": None}
    without, _ = _shortlist(vehicles, variants_by, sanctioned, down, tenure, empty, rate, max_ltv)
    return {
        "message": (f"No vehicle fits your budget with these filters. The cheapest option is "
                    f"{v['make']} {v['model']} {cheapest['variant_name']} at about {price:,} on-road; "
                    f"you would need about {extra:,} more as down payment."),
        "cheapest_option": {"vehicle_id": v["vehicle_id"], "name": f"{v['make']} {v['model']}",
                            "variant_name": cheapest["variant_name"], "on_road_price": price},
        "extra_down_payment_needed": extra,
        "matches_without_filters": len(without),
    }


# ---------------------------------------------------------------- details
def get_vehicle_detail(vehicle_id):
    v = queries.get_vehicle(vehicle_id)
    if not v:
        return None
    variants = []
    for r in queries.get_variants(vehicle_id):
        variants.append({"variant_name": r["variant_name"], "transmission": r["transmission"],
                         "ex_showroom": int(r["ex_showroom"]), "on_road_price": on_road_price(r["ex_showroom"]),
                         "features": r["features"]})
    try:
        description = get_retriever().section_text(vehicle_id, "Overview")
    except FileNotFoundError:
        description = None
    return {**v, "name": f"{v['make']} {v['model']}", "description": description, "variants": variants}


# ---------------------------------------------------------------- questions about one vehicle
def _fact_card(detail):
    """The structured facts of this vehicle as plain text, handed to the LLM as 'DATA SHEET'."""
    labels = [("body_type", "Body type"), ("fuel_type", "Fuel"), ("engine_cc", "Engine (cc)"), ("power_ps", "Power (PS)"),
              ("torque_nm", "Torque (Nm)"), ("mileage", "Efficiency"), ("mileage_unit", "Efficiency unit"),
              ("battery_kwh", "Battery (kWh)"), ("ev_range_km", "EV range (km)"), ("fuel_tank_l", "Fuel tank (L)"),
              ("seats", "Seats"), ("boot_litres", "Boot (L)"), ("ground_clearance_mm", "Ground clearance (mm)"),
              ("safety_rating", "Safety rating (out of 5, synthetic)"), ("warranty_years", "Warranty (years)"),
              ("warranty_km", "Warranty (km)"), ("tagline", "Tagline")]
    lines = [f"Vehicle: {detail['name']}"]
    lines += [f"{label}: {detail[k]}" for k, label in labels if detail.get(k) is not None]
    if detail["colours"]:
        lines.append("Colours: " + ", ".join(detail["colours"]))
    for var in detail["variants"]:
        lines.append(f"Variant {var['variant_name']} ({var['transmission']}): ex-showroom {var['ex_showroom']:,}, "
                     f"estimated on-road {var['on_road_price']:,}. Features: {'; '.join(var['features'])}")
    return "\n".join(lines)


def _prompt(question, card, passages):
    text = "\n\n".join(f"[Brochure: {p['section']}]\n{p['text']}" for p in passages) or "(none found)"
    return (
        "You answer buyer questions about ONE vehicle.\n"
        "Use ONLY the DATA SHEET and BROCHURE PASSAGES below. Use no outside knowledge. Never guess or change a number.\n"
        f"If the answer is not stated there, reply exactly: {DONT_KNOW}\n"
        "Answer in 1-4 short sentences and say where it came from, e.g. (data sheet) or (brochure: Safety).\n\n"
        f"DATA SHEET:\n{card}\n\nBROCHURE PASSAGES:\n{text}\n\nQUESTION: {question}\n"
    )


def ask_about_vehicle(vehicle_id, question):
    detail = get_vehicle_detail(vehicle_id)
    if detail is None:
        return None
    passages = get_retriever().search(question, vehicle_id, k=4)
    sources = [{"type": "catalogue", "reference": f"{detail['name']} data sheet", "text": None}]
    sources += [{"type": "brochure", "reference": f"{p['file']} - {p['section']}", "text": p["text"]} for p in passages]

    if gemini_available():
        try:
            answer = generate_text(_prompt(question, _fact_card(detail), passages)).strip()
            return {"answer": answer, "answerable": DONT_KNOW not in answer, "generated_by": "gemini", "sources": sources}
        except Exception:
            pass   # fall through to retrieval-only
    if passages:
        return {"answer": "Closest passage from the brochure: " + passages[0]["text"], "answerable": True,
                "generated_by": "retrieval_only", "sources": sources[1:]}
    return {"answer": DONT_KNOW, "answerable": False, "generated_by": "retrieval_only", "sources": []}