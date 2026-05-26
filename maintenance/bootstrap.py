"""Shared Streamlit resources across pages."""

import json

import streamlit as st

import database
from maintenance.config import (
    DEFAULT_DOWNTIME_COST_PER_HOUR,
    HEALTH_CRITICAL,
    HEALTH_WARNING,
    MODEL_META_PATH,
    MODEL_PATH,
    NUM_MACHINES,
)
from maintenance.core import HybridMaintenanceSystem, SupervisedConfig, create_synthetic_data
from maintenance.health_model import load_health_model
from maintenance.scenarios import SCENARIOS, get_scenario


@st.cache_resource
def load_model_cached():
    return load_health_model(MODEL_PATH)


@st.cache_data
def load_sensor_pool():
    return create_synthetic_data(SupervisedConfig(), num_samples=500)


def get_system() -> HybridMaintenanceSystem | None:
    model = load_model_cached()
    if model is None:
        return None
    scenario_name = st.session_state.get("scenario_name", "Normal operations")
    if "system" not in st.session_state:
        st.session_state.system = HybridMaintenanceSystem(model, get_scenario(scenario_name))
    else:
        st.session_state.system.set_scenario(get_scenario(scenario_name))
    return st.session_state.system


def model_metadata() -> dict:
    if MODEL_META_PATH.exists():
        return json.loads(MODEL_META_PATH.read_text(encoding="utf-8"))
    return {"epochs": "—", "loss": "—", "trained": "Run train.py"}


def render_insight_cards(cards: list[dict]) -> None:
    html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0.75rem;margin:0.5rem 0 1rem;">'
    for c in cards[:5]:
        border = {"positive": "#22c55e", "warning": "#f59e0b", "neutral": "#6366f1"}.get(c.get("tone", "neutral"), "#6366f1")
        html += (
            f'<div style="background:rgba(30,41,59,0.92);border:1px solid rgba(148,163,184,0.15);'
            f'border-left:4px solid {border};border-radius:12px;padding:0.9rem 1rem;">'
            f'<div style="font-size:0.85rem;color:#94a3b8;">{c["icon"]} {c["title"]}</div>'
            f'<div style="font-size:0.92rem;color:#e2e8f0;margin-top:0.35rem;">{c["body"]}</div></div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_demo_sidebar() -> dict:
    from maintenance.theme import inject_theme

    inject_theme()
    st.markdown("### 🎬 Demo")
    present = st.toggle("Present mode", value=st.session_state.get("present_mode", True), key="present_mode_toggle")
    st.session_state.present_mode = present
    scenario = st.selectbox("Scenario", list(SCENARIOS.keys()), key="scenario_select")
    st.session_state.scenario_name = scenario
    st.caption(SCENARIOS[scenario]["blurb"])

    crit = HEALTH_CRITICAL if present else st.slider("Critical below", 0.3, 0.6, HEALTH_CRITICAL, 0.05)
    warn = HEALTH_WARNING if present else st.slider("Warning below", 0.6, 0.9, HEALTH_WARNING, 0.05)
    downtime = DEFAULT_DOWNTIME_COST_PER_HOUR if present else st.number_input(
        "Downtime cost ($/hr)", 1000, 20000, DEFAULT_DOWNTIME_COST_PER_HOUR, 500
    )

    with st.expander("Demo tools"):
        if st.button("🔄 Reseed telemetry", use_container_width=True):
            from maintenance.seed import seed_force
            n = seed_force()
            st.session_state["seed_msg"] = f"Reseeded {n} records." if n > 0 else "Train model first."
            st.rerun()
        if st.button("🗑️ Reset demo DB", use_container_width=True):
            database.init_db(force_reset=True)
            for key in ("fleet_reports", "fleet_run", "run", "acked_alerts"):
                st.session_state.pop(key, None)
            st.session_state["seed_msg"] = "Database cleared."
            st.rerun()

    return {"present": present, "scenario": scenario, "critical": crit, "warn": warn, "downtime_cost": downtime}


def fleet_status_color(score: float, critical: float = HEALTH_CRITICAL, warning: float = HEALTH_WARNING) -> str:
    if score < critical:
        return "#ef4444"
    if score < warning:
        return "#f59e0b"
    return "#22c55e"


def init_app(seed: bool = True):
    database.init_db(force_reset=False)
    if seed:
        try:
            from maintenance.seed import seed_if_empty
            n = seed_if_empty()
            if n > 0:
                try:
                    st.session_state["seed_msg"] = f"Loaded {n} demo telemetry records."
                except Exception:
                    pass
        except Exception:
            pass


def render_alert_banner(reports: dict | None = None):
    """Top-of-page critical alert strip."""
    if reports is None:
        df = database.get_fleet_latest()
        if df.empty:
            return
        critical = df[df["health_score"] < HEALTH_CRITICAL]
        if critical.empty:
            return
        mids = ", ".join(f"#{int(m)}" for m in critical["machine_id"].tolist())
        st.error(f"🚨 CRITICAL ASSETS: Machines {mids} — dispatch technician immediately.")
        return
    crit = [mid for mid, r in reports.items() if r["health_metrics"]["health_score"] < HEALTH_CRITICAL]
    if crit:
        st.error(f"🚨 CRITICAL: Machines {', '.join(f'#{m}' for m in crit)} require immediate action.")


def ensure_model_message():
    if not MODEL_PATH.exists():
        st.info("Using built-in health estimator (no `train.py` needed for demos). Run `python train.py` locally for full LSTM.")
    return True
