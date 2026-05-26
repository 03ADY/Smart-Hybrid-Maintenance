"""Shared Streamlit resources across pages."""

import json

import streamlit as st

import database
from maintenance.config import (
    APP_NAME,
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


@st.cache_resource(show_spinner=False)
def load_model_cached_v2():
    """v2 suffix busts stale Streamlit Cloud cache from older builds."""
    return load_health_model(MODEL_PATH)


@st.cache_data(show_spinner=False)
def load_sensor_pool_v2():
    return create_synthetic_data(SupervisedConfig(), num_samples=500)


def load_model_cached():
    return load_model_cached_v2()


def load_sensor_pool():
    return load_sensor_pool_v2()


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
        icon = c.get("icon", "•")
        title = c.get("title", "Insight")
        body = c.get("body", "")
        html += (
            f'<div style="background:rgba(30,41,59,0.92);border:1px solid rgba(148,163,184,0.15);'
            f'border-left:4px solid {border};border-radius:12px;padding:0.9rem 1rem;">'
            f'<div style="font-size:0.85rem;color:#94a3b8;">{icon} {title}</div>'
            f'<div style="font-size:0.92rem;color:#e2e8f0;margin-top:0.35rem;">{body}</div></div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def get_demo_opts() -> dict:
    """Demo controls set in app.py sidebar before each page runs."""
    return st.session_state.get(
        "demo_opts",
        {
            "present": True,
            "scenario": "Normal operations",
            "critical": HEALTH_CRITICAL,
            "warn": HEALTH_WARNING,
            "downtime_cost": DEFAULT_DOWNTIME_COST_PER_HOUR,
        },
    )


def render_demo_sidebar() -> dict:
    sb = st.sidebar
    sb.markdown("### 🎬 Demo")
    present = sb.toggle(
        "Present mode",
        value=st.session_state.get("present_mode", True),
        key="present_mode_toggle",
    )
    st.session_state.present_mode = present
    scenario_names = list(SCENARIOS.keys())
    current = st.session_state.get("scenario_name", scenario_names[0])
    scenario_idx = scenario_names.index(current) if current in scenario_names else 0
    scenario = sb.radio(
        "Scenario",
        scenario_names,
        index=scenario_idx,
        key="scenario_select",
    )
    st.session_state.scenario_name = scenario
    sb.caption(SCENARIOS.get(scenario, SCENARIOS["Normal operations"]).get("blurb", ""))

    crit = HEALTH_CRITICAL if present else sb.slider("Critical below", 0.3, 0.6, HEALTH_CRITICAL, 0.05)
    warn = HEALTH_WARNING if present else sb.slider("Warning below", 0.6, 0.9, HEALTH_WARNING, 0.05)
    downtime = DEFAULT_DOWNTIME_COST_PER_HOUR if present else sb.number_input(
        "Downtime cost ($/hr)", 1000, 20000, DEFAULT_DOWNTIME_COST_PER_HOUR, 500
    )

    with sb.expander("Demo tools"):
        if sb.button("🔄 Reseed telemetry", use_container_width=True):
            from maintenance.seed import seed_force

            n = seed_force()
            st.session_state["seed_msg"] = f"Reseeded {n} records." if n > 0 else "Train model first."
            st.rerun()
        if sb.button("🗑️ Reset demo DB", use_container_width=True):
            database.init_db(force_reset=True)
            for key in ("fleet_reports", "fleet_run", "run", "acked_alerts"):
                st.session_state.pop(key, None)
            st.session_state["seed_msg"] = "Database cleared."
            st.rerun()

    opts = {
        "present": present,
        "scenario": scenario,
        "critical": crit,
        "warn": warn,
        "downtime_cost": downtime,
    }
    st.session_state["demo_opts"] = opts
    return opts


def render_sidebar_footer() -> None:
    """Shared sidebar tail — fills empty space and keeps layout consistent across pages."""
    sb = st.sidebar
    sb.divider()
    kpis = database.fleet_kpis()
    n_alerts = len(database.get_alerts(50))
    if kpis["total_records"]:
        sb.caption(
            f"Fleet · {kpis['avg_health']:.0%} avg health · "
            f"{kpis['critical']} critical · {n_alerts} alerts"
        )
    else:
        sb.caption("Run a fleet scan or live simulation to populate telemetry.")

    sb.markdown("**Shortcuts**")
    sb.page_link("views/dashboard.py", label="🏠 Dashboard", use_container_width=True)
    sb.page_link("pages/0_🌐_Fleet_Command_Center.py", label="🌐 Fleet scan", use_container_width=True)
    sb.page_link("pages/5_🚨_Alert_Center.py", label="🚨 Alerts", use_container_width=True)
    sb.page_link("pages/1_📈_Live_Dashboard.py", label="📈 Live machine", use_container_width=True)
    sb.caption(APP_NAME)


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
