import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="Vehicle Loan Advisor", page_icon="🚗", layout="wide")

RULE_LABELS = {
    "minimum_credit_score": "Minimum credit score",
    "obligation_limit": "Existing EMIs vs income",
    "obligation_limit_self_employed": "Existing EMIs vs income (self-employed)",
    "model_risk_score": "Statistical risk assessment",
    "sanctionable_amount_below_minimum": "Amount below the minimum loan",
}
LIMIT_LABELS = {
    "requested_amount": "the amount you requested",
    "ml_estimate": "the amount typical for similar approved applicants",
    "repayment_capacity": "what you can repay within the EMI limit",
    "income_multiple_cap": "the maximum multiple of annual income",
    "policy_maximum": "the maximum vehicle loan",
}


# ---------------------------------------------------------------- helpers
def inr(x):
    """Indian digit grouping, e.g. 1234567 -> ₹12,34,567"""
    s = str(int(round(x)))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    return "₹" + s


def api(method, path, payload=None):
    """Returns (data, error_message). Never raises."""
    try:
        r = requests.request(method, BACKEND_URL + path, json=payload, timeout=90)
    except requests.exceptions.RequestException:
        return None, f"Cannot reach the backend at {BACKEND_URL}. Is it running?"
    if r.ok:
        return r.json(), None
    try:
        detail = r.json().get("detail")
    except ValueError:
        detail = r.text
    if isinstance(detail, list):                      # validation errors from FastAPI
        detail = "; ".join(f"{'.'.join(str(p) for p in e['loc'][1:])}: {e['msg']}" for e in detail)
    elif isinstance(detail, dict):
        detail = detail.get("message", str(detail))
    return None, f"{r.status_code}: {detail}"


@st.cache_data(ttl=20)
def backend_health():
    return api("GET", "/health")


@st.cache_data(ttl=300)
def filter_options():
    return api("GET", "/vehicles/filters")


def go(page):
    st.session_state.page = page
    st.rerun()


def init_state():
    defaults = {"page": "form", "applicant": None, "down_payment": 0, "decision": None, "sanction": None,
                "explain_decision": None, "explain_amount": None, "shortlist": None, "vehicle_id": None, "qa": {}}
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def show_explanation(exp):
    if not exp:
        return
    st.markdown(exp["explanation"])
    if exp["generated_by"] == "template":
        st.caption("Standard wording (the AI writer was not used for this answer).")
    for gap in exp.get("gaps", []):
        st.warning(gap)
    if exp["sources"]:
        with st.expander("Policy sources"):
            for s in exp["sources"]:
                st.markdown(f"**{s['document']}, Section {s['section']}: {s['title']}**")
                st.caption(s["text"])


# ---------------------------------------------------------------- sidebar
def sidebar():
    st.sidebar.title("🚗 Vehicle Loan Advisor")
    health, err = backend_health()
    if err:
        st.sidebar.error(err)
    else:
        st.sidebar.success("Backend connected" + ("" if health["gemini_configured"] else " (AI writer off)"))

    st.sidebar.markdown("**Steps**")
    approved = bool(st.session_state.decision and st.session_state.decision["decision"] == "Approved"
                    and st.session_state.sanction and st.session_state.sanction["offer_made"])
    steps = [("form", "1. Applicant details", True),
             ("decision", "2. Decision and amount", st.session_state.decision is not None),
             ("shortlist", "3. Vehicles", approved),
             ("detail", "4. Vehicle details", approved and st.session_state.vehicle_id is not None)]
    for key, label, enabled in steps:
        marker = "▶ " if st.session_state.page == key else ""
        if st.sidebar.button(marker + label, key=f"nav_{key}", disabled=not enabled):
            go(key)
    if st.sidebar.button("Start over"):
        for k in ["applicant", "decision", "sanction", "explain_decision", "explain_amount", "shortlist", "vehicle_id"]:
            st.session_state[k] = None
        st.session_state.qa = {}
        go("form")


# ---------------------------------------------------------------- page 1: form
def page_form():
    st.header("Applicant details")
    st.caption("Fill in the details below. Nothing is saved on the server.")
    a = st.session_state.applicant or {}
    monthly_default = (a.get("income_annum", 1_800_000) / 12) if a else 150_000.0

    with st.form("applicant_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("Personal")
            education = st.selectbox("Education", ["Graduate", "Not Graduate"],
                                     index=["Graduate", "Not Graduate"].index(a.get("education", "Graduate")))
            self_employed = st.selectbox("Self-employed", ["No", "Yes"],
                                         index=["No", "Yes"].index(a.get("self_employed", "No")))
            dependents = st.number_input("Number of dependents", 0, 10, int(a.get("no_of_dependents", 1)))
            cibil = st.number_input("Credit score (300-900)", 300, 900, int(a.get("cibil_score", 750)))
        with c2:
            st.subheader("Income and obligations")
            monthly_income = st.number_input("Monthly income (₹)", min_value=1000.0, value=float(monthly_default),
                                             step=5000.0, help="Converted to annual income (x 12) for the model")
            existing_emi = st.number_input("Existing EMIs per month (₹)", min_value=0.0,
                                           value=float(a.get("existing_emi", 0)), step=1000.0)
            down_payment = st.number_input("Down payment available (₹)", min_value=0.0,
                                           value=float(st.session_state.down_payment or 200_000), step=10000.0)
        with c3:
            st.subheader("Loan request")
            loan_amount = st.number_input("Loan amount requested (₹)", min_value=10000.0,
                                          value=float(a.get("loan_amount", 800_000)), step=50000.0)
            loan_term = st.slider("Tenure (years)", 1, 20, int(a.get("loan_term", 5)),
                                  help="The policy allows 1-7 years; a longer request is sized at 7 years.")

        with st.expander("Assets and savings (₹)", expanded=False):
            d1, d2, d3, d4 = st.columns(4)
            residential = d1.number_input("Residential", 0.0, value=float(a.get("residential_assets_value", 0)), step=100000.0)
            commercial = d2.number_input("Commercial", 0.0, value=float(a.get("commercial_assets_value", 0)), step=100000.0)
            luxury = d3.number_input("Luxury", 0.0, value=float(a.get("luxury_assets_value", 0)), step=50000.0)
            bank = d4.number_input("Bank balance", 0.0, value=float(a.get("bank_asset_value", 0)), step=10000.0)

        submitted = st.form_submit_button("Check eligibility", type="primary")

    if submitted:
        payload = {"no_of_dependents": int(dependents), "education": education, "self_employed": self_employed,
                   "income_annum": monthly_income * 12, "loan_amount": loan_amount, "loan_term": int(loan_term),
                   "cibil_score": int(cibil), "residential_assets_value": residential,
                   "commercial_assets_value": commercial, "luxury_assets_value": luxury,
                   "bank_asset_value": bank, "existing_emi": existing_emi}
        run_assessment(payload, down_payment)


def run_assessment(payload, down_payment):
    with st.spinner("Assessing the application..."):
        decision, err = api("POST", "/predict", payload)
        if err:
            st.error(err)
            return
        sanction = exp_amount = None
        if decision["decision"] == "Approved":
            sanction, err = api("POST", "/loan-amount", payload)
            if err:
                st.error(err)
                return
            if sanction["offer_made"]:
                exp_amount, _ = api("POST", "/explain", {"applicant": payload, "topic": "amount"})
        exp_decision, _ = api("POST", "/explain", {"applicant": payload, "topic": "decision"})

    st.session_state.update({"applicant": payload, "down_payment": down_payment, "decision": decision,
                             "sanction": sanction, "explain_decision": exp_decision, "explain_amount": exp_amount,
                             "shortlist": None, "vehicle_id": None})
    go("decision")


# ---------------------------------------------------------------- page 2: decision
def page_decision():
    d, s = st.session_state.decision, st.session_state.sanction
    st.header("Decision")

    if d["decision"] == "Rejected":
        st.error("## Rejected")
        st.markdown("**Reasons**")
        for r in d["reasons"]:
            st.markdown(f"- **{RULE_LABELS.get(r['rule'], r['rule'])}**: your value is `{r['applicant_value']}`; "
                        f"the policy requires `{r['policy_threshold']}` (Section {r['section']})")
        st.subheader("Explanation")
        show_explanation(st.session_state.explain_decision)
        st.info("You can change the details (for example a smaller loan or a larger down payment) and check again.")
        if st.button("Edit details", type="primary"):
            go("form")
        return

    if not s["offer_made"]:
        st.warning("## Approved in principle, but no loan can be offered")
        st.write("The amount you qualify for is below the minimum loan the lender offers.")
        with st.expander("How was this calculated?"):
            for i, line in enumerate(s["trace"], 1):
                st.write(f"{i}. {line}")
        if st.button("Edit details", type="primary"):
            go("form")
        return

    st.success("## Approved")
    requested = st.session_state.applicant["loan_amount"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sanctioned amount", inr(s["sanctioned_amount"]),
              delta=None if s["sanctioned_amount"] >= requested else f"{inr(requested - s['sanctioned_amount'])} below request",
              delta_color="off")
    c2.metric("Monthly EMI", inr(s["emi"]))
    c3.metric("Tenure", f"{s['tenure_years']} years")
    c4.metric("Interest rate", f"{s['interest_rate_pa'] * 100:.1f}% p.a.")

    if s["sanctioned_amount"] < requested:
        st.info(f"The amount is lower than requested because it was limited by "
                f"{LIMIT_LABELS.get(s['binding_constraint'], s['binding_constraint'])}.")

    st.subheader("Why this amount")
    show_explanation(st.session_state.explain_amount)
    with st.expander("How was the amount calculated? (step by step)"):
        for i, line in enumerate(s["trace"], 1):
            st.write(f"{i}. {line}")
        st.table({"Limit": [LIMIT_LABELS.get(k, k).capitalize() for k in s["limits"]],
                  "Amount": [inr(v) for v in s["limits"].values()]})
    with st.expander("Why was the application approved?"):
        show_explanation(st.session_state.explain_decision)
        st.caption(f"Model confidence: {d['probability_approved']:.0%} (approval needs at least {d['threshold']:.0%}).")

    b1, b2 = st.columns([1, 5])
    if b1.button("Edit details"):
        go("form")
    if b2.button("See vehicles you can afford →", type="primary"):
        go("shortlist")


# ---------------------------------------------------------------- page 3: shortlist
def page_shortlist():
    s = st.session_state.sanction
    st.header("Vehicles you can afford")
    opts, err = filter_options()
    if err:
        st.error(err)
        return

    with st.expander("Filters", expanded=True):
        f1, f2, f3, f4 = st.columns(4)
        body = f1.multiselect("Body type", opts["body_types"])
        fuel = f2.multiselect("Fuel", opts["fuel_types"])
        trans = f3.multiselect("Transmission", opts["transmissions"])
        colour = f4.selectbox("Colour", ["Any"] + opts["colours"])
        g1, g2, g3, g4 = st.columns(4)
        seats = g1.selectbox("Minimum seats", ["Any"] + [x for x in opts["seats"]])
        safety = g2.selectbox("Minimum safety rating", ["Any", 3, 4, 5])
        max_price = g3.number_input("Max on-road price (₹, 0 = no limit)", 0.0, step=50000.0)
        sort_label = g4.radio("Sort by", ["Lowest EMI", "Lowest price", "Safest"], horizontal=True)

    payload = {
        "sanctioned_amount": s["sanctioned_amount"], "down_payment": st.session_state.down_payment,
        "tenure_years": s["tenure_years"],
        "filters": {"body_types": body, "fuel_types": fuel, "transmissions": trans,
                    "min_seats": None if seats == "Any" else int(seats),
                    "min_safety_rating": None if safety == "Any" else int(safety),
                    "colour": None if colour == "Any" else colour,
                    "max_on_road_price": max_price or None},
        "sort_by": {"Lowest EMI": "emi", "Lowest price": "price", "Safest": "safety"}[sort_label],
    }
    result, err = api("POST", "/vehicles", payload)
    if err:
        st.error(err)
        return
    st.session_state.shortlist = result

    m1, m2, m3 = st.columns(3)
    m1.metric("Sanctioned loan", inr(s["sanctioned_amount"]))
    m2.metric("Down payment", inr(st.session_state.down_payment))
    m3.metric("Affordable on-road price up to", inr(result["affordable_price_limit"]))
    a = result["assumptions"]
    st.caption(f"Prices are estimated on-road prices (ex-showroom + road tax + insurance). EMI at {a['interest_rate_pa'] * 100:.1f}% "
               f"over {a['tenure_years']} years. A vehicle qualifies if the loan fits the sanctioned amount and the down "
               f"payment is at least {(1 - a['max_loan_to_value']) * 100:.0f}% of its price.")

    if result["count"] == 0:
        nm = result["no_match"]
        st.warning(nm["message"])
        if nm["matches_without_filters"]:
            st.info(f"{nm['matches_without_filters']} vehicle(s) would fit your budget if you removed the filters.")
        return

    st.subheader(f"{result['count']} vehicle(s) match")
    for v in result["vehicles"]:
        with st.container(border=True):
            left, right = st.columns([3, 2])
            with left:
                st.markdown(f"### {v['name']}")
                if v["tagline"]:
                    st.caption(v["tagline"])
                stars = f" • Safety {v['safety_rating']}/5" if v["safety_rating"] else ""
                eff = f" • {v['mileage']} {v['mileage_unit']}" if v["mileage"] else ""
                st.write(f"{v['body_type']} • {v['fuel_type']} • {v['seats']} seats{eff}{stars}")
                st.caption("Colours: " + ", ".join(v["colours"]))
            with right:
                st.metric("From (on-road)", inr(v["from_on_road_price"]))
                st.write(f"EMI from **{inr(v['from_emi'])}** per month")
                if st.button("View details", key=f"view_{v['vehicle_id']}"):
                    st.session_state.vehicle_id = v["vehicle_id"]
                    go("detail")
            st.caption(f"{len(v['affordable_variants'])} of {v['total_variants']} variants within your budget")
            st.dataframe(
                [{"Variant": x["variant_name"], "Transmission": x["transmission"], "On-road price": inr(x["on_road_price"]),
                  "Loan needed": inr(x["loan_needed"]), "EMI / month": inr(x["emi"])} for x in v["affordable_variants"]],
                hide_index=True)


# ---------------------------------------------------------------- page 4: detail
def page_detail():
    vid = st.session_state.vehicle_id
    if st.button("← Back to the list"):
        go("shortlist")
    v, err = api("GET", f"/vehicles/{vid}")
    if err:
        st.error(err)
        return

    st.header(v["name"])
    if v["tagline"]:
        st.caption(v["tagline"])
    if v.get("source") and v["source"].upper() == "SYNTHETIC":
        st.caption("Demo data: this vehicle is fictional.")
    if v["description"]:
        st.write(v["description"])

    st.subheader("Specifications")
    efficiency = f"{v['mileage']} {v['mileage_unit']}" if v["mileage"] else None
    warranty = None
    if v["warranty_years"]:
        warranty = f"{v['warranty_years']:g} years" + (f" / {int(v['warranty_km']):,} km" if v["warranty_km"] else "")
    specs = [("Body type", v["body_type"]), ("Fuel", v["fuel_type"]),
             ("Engine", f"{v['engine_cc']:g} cc" if v["engine_cc"] else None),
             ("Power", f"{v['power_ps']:g} PS" if v["power_ps"] else None),
             ("Torque", f"{v['torque_nm']:g} Nm" if v["torque_nm"] else None),
             ("Efficiency (claimed)", efficiency),
             ("Battery", f"{v['battery_kwh']:g} kWh" if v["battery_kwh"] else None),
             ("Range", f"{v['ev_range_km']:g} km" if v["ev_range_km"] else None),
             ("Fuel tank", f"{v['fuel_tank_l']:g} L" if v["fuel_tank_l"] else None),
             ("Seats", v["seats"]), ("Boot space", f"{v['boot_litres']:g} L" if v["boot_litres"] else None),
             ("Ground clearance", f"{v['ground_clearance_mm']:g} mm" if v["ground_clearance_mm"] else None),
             ("Safety rating", f"{v['safety_rating']}/5" if v["safety_rating"] else None),
             ("Warranty", warranty), ("Colours", ", ".join(v["colours"]) if v["colours"] else None)]
    specs = [(k, val) for k, val in specs if val not in (None, "")]
    half = (len(specs) + 1) // 2
    col1, col2 = st.columns(2)
    for col, chunk in ((col1, specs[:half]), (col2, specs[half:])):
        with col:
            for k, val in chunk:
                st.markdown(f"**{k}:** {val}")

    st.subheader("Variants")
    emi_lookup = {}
    sl = st.session_state.shortlist
    if sl:
        for sv in sl["vehicles"]:
            if sv["vehicle_id"] == vid:
                emi_lookup = {x["variant_name"]: x for x in sv["affordable_variants"]}
    tabs = st.tabs([f"{x['variant_name']} ({x['transmission']})" for x in v["variants"]])
    for tab, var in zip(tabs, v["variants"]):
        with tab:
            c1, c2, c3 = st.columns(3)
            c1.metric("Ex-showroom", inr(var["ex_showroom"]))
            c2.metric("Estimated on-road", inr(var["on_road_price"]))
            hit = emi_lookup.get(var["variant_name"])
            c3.metric("Your EMI", inr(hit["emi"]) if hit else "Outside budget")
            st.markdown("**Features**")
            fc = st.columns(2)
            for i, feat in enumerate(var["features"]):
                fc[i % 2].markdown(f"- {feat}")

    st.subheader("Ask about this vehicle")
    st.caption("Answers come from this vehicle's data sheet and brochure only. If it is not there, you will be told.")
    history = st.session_state.qa.setdefault(vid, [])
    for item in history:
        with st.chat_message("user"):
            st.write(item["q"])
        with st.chat_message("assistant"):
            if item["a"]["answerable"]:
                st.write(item["a"]["answer"])
            else:
                st.warning(item["a"]["answer"])
            if item["a"]["generated_by"] == "retrieval_only":
                st.caption("Showing the closest brochure text (the AI writer was not used).")
            brochure = [x for x in item["a"]["sources"] if x["type"] == "brochure"]
            if brochure:
                with st.expander("Sources"):
                    for x in brochure:
                        st.markdown(f"**{x['reference']}**")
                        st.caption(x["text"])
    with st.form("ask_form", clear_on_submit=True):
        q = st.text_input("Your question", placeholder="e.g. Is it comfortable on rough roads?")
        if st.form_submit_button("Ask") and q.strip():
            with st.spinner("Looking it up..."):
                ans, err = api("POST", f"/vehicles/{vid}/ask", {"question": q.strip()})
            if err:
                st.error(err)
            else:
                history.append({"q": q.strip(), "a": ans})
                st.rerun()


# ---------------------------------------------------------------- main
init_state()
sidebar()
page = st.session_state.page
if page == "form":
    page_form()
elif page == "decision":
    page_decision()
elif page == "shortlist":
    page_shortlist()
else:
    page_detail()