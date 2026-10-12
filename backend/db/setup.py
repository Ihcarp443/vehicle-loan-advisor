import csv
import json
import os
import sqlite3
from pathlib import Path

from rag.config import BROCHURE_DIR, ROOT

RAW_DIR = Path(os.getenv("RAW_DIR", ROOT / "data" / "raw"))
DB_PATH = Path(os.getenv("VEHICLE_DB", ROOT / "data" / "processed" / "vehicle_catalogue.db"))

VEHICLE_COLS = ["vehicle_id", "make", "model", "body_type", "fuel_type", "engine_cc", "power_ps", "torque_nm",
                "mileage", "mileage_unit", "battery_kwh", "ev_range_km", "fuel_tank_l", "seats", "boot_litres",
                "ground_clearance_mm", "safety_rating", "warranty_years", "warranty_km", "colours", "tagline", "source"]


def _as_list(value):
    """Accept a JSON list or a 'a|b|c' string."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [x.strip() for x in str(value).split("|") if x.strip()]


def _clean(value):
    if value == "" or (isinstance(value, float) and value != value):
        return None
    return value


def _load_table(stem, issues):
    csv_path, json_path = RAW_DIR / f"{stem}.csv", RAW_DIR / f"{stem}.json"
    if csv_path.exists():
        rows = []
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            reader.fieldnames = [h.strip() for h in reader.fieldnames]
            first_col = reader.fieldnames[0]
            for n, row in enumerate(reader, start=2):
                if row.get(None):                                  
                    issues.append(f"{csv_path.name} line {n}: too many columns, row skipped")
                elif row.get(first_col, "").strip() == first_col:   
                    issues.append(f"{csv_path.name} line {n}: repeated header row skipped")
                else:
                    rows.append({k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()})
        return rows
    if json_path.exists():
        data = json.loads(json_path.read_text(encoding="utf-8"))
        return next(v for v in data.values() if isinstance(v, list)) if isinstance(data, dict) else data
    raise FileNotFoundError(f"Neither {csv_path} nor {json_path} exists. Put the file there, or set RAW_DIR.")


def build_db():
    issues = []
    vehicles = _load_table("vehicles", issues)
    variants = _load_table("variants", issues)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.unlink(missing_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE vehicles (vehicle_id TEXT PRIMARY KEY, make TEXT, model TEXT, body_type TEXT,
        fuel_type TEXT, engine_cc REAL, power_ps REAL, torque_nm REAL, mileage REAL, mileage_unit TEXT,
        battery_kwh REAL, ev_range_km REAL, fuel_tank_l REAL, seats INTEGER, boot_litres REAL,
        ground_clearance_mm REAL, safety_rating INTEGER, warranty_years REAL, warranty_km REAL,
        colours TEXT, tagline TEXT, source TEXT)""")
    conn.execute("""CREATE TABLE variants (variant_id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id TEXT REFERENCES vehicles(vehicle_id), variant_name TEXT, transmission TEXT,
        ex_showroom REAL, features TEXT)""")

    ids = set()
    for v in vehicles:
        v = dict(v)
        v["vehicle_id"] = v.get("vehicle_id") or v.get("id")
        v["colours"] = json.dumps(_as_list(v.get("colours")))
        try:
            conn.execute(f"INSERT INTO vehicles VALUES ({','.join('?' * len(VEHICLE_COLS))})",
                         [_clean(v.get(c)) for c in VEHICLE_COLS])
            ids.add(v["vehicle_id"])
        except sqlite3.IntegrityError:
            issues.append(f"duplicate or missing vehicle id: {v.get('vehicle_id')}")

    n_variants, with_variants = 0, set()
    for r in variants:
        vid = r.get("vehicle_id") or r.get("id")
        price = r.get("ex_showroom") or r.get("ex_showroom_price")
        try:
            price = float(price)
        except (TypeError, ValueError):
            price = None
        if vid not in ids or price is None:
            issues.append(f"variant skipped (unknown vehicle or bad price): {r.get('variant_name')} / {vid}")
            continue
        conn.execute("INSERT INTO variants (vehicle_id, variant_name, transmission, ex_showroom, features) VALUES (?,?,?,?,?)",
                     (vid, r.get("variant_name"), r.get("transmission"), price,
                      json.dumps(_as_list(r.get("features")))))
        n_variants += 1
        with_variants.add(vid)

    for vid in sorted(ids - with_variants):
        issues.append(f"vehicle {vid} has no variants")
    for vid in sorted(ids):
        if not list(BROCHURE_DIR.glob(f"{vid}*.md")):
            issues.append(f"vehicle {vid} has no brochure file")

    conn.commit()
    conn.close()
    print(f"{len(ids)} vehicles, {n_variants} variants loaded into {DB_PATH}")
    for i in issues:
        print("WARNING:", i)
    return {"vehicles": len(ids), "variants": n_variants, "issues": issues}


def ensure_db():
    if not DB_PATH.exists():
        build_db()


if __name__ == "__main__":
    build_db()