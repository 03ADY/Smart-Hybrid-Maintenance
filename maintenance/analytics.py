"""Fleet analytics: anomalies, shifts, calendar, heatmaps."""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from maintenance.config import FEATURE_NAMES, HEALTH_CRITICAL, NUM_MACHINES


SENSOR_LIMITS = {name: (0.15, 0.92) for name in FEATURE_NAMES}


def detect_sensor_anomalies(snapshot: dict[str, float]) -> list[str]:
    flags = []
    for name, (lo, hi) in SENSOR_LIMITS.items():
        val = snapshot.get(name)
        if val is None:
            continue
        if val < lo:
            flags.append(f"{name} low ({val:.2f})")
        elif val > hi:
            flags.append(f"{name} high ({val:.2f})")
    return flags


def shift_comparison(history: pd.DataFrame) -> dict | None:
    if history.empty or "timestamp" not in history.columns:
        return None
    h = history.copy()
    h["timestamp"] = pd.to_datetime(h["timestamp"])
    h["shift"] = np.where(h["timestamp"].dt.hour < 12, "Day shift", "Night shift")
    g = h.groupby("shift")["health_score"].agg(["mean", "count"])
    if len(g) < 2:
        return None
    day = g.loc["Day shift", "mean"] if "Day shift" in g.index else g["mean"].iloc[0]
    night = g.loc["Night shift", "mean"] if "Night shift" in g.index else g["mean"].iloc[-1]
    return {"day_shift": day, "night_shift": night, "delta": night - day}


def build_maintenance_calendar(reports: dict[int, dict], days: int = 7) -> pd.DataFrame:
    """Generate planned maintenance slots from open work orders."""
    rows = []
    base = datetime.utcnow()
    slot = 0
    for mid, rep in sorted(reports.items()):
        wo = rep.get("work_order", {})
        if wo.get("status") == "CLOSED" or rep["maintenance_action"]["action"] == 0:
            continue
        start = base + timedelta(hours=slot * 4)
        end = start + timedelta(hours=wo.get("eta_hours", 2))
        rows.append({
            "machine_id": mid,
            "title": wo.get("title", f"Machine {mid} service"),
            "priority": rep.get("priority", "P3"),
            "action": rep["maintenance_action"]["label"],
            "start": start,
            "end": end,
            "technician": f"Team {(mid % 3) + 1}",
        })
        slot += 1
    if not rows:
        for mid in range(min(3, NUM_MACHINES)):
            start = base + timedelta(days=mid)
            rows.append({
                "machine_id": mid,
                "title": f"Machine #{mid} preventive inspect",
                "priority": "P3",
                "action": "Inspect",
                "start": start,
                "end": start + timedelta(hours=2),
                "technician": "Team 1",
            })
    return pd.DataFrame(rows)


def fleet_health_heatmap(history: pd.DataFrame) -> pd.DataFrame:
    if history.empty:
        return pd.DataFrame()
    h = history.copy()
    h["timestamp"] = pd.to_datetime(h["timestamp"])
    h["bucket"] = h["timestamp"].dt.floor("h")
    pivot = h.pivot_table(index="machine_id", columns="bucket", values="health_score", aggfunc="mean")
    return pivot.sort_index()


def aggregate_drivers(history: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    if history.empty or "explanation" not in history.columns:
        return pd.DataFrame(columns=["sensor", "avg_driver"])
    import json
    totals: dict[str, list[float]] = {n: [] for n in FEATURE_NAMES}
    for raw in history["explanation"].dropna().tail(200):
        try:
            exp = json.loads(raw) if isinstance(raw, str) else raw
            for k, v in exp.items():
                if k in totals:
                    totals[k].append(float(v))
        except (json.JSONDecodeError, TypeError):
            continue
    rows = [{"sensor": k, "avg_driver": np.mean(v) if v else 0} for k, v in totals.items() if v]
    df = pd.DataFrame(rows).sort_values("avg_driver", ascending=False).head(top_n)
    return df


def cmms_export_payload(reports: dict[int, dict]) -> list[dict]:
    orders = []
    for mid, rep in reports.items():
        if rep["maintenance_action"]["action"] == 0:
            continue
        orders.append({
            "asset_id": f"M{mid:03d}",
            "priority": rep.get("priority", "P3"),
            "summary": rep.get("problem_description", "Maintenance required"),
            "instructions": rep.get("suggested_resolution", ""),
            "recommended_action": rep["maintenance_action"]["label"],
            "health_score": rep["health_metrics"]["health_score"],
            "failure_probability": rep["health_metrics"]["failure_prob"],
        })
    return orders
