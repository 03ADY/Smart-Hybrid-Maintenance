"""Fleet-wide command center — multi-machine simulation."""

import json
import time

import pandas as pd
import plotly.express as px
import streamlit as st

import database
from maintenance.analytics import fleet_health_heatmap
from maintenance.bootstrap import (
    ensure_model_message,
    fleet_status_color,
    get_system,
    init_app,
    load_sensor_pool,
    render_alert_banner,
    render_demo_sidebar,
    render_insight_cards,
)
from maintenance.config import APP_NAME, NUM_MACHINES
from maintenance.insights import estimate_roi, executive_brief, fleet_summary, insight_cards
from maintenance.reports import html_executive_report
from maintenance.theme import page_setup

page_setup("Fleet Command", "🌐")
init_app()
st.title("🌐 Fleet Command Center")

if st.session_state.get("seed_msg"):
    st.toast(st.session_state.pop("seed_msg"))

if not ensure_model_message():
    st.stop()

opts = render_demo_sidebar()
system = get_system()
pool = load_sensor_pool()

if st.sidebar.button("▶️ Run fleet scan", type="primary"):
    st.session_state.fleet_run = True
if st.sidebar.button("⏹️ Stop"):
    st.session_state.fleet_run = False
refresh = 2 if opts["present"] else st.sidebar.slider("Refresh (sec)", 1, 5, 2)

if "fleet_reports" not in st.session_state:
    st.session_state.fleet_reports = {}

if st.session_state.get("fleet_run") and system:
    reports = system.monitor_fleet(list(range(NUM_MACHINES)), pool)
    for rep in reports.values():
        database.add_report(rep)
    st.session_state.fleet_reports = reports
    time.sleep(refresh)
    st.rerun()
elif not st.session_state.fleet_reports:
    db_fleet = database.get_fleet_latest()
    if not db_fleet.empty:
        st.session_state.fleet_reports = {
            int(row.machine_id): {
                "machine_id": int(row.machine_id),
                "health_metrics": {
                    "health_score": row.health_score,
                    "failure_prob": row.failure_prob,
                    "rul": row.rul,
                    "status": getattr(row, "status", "HEALTHY"),
                },
                "maintenance_action": {"action": int(row.action), "label": getattr(row, "action_label", "?")},
                "problem_description": getattr(row, "problem_description", "No issue detected."),
                "suggested_resolution": getattr(row, "suggested_resolution", ""),
                "priority": getattr(row, "priority", "P3"),
                "work_order": {"title": getattr(row, "problem_description", "OK"), "eta_hours": 2, "status": "OPEN"},
            }
            for row in db_fleet.itertuples()
        }

reports = st.session_state.get("fleet_reports", {})
render_alert_banner(reports)

summary = fleet_summary(reports)
roi = estimate_roi(reports, downtime_cost=opts["downtime_cost"])
brief = executive_brief(summary, reports, opts["scenario"], roi)
html_report = html_executive_report(brief, summary, roi)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Avg fleet health", f"{summary['avg_health']:.0%}")
c2.metric("Critical", summary["critical"], delta_color="inverse")
c3.metric("Warning", summary["warning"])
c4.metric("Healthy", summary["healthy"])
c5.metric("Net ROI (modeled)", f"${roi['net_benefit']:,.0f}")

render_insight_cards(insight_cards(summary, reports, opts["scenario"]))

col_a, col_b = st.columns(2)
with col_a:
    with st.expander("📑 Executive brief", expanded=opts["present"]):
        st.markdown(brief)
        st.download_button("Brief (.md)", brief.encode(), "predictiveops_brief.md")
with col_b:
    st.download_button("Report (.html)", html_report.encode(), "predictiveops_report.html", type="primary")

st.subheader("Fleet health map")
drill = st.selectbox("Drill into machine", ["—"] + list(range(NUM_MACHINES)), format_func=lambda x: "All" if x == "—" else f"Machine #{x}")

cols = st.columns(5)
for mid in range(NUM_MACHINES):
    rep = reports.get(mid)
    score = rep["health_metrics"]["health_score"] if rep else 0.85
    status = rep["health_metrics"].get("status", "—") if rep else "IDLE"
    color = fleet_status_color(score, opts["critical"], opts["warn"])
    highlight = drill == mid
    border = f"4px solid {color}" if highlight else f"2px solid {color}"
    with cols[mid % 5]:
        st.markdown(
            f'<div style="background:{color}22;border:{border};border-radius:12px;padding:1rem;text-align:center;">'
            f'<div style="font-weight:700;">Machine #{mid}</div>'
            f'<div style="font-size:1.4rem;font-weight:800;color:{color};">{score:.0%}</div>'
            f'<div style="font-size:0.8rem;">{status}</div></div>',
            unsafe_allow_html=True,
        )

if drill != "—" and reports.get(drill):
    r = reports[drill]
    st.markdown(f"### Machine #{drill} detail")
    d1, d2, d3 = st.columns(3)
    d1.write(f"**Issue:** {r.get('problem_description')}")
    d2.write(f"**Action:** {r['maintenance_action']['label']}")
    d3.write(f"**Resolution:** {r.get('suggested_resolution')}")
    alerts = r.get("sensor_alerts", [])
    if alerts:
        st.warning("Sensor flags: " + ", ".join(alerts))

if reports:
    rank = pd.DataFrame([
        {
            "machine_id": mid,
            "health": r["health_metrics"]["health_score"],
            "failure_prob": r["health_metrics"]["failure_prob"],
            "action": r["maintenance_action"]["label"],
            "issue": r.get("problem_description", ""),
        }
        for mid, r in reports.items()
    ]).sort_values("health")
    st.subheader("Risk ranking")
    st.dataframe(rank, use_container_width=True, hide_index=True)
    st.plotly_chart(
        px.bar(rank, x="machine_id", y="health", color="health", color_continuous_scale="RdYlGn"),
        use_container_width=True,
    )

hist = database.get_fleet_history(500)
if not hist.empty:
    heat = fleet_health_heatmap(hist)
    if not heat.empty and heat.shape[1] > 1:
        st.subheader("Fleet health heatmap (hourly)")
        st.plotly_chart(px.imshow(heat, color_continuous_scale="RdYlGn", aspect="auto"), use_container_width=True)
    st.download_button("Export fleet CSV", hist.to_csv(index=False).encode(), "fleet_history.csv")

st.caption(APP_NAME)
