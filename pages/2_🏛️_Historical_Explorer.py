"""Historical audit, MTBF-style metrics, and period comparison."""

import json

import pandas as pd
import plotly.express as px
import streamlit as st

import database
from maintenance.bootstrap import init_app, render_demo_sidebar
from maintenance.config import ACTION_LABELS
from maintenance.analytics import shift_comparison
from maintenance.bootstrap import render_alert_banner
from maintenance.insights import period_compare

from maintenance.theme import page_setup

page_setup("Historical Explorer", "🏛️")
init_app()
st.title("🏛️ Historical Data Explorer")
render_demo_sidebar()
render_alert_banner()

machines = database.get_all_machines() or list(range(10))
machine_id = st.sidebar.selectbox("Machine", machines, format_func=lambda x: f"Machine #{x}")

history = database.get_reports_by_machine(machine_id)
if history.empty:
    st.warning(f"No history for Machine #{machine_id}. Run Fleet scan or Live simulation first.")
    st.stop()

history["timestamp"] = pd.to_datetime(history["timestamp"])
cmp = period_compare(history)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Records", len(history))
c2.metric("Avg health", f"{history['health_score'].mean():.0%}")
c3.metric("Min health", f"{history['health_score'].min():.0%}")
last_label = history["action_label"].iloc[-1] if "action_label" in history.columns and pd.notna(history["action_label"].iloc[-1]) else ACTION_LABELS.get(int(history["action"].iloc[-1]), "?")
c4.metric("Last action", last_label)

if cmp:
    st.caption(f"Period compare: 2nd half vs 1st half health **{cmp['delta']:+.1%}** ({cmp['health_first']:.0%} → {cmp['health_second']:.0%})")

shift = shift_comparison(history)
if shift:
    st.caption(f"Shift compare: Day {shift['day_shift']:.0%} vs Night {shift['night_shift']:.0%} (Δ {shift['delta']:+.1%})")

# MTBF-style: mean gap between critical events
critical = history[history["health_score"] < 0.5]
if len(critical) >= 2:
    gaps = critical["timestamp"].diff().dt.total_seconds() / 3600
    st.metric("Mean hours between critical events", f"{gaps.dropna().mean():.1f}")

tab1, tab2, tab3 = st.tabs(["📈 Trends", "🔧 Actions & alerts", "📋 Raw log"])

with tab1:
    st.plotly_chart(
        px.line(history, x="timestamp", y=["health_score", "failure_prob"], title="Health & failure probability"),
        use_container_width=True,
    )
    if "rul" in history.columns:
        st.plotly_chart(px.area(history, x="timestamp", y="rul", title="Remaining useful life (est.)"), use_container_width=True)

with tab2:
    if "action_label" in history.columns:
        ac = history["action_label"].value_counts().reset_index()
        ac.columns = ["action", "count"]
        st.plotly_chart(px.bar(ac, x="action", y="count", title="Recommended actions"), use_container_width=True)
    if "problem_description" in history.columns:
        alerts = history[history["problem_description"].notna() & (history["problem_description"] != "No issue detected.")]
        if not alerts.empty:
            st.subheader("Alert timeline")
            show = alerts[["timestamp", "problem_description", "suggested_resolution", "priority", "action_label"]].tail(20)
            st.dataframe(show, use_container_width=True, hide_index=True)

with tab3:
    st.dataframe(
        history,
        column_config={
            "timestamp": st.column_config.DatetimeColumn(format="YYYY-MM-DD HH:mm:ss"),
            "health_score": st.column_config.ProgressColumn(min_value=0, max_value=1),
            "failure_prob": st.column_config.ProgressColumn(min_value=0, max_value=1),
        },
        use_container_width=True,
    )
    st.download_button("Export", history.to_csv(index=False).encode(), f"machine_{machine_id}_history.csv")

# Sensor replay from last snapshot
if "sensor_snapshot" in history.columns and pd.notna(history["sensor_snapshot"].iloc[-1]):
    try:
        snap = json.loads(history["sensor_snapshot"].iloc[-1])
        st.subheader("Last sensor snapshot")
        st.plotly_chart(px.bar(x=list(snap.keys()), y=list(snap.values()), title="Sensors at last reading"), use_container_width=True)
    except (json.JSONDecodeError, TypeError):
        pass
