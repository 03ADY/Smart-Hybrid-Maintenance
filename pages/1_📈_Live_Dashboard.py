"""Single-machine live telemetry and work orders."""

import json
import random
import time

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import database
from maintenance.bootstrap import (
    ensure_model_message,
    get_system,
    init_app,
    load_sensor_pool,
    render_alert_banner,
    render_demo_sidebar,
)
from maintenance.config import PLAYBOOKS
from maintenance.inventory import recommend_parts
from maintenance.theme import page_setup

page_setup("Live Dashboard", "📈")
init_app()
st.title("📈 Live Operations Dashboard")

if not ensure_model_message():
    st.stop()

opts = render_demo_sidebar()
system = get_system()
pool = load_sensor_pool()
render_alert_banner(st.session_state.get("fleet_reports"))

mid = st.sidebar.selectbox("Machine", range(10), format_func=lambda x: f"Machine #{x}")
compare = st.sidebar.checkbox("Compare with machine", value=False)
compare_mid = st.sidebar.selectbox("Compare to", range(10), index=1, format_func=lambda x: f"Machine #{x}") if compare else None
speed = 2 if opts["present"] else st.sidebar.slider("Refresh (sec)", 1, 5, 2)

if st.sidebar.button("▶️ Start simulation", type="primary"):
    st.session_state.run = True
if st.sidebar.button("⏹️ Stop"):
    st.session_state.run = False

if st.sidebar.button("✅ Acknowledge alert"):
    st.session_state.ack = True
if st.sidebar.button("📅 Schedule service"):
    st.session_state.scheduled = True

hist = database.get_reports_by_machine(mid)
if not hist.empty and st.sidebar.button("📥 Export machine CSV"):
    st.sidebar.download_button("Download", hist.to_csv(index=False).encode(), f"machine_{mid}.csv")

slot = st.empty()

if st.session_state.get("run") and system:
    idx = random.randint(0, len(pool) - 50)
    for i in range(idx, min(idx + 3, len(pool))):
        if not st.session_state.get("run"):
            break
        report = system.monitor_machine(mid, pool[i])
        database.add_report(report)
        h = report["health_metrics"]
        with slot.container():
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Health", f"{h['health_score']:.0%}")
            c2.metric("Failure prob", f"{h['failure_prob']:.0%}", delta_color="inverse")
            c3.metric("RUL (est.)", f"{h['rul']:.0f} h")
            c4.metric("Status", h.get("status", "—"))
            c5.metric("Action", report["maintenance_action"]["label"])

            if report["problem_description"] != "No issue detected.":
                st.error(f"**{report['problem_description']}** ({report.get('priority', '')}) — {report['suggested_resolution']}")
                pb = PLAYBOOKS.get(report["problem_description"])
                if pb:
                    st.info(f"Playbook: {pb}")
            else:
                st.success("All sensors nominal")

            if report.get("sensor_alerts"):
                st.warning("Sensor anomalies: " + " · ".join(report["sensor_alerts"]))

            parts = recommend_parts(report.get("problem_description", ""))
            if parts:
                st.markdown("**Suggested spare parts:** " + ", ".join(f"{p['sku']} ({p['name']})" for p in parts))

            if compare and compare_mid is not None and compare_mid != mid:
                rep_b = system.monitor_machine(compare_mid, pool[min(i + 1, len(pool) - 1)])
                h2 = rep_b["health_metrics"]
                st.markdown(f"**Compare Machine #{compare_mid}:** health {h2['health_score']:.0%} vs #{mid} {h['health_score']:.0%}")

            wo = report.get("work_order", {})
            w1, w2, w3 = st.columns(3)
            w1.metric("Work order", wo.get("title", "—")[:40])
            w2.metric("ETA (h)", wo.get("eta_hours", 0))
            status = wo.get("status", "—")
            if st.session_state.get("ack"):
                status = "ACKNOWLEDGED"
            if st.session_state.get("scheduled"):
                status = "SCHEDULED"
            w3.metric("WO status", status)

            sensors = report.get("sensor_snapshot", {})
            if sensors:
                sdf = pd.DataFrame({"sensor": list(sensors.keys()), "value": list(sensors.values())})
                sc1, sc2 = st.columns(2)
                with sc1:
                    st.plotly_chart(px.bar(sdf, x="sensor", y="value", title="Live sensor strip"), use_container_width=True)
                with sc2:
                    exp = report.get("explanation", {})
                    edf = pd.DataFrame({"sensor": list(exp.keys()), "driver": list(exp.values())})
                    st.plotly_chart(px.bar(edf, x="sensor", y="driver", title="Top drivers (normalized)"), use_container_width=True)

            trend = system.health_trend_df()
            if not trend.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(y=trend["health_score"], mode="lines", name="Health"))
                fig.add_hline(y=0.5, line_dash="dash", line_color="red", annotation_text="Critical")
                fig.add_hline(y=0.75, line_dash="dash", line_color="orange", annotation_text="Warning")
                fig.update_layout(height=280, yaxis_range=[0, 1], title="Health trend (session)")
                st.plotly_chart(fig, use_container_width=True)

        time.sleep(speed)
    if st.session_state.get("run"):
        st.rerun()
else:
    st.info("Start simulation to stream live telemetry, sensors, and work orders.")
