"""Maintenance calendar, work-order queue, CMMS export."""

import json

import pandas as pd
import plotly.express as px
import streamlit as st

import database
from maintenance.analytics import build_maintenance_calendar, cmms_export_payload
from maintenance.inventory import inventory_status, recommend_parts
from maintenance.bootstrap import get_system, init_app, load_sensor_pool, render_alert_banner
from maintenance.config import APP_NAME, NUM_MACHINES

from maintenance.theme import page_setup

page_setup("Maintenance Planner", "📅", set_config=False)
init_app()
st.title("📅 Maintenance Planner")

system = get_system()
pool = load_sensor_pool()
reports = st.session_state.get("fleet_reports", {})

if not reports and system:
    reports = system.monitor_fleet(list(range(NUM_MACHINES)), pool)
    st.session_state.fleet_reports = reports

if not reports:
    latest = database.get_fleet_latest()
    if not latest.empty:
        reports = {
            int(r.machine_id): {
                "machine_id": int(r.machine_id),
                "health_metrics": {"health_score": r.health_score, "failure_prob": r.failure_prob},
                "maintenance_action": {"action": int(r.action), "label": getattr(r, "action_label", "?")},
                "problem_description": getattr(r, "problem_description", ""),
                "suggested_resolution": getattr(r, "suggested_resolution", ""),
                "priority": getattr(r, "priority", "P3"),
                "work_order": {"title": getattr(r, "problem_description", "Inspect"), "eta_hours": 2, "status": "OPEN"},
            }
            for r in latest.itertuples()
        }

render_alert_banner(reports)

cal = build_maintenance_calendar(reports, days=7)
tab1, tab2, tab3, tab4 = st.tabs(["📆 Schedule", "📋 Work queue", "🔗 CMMS export", "📦 Spare parts"])

with tab1:
    if cal.empty:
        st.info("Run a fleet scan to populate work orders.")
    else:
        fig = px.timeline(cal, x_start="start", x_end="end", y="machine_id", color="priority", hover_name="title")
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=400, title="7-day maintenance schedule")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(cal, use_container_width=True, hide_index=True)

with tab2:
    open_orders = [r for r in reports.values() if r["maintenance_action"]["action"] > 0]
    if not open_orders:
        st.success("No open work orders — fleet nominal.")
    else:
        q = pd.DataFrame([{
            "machine": f"#{r['machine_id']}",
            "priority": r.get("priority"),
            "issue": r.get("problem_description"),
            "action": r["maintenance_action"]["label"],
            "resolution": r.get("suggested_resolution"),
        } for r in open_orders])
        st.dataframe(q, use_container_width=True, hide_index=True)

with tab3:
    payload = cmms_export_payload(reports)
    st.json(payload)
    st.download_button("Download CMMS JSON", json.dumps(payload, indent=2).encode(), "cmms_work_orders.json")

with tab4:
    st.subheader("Warehouse catalog")
    st.dataframe(pd.DataFrame(inventory_status()), use_container_width=True, hide_index=True)
    st.subheader("Recommended picks (open faults)")
    rec_rows = []
    for r in reports.values():
        prob = r.get("problem_description", "")
        for p in recommend_parts(prob):
            rec_rows.append({**p, "machine_id": r["machine_id"]})
    if rec_rows:
        st.dataframe(pd.DataFrame(rec_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No fault-based part recommendations — fleet healthy.")

st.caption(APP_NAME)
