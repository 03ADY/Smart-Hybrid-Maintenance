"""Spare-parts recommendations keyed to fault types (demo catalog)."""

PARTS_CATALOG = [
    {"sku": "BRG-6205", "name": "Bearing kit 6205", "stock": 14, "lead_days": 2},
    {"sku": "CLT-90", "name": "Cooling fan assembly", "stock": 6, "lead_days": 5},
    {"sku": "HYD-SEAL-K", "name": "Hydraulic seal kit", "stock": 22, "lead_days": 3},
    {"sku": "VIB-PAD", "name": "Vibration damping pad", "stock": 30, "lead_days": 1},
    {"sku": "PSU-24V", "name": "24V power supply module", "stock": 8, "lead_days": 4},
    {"sku": "OIL-ISO46", "name": "Lubricant ISO 46 (20L)", "stock": 18, "lead_days": 1},
]

FAULT_TO_PARTS = {
    "Critical overheating": ["CLT-90", "OIL-ISO46"],
    "Excessive vibration": ["BRG-6205", "VIB-PAD"],
    "Pressure drop": ["HYD-SEAL-K", "OIL-ISO46"],
    "Voltage instability": ["PSU-24V"],
}


def recommend_parts(problem: str) -> list[dict]:
    if not problem or problem == "No issue detected.":
        return []
    skus = FAULT_TO_PARTS.get(problem, ["OIL-ISO46"])
    lookup = {p["sku"]: p for p in PARTS_CATALOG}
    out = []
    for sku in skus:
        if sku in lookup:
            row = lookup[sku].copy()
            row["recommended_for"] = problem
            out.append(row)
    return out


def inventory_status() -> list[dict]:
    return PARTS_CATALOG.copy()
