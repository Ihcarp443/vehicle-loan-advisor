"""Read-only queries on the vehicle catalogue."""
import json
import sqlite3

from db.setup import DB_PATH


def _rows(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(sql, params)]
    finally:
        conn.close()


def _vehicle(d):
    d["colours"] = json.loads(d["colours"] or "[]")
    return d


def all_vehicles():
    return [_vehicle(d) for d in _rows("SELECT * FROM vehicles ORDER BY vehicle_id")]


def get_vehicle(vehicle_id):
    rows = _rows("SELECT * FROM vehicles WHERE vehicle_id = ?", (vehicle_id,))
    return _vehicle(rows[0]) if rows else None


def get_variants(vehicle_id=None):
    sql, params = "SELECT * FROM variants", ()
    if vehicle_id:
        sql, params = sql + " WHERE vehicle_id = ?", (vehicle_id,)
    rows = _rows(sql + " ORDER BY vehicle_id, ex_showroom", params)
    for r in rows:
        r["features"] = json.loads(r["features"] or "[]")
    return rows


def filter_options():
    vehicles, variants = all_vehicles(), get_variants()
    return {
        "body_types": sorted({v["body_type"] for v in vehicles}),
        "fuel_types": sorted({v["fuel_type"] for v in vehicles}),
        "transmissions": sorted({r["transmission"] for r in variants}),
        "colours": sorted({c for v in vehicles for c in v["colours"]}),
        "seats": sorted({v["seats"] for v in vehicles}),
        "min_ex_showroom": min(r["ex_showroom"] for r in variants),
        "max_ex_showroom": max(r["ex_showroom"] for r in variants),
    }
