"""PredictiveOps Enterprise — landing, OEE scorecard, quick navigation."""

import streamlit as st

import database
from maintenance.bootstrap import fleet_status_color, init_app, model_metadata
from maintenance.config import APP_NAME, FEATURE_NAMES, MODEL_PATH, NUM_MACHINES
from maintenance.oee import compute_oee

init_app()
st.set_page_config(page_title=APP_NAME, page_icon="⚙️", layout="wide")

if st.session_state.get("seed_msg"):
    st.success(st.session_state.pop("seed_msg"))

st.markdown(f"""
<div style="background:linear-gradient(135deg,#0f766e,#0369a1);padding:2rem;border-radius:14px;color:white;">
<h1 style="margin:0;">⚙️ {APP_NAME}</h1>
<p style="margin:0.5rem 0 0;">OEE · Alerts · Spare parts · Full audit trail</p>
</div>
""", unsafe_allow_html=True)

meta = model_metadata()
kpis = database.fleet_kpis()
latest = database.get_fleet_latest()
oee = compute_oee(latest)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("OEE", f"{oee['oee']:.1f}%")
c2.metric("Availability", f"{oee['availability']:.1f}%")
c3.metric("Fleet health", f"{kpis['avg_health']:.0%}" if kpis["total_records"] else "—")
c4.metric("Critical assets", kpis["critical"])
c5.metric("Open alerts", len(database.get_alerts(50)))

st.markdown("#### Quick navigation")
q1, q2, q3, q4, q5 = st.columns(5)
q1.page_link("pages/0_🌐_Fleet_Command_Center.py", label="🌐 Fleet", use_container_width=True)
q2.page_link("pages/5_🚨_Alert_Center.py", label="🚨 Alerts", use_container_width=True)
q3.page_link("pages/1_📈_Live_Dashboard.py", label="📈 Live", use_container_width=True)
q4.page_link("pages/3_📅_Maintenance_Planner.py", label="📅 Planner", use_container_width=True)
q5.page_link("pages/4_🔬_Model_Insights.py", label="🔬 Model", use_container_width=True)

if not latest.empty:
    st.subheader("Fleet snapshot")
    cols = st.columns(5)
    for mid in range(NUM_MACHINES):
        row = latest[latest["machine_id"] == mid]
        score = float(row["health_score"].iloc[-1]) if not row.empty else 0.9
        color = fleet_status_color(score)
        with cols[mid % 5]:
            st.markdown(
                f'<div style="text-align:center;padding:0.5rem;border:2px solid {color};border-radius:8px;">'
                f'<b>#{mid}</b><br><span style="color:{color};font-size:1.2rem;">{score:.0%}</span></div>',
                unsafe_allow_html=True,
            )

with st.expander("✅ Presenter checklist (2 min)", expanded=False):
    st.markdown("""
1. Show **OEE** row and fleet snapshot on this page  
2. **Fleet Command** → Cooling failure drill → fleet scan  
3. **Alert Center** → acknowledge a P1 alert  
4. **Maintenance Planner** → spare parts tab + CMMS JSON  
5. **Live Dashboard** → Machine #5 + compare mode  
6. Download **HTML report** from Fleet Command  
    """)

st.markdown("""
| Page | Purpose |
|------|---------|
| **🌐 Fleet Command** | Health map, heatmap, ROI, HTML report |
| **🚨 Alert Center** | Unified alerts, acknowledge workflow |
| **📈 Live Dashboard** | Sensors, compare, work orders |
| **🏛️ Historical** | Trends, shifts, timeline |
| **📅 Planner** | Gantt, CMMS, **spare parts** |
| **🔬 Model Insights** | Model card, drivers, heatmap |
""")

with st.expander("Model card"):
    if MODEL_PATH.exists():
        st.markdown(
            f"**{meta.get('trained', '—')}** · loss {meta.get('loss', '—')} · "
            f"{len(FEATURE_NAMES)} sensors"
        )
    else:
        st.error("Run `python train.py`")

open_alerts = database.get_alerts(10)
if not open_alerts.empty and kpis["critical"] > 0:
    st.warning(f"{kpis['critical']} critical asset(s) — open Alert Center for dispatch queue.")
