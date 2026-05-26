"""OEE-style plant KPIs derived from fleet health (demo metrics)."""

import pandas as pd

from maintenance.config import HEALTH_WARNING


def compute_oee(latest: pd.DataFrame) -> dict:
    if latest.empty:
        return {
            "oee": 0.0,
            "availability": 0.0,
            "performance": 0.0,
            "quality": 0.0,
            "uptime_pct": 0.0,
        }
    availability = float((latest["health_score"] >= HEALTH_WARNING).mean())
    performance = float(latest["health_score"].mean())
    quality = float(1 - latest["failure_prob"].clip(0, 1).mean())
    oee = availability * performance * quality
    return {
        "oee": round(oee * 100, 1),
        "availability": round(availability * 100, 1),
        "performance": round(performance * 100, 1),
        "quality": round(quality * 100, 1),
        "uptime_pct": round(availability * 100, 1),
    }
