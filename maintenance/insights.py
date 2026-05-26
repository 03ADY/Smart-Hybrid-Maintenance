"""Executive narrative and ROI (no external APIs)."""

from datetime import datetime

import pandas as pd

from maintenance.config import (
    DEFAULT_DOWNTIME_COST_PER_HOUR,
    DEFAULT_PREVENTIVE_COST,
    HEALTH_CRITICAL,
    HEALTH_WARNING,
    HOURS_SAVED_EARLY_ACTION,
    NUM_MACHINES,
)


def fleet_summary(reports: dict[int, dict]) -> dict:
    if not reports:
        return {"avg_health": 0, "critical": 0, "warning": 0, "healthy": NUM_MACHINES, "worst_id": None, "worst_health": 1.0}
    scores = [r["health_metrics"]["health_score"] for r in reports.values()]
    critical = sum(1 for s in scores if s < HEALTH_CRITICAL)
    warning = sum(1 for s in scores if HEALTH_CRITICAL <= s < HEALTH_WARNING)
    healthy = len(scores) - critical - warning
    worst_id = min(reports, key=lambda k: reports[k]["health_metrics"]["health_score"])
    return {
        "avg_health": sum(scores) / len(scores),
        "critical": critical,
        "warning": warning,
        "healthy": healthy,
        "worst_id": worst_id,
        "worst_health": reports[worst_id]["health_metrics"]["health_score"],
    }


def insight_cards(summary: dict, reports: dict[int, dict], scenario: str) -> list[dict]:
    cards = [
        {
            "icon": "🏭",
            "title": "Fleet health",
            "body": f"Average health {summary['avg_health']:.0%} across {len(reports) or NUM_MACHINES} monitored assets.",
            "tone": "positive" if summary["avg_health"] >= HEALTH_WARNING else "warning",
        },
        {
            "icon": "🚨",
            "title": "Critical assets",
            "body": f"{summary['critical']} machine(s) below critical threshold — prioritize dispatch.",
            "tone": "warning" if summary["critical"] else "positive",
        },
    ]
    if summary.get("worst_id") is not None:
        r = reports.get(summary["worst_id"], {})
        prob = r.get("health_metrics", {}).get("failure_prob", 0)
        cards.append({
            "icon": "⚙️",
            "title": "Highest risk",
            "body": f"Machine #{summary['worst_id']} at {summary['worst_health']:.0%} health ({prob:.0%} failure risk).",
            "tone": "warning",
        })
    alerts = [r for r in reports.values() if r.get("problem_description", "").startswith("Critical") or "Excessive" in r.get("problem_description", "")]
    if alerts:
        a = alerts[0]
        cards.append({
            "icon": "🔧",
            "title": "Active alert",
            "body": f"{a['problem_description']} — {a['maintenance_action']['label']}.",
            "tone": "warning",
        })
    cards.append({
        "icon": "🎬",
        "title": "Scenario",
        "body": f"Running {scenario} simulation profile.",
        "tone": "neutral",
    })
    return cards


def estimate_roi(
    reports: dict[int, dict],
    *,
    downtime_cost: float = DEFAULT_DOWNTIME_COST_PER_HOUR,
    hours_saved: float = HOURS_SAVED_EARLY_ACTION,
) -> dict:
    critical = [r for r in reports.values() if r["health_metrics"]["health_score"] < HEALTH_CRITICAL]
    prevented = len(critical) * downtime_cost * hours_saved
    preventive_spend = len(critical) * DEFAULT_PREVENTIVE_COST
    net = prevented - preventive_spend
    return {
        "machines_at_risk": len(critical),
        "downtime_avoided": prevented,
        "preventive_spend": preventive_spend,
        "net_benefit": net,
        "downtime_cost": downtime_cost,
        "hours_saved": hours_saved,
    }


def executive_brief(summary: dict, reports: dict[int, dict], scenario: str, roi: dict) -> str:
    lines = [
        f"# {datetime.now().strftime('%Y-%m-%d %H:%M')} — PredictiveOps Executive Brief",
        f"**Scenario:** {scenario}",
        "",
        "## Fleet snapshot",
        f"- Average health: **{summary['avg_health']:.1%}**",
        f"- Critical: **{summary['critical']}** · Warning: **{summary['warning']}** · Healthy: **{summary['healthy']}**",
    ]
    if summary.get("worst_id") is not None:
        r = reports[summary["worst_id"]]
        lines.extend([
            f"- Highest risk: **Machine #{summary['worst_id']}** ({summary['worst_health']:.1%})",
            f"- Active issue: {r.get('problem_description', 'N/A')}",
            f"- Recommended: {r.get('suggested_resolution', 'N/A')}",
        ])
    lines.extend([
        "",
        "## Economics (modeled)",
        f"- Downtime cost assumption: **${roi['downtime_cost']:,.0f}/hr**",
        f"- Estimated downtime avoided (early action): **${roi['downtime_avoided']:,.0f}**",
        f"- Preventive spend estimate: **${roi['preventive_spend']:,.0f}**",
        f"- **Net benefit: ${roi['net_benefit']:,.0f}**",
        "",
        "## Recommended actions",
        "1. Dispatch P1 technician to critical assets within 2 hours.",
        "2. Schedule inspect on warning-tier machines this shift.",
        "3. Export fleet CSV for CMMS work-order creation.",
        "",
        "---",
        "*PredictiveOps Enterprise — demo maintenance brief*",
    ])
    return "\n".join(lines)


def period_compare(history: pd.DataFrame) -> dict | None:
    if history.empty or "timestamp" not in history.columns:
        return None
    h = history.copy()
    h["timestamp"] = pd.to_datetime(h["timestamp"])
    mid = h["timestamp"].median()
    first = h[h["timestamp"] <= mid]
    second = h[h["timestamp"] > mid]
    if first.empty or second.empty:
        return None
    return {
        "health_first": first["health_score"].mean(),
        "health_second": second["health_score"].mean(),
        "delta": second["health_score"].mean() - first["health_score"].mean(),
    }
