"""Centralized alert feed with acknowledge workflow."""

import pandas as pd
import streamlit as st

import database
from maintenance.bootstrap import init_app
from maintenance.config import APP_NAME

from maintenance.theme import page_setup

page_setup("Alert Center", "🚨", set_config=False)
init_app()
st.title("🚨 Alert Center")

if "acked_alerts" not in st.session_state:
    st.session_state.acked_alerts = set()

alerts = database.get_alerts(300)
if alerts.empty:
    st.success("No active alerts in the log. Run a fleet scan to generate events.")
    st.stop()

alerts = alerts.copy()
alerts["alert_id"] = alerts["id"].astype(str) + "-" + alerts["machine_id"].astype(str)
alerts["acked"] = alerts["alert_id"].isin(st.session_state.acked_alerts)

if "priority" not in alerts.columns:
    alerts["priority"] = "—"

filt = st.multiselect("Priority filter", sorted(alerts["priority"].unique()), default=list(alerts["priority"].unique()))
show_acked = st.checkbox("Show acknowledged", value=False)

view = alerts[alerts["priority"].isin(filt)]
if not show_acked:
    view = view[~view["acked"]]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Open alerts", int((~alerts["acked"]).sum()))
c2.metric("P1 open", int((~alerts["acked"] & (alerts["priority"] == "P1")).sum()))
c3.metric("Critical health", int((alerts["health_score"] < 0.5).sum()))
c4.metric("Showing", len(view))

for _, row in view.head(25).iterrows():
    aid = row["alert_id"]
    severity = "🔴" if row["health_score"] < 0.5 else "🟠"
    with st.container(border=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            prob = row.get("problem_description", "Threshold breach")
            st.markdown(f"{severity} **Machine #{int(row['machine_id'])}** · {prob}")
            st.caption(f"{row['timestamp']} · {row.get('action_label', '—')} · Priority {row.get('priority', '—')}")
            if pd.notna(row.get("suggested_resolution")) and row.get("suggested_resolution"):
                st.write(row["suggested_resolution"])
        with col2:
            if not row["acked"]:
                if st.button("Acknowledge", key=f"ack_{aid}"):
                    st.session_state.acked_alerts.add(aid)
                    st.rerun()
            else:
                st.caption("✓ Acked")

if not view.empty:
    st.download_button("Export alerts CSV", view.to_csv(index=False).encode(), "alerts_export.csv")

st.caption(APP_NAME)
