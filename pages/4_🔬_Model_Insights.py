"""Model transparency, driver aggregates, fleet heatmap."""

import plotly.express as px
import streamlit as st

import database
from maintenance.analytics import aggregate_drivers, fleet_health_heatmap, shift_comparison
from maintenance.bootstrap import init_app, model_metadata, render_demo_sidebar
from maintenance.config import APP_NAME, FEATURE_NAMES, MODEL_PATH

from maintenance.theme import page_setup

page_setup("Model Insights", "🔬")
init_app()
st.title("🔬 Model & Fleet Analytics")
render_demo_sidebar()

meta = model_metadata()
hist = database.get_fleet_history(2000)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Last trained", meta.get("trained", "—"))
c2.metric("Training loss", meta.get("loss", "—"))
c3.metric("Epochs", meta.get("epochs", "—"))
c4.metric("Records analyzed", len(hist))

with st.expander("Model card", expanded=True):
    st.markdown(f"""
- **Architecture:** LSTM(50) → Dense(25) → Dense(1)
- **Input window:** {meta.get('sequence_length', 100)} timesteps × {meta.get('feature_dim', 10)} sensors
- **Sensors:** {', '.join(FEATURE_NAMES)}
- **Trained:** {meta.get('trained', '—')}
- **Artifact:** `{MODEL_PATH.name}` ({'found' if MODEL_PATH.exists() else 'missing — run train.py'})
    """)
    st.caption("Health score = 1 / (1 + LSTM vibration forecast error). Demo metric — not plant-certified.")

tab1, tab2, tab3 = st.tabs(["🌡️ Fleet heatmap", "📊 Top drivers", "🕐 Shift compare"])

with tab1:
    heat = fleet_health_heatmap(hist)
    if heat.empty:
        st.info("Run fleet scans to build hourly health heatmap.")
    else:
        st.plotly_chart(
            px.imshow(heat, labels=dict(x="Hour", y="Machine", color="Health"), aspect="auto", color_continuous_scale="RdYlGn"),
            use_container_width=True,
        )

with tab2:
    drivers = aggregate_drivers(hist)
    if drivers.empty:
        st.info("No driver history yet.")
    else:
        st.plotly_chart(px.bar(drivers, x="sensor", y="avg_driver", title="Avg driver weights (fleet)"), use_container_width=True)

with tab3:
    if not hist.empty:
        import pandas as pd
        h = hist.copy()
        h["timestamp"] = pd.to_datetime(h["timestamp"])
        for mid in sorted(h["machine_id"].unique())[:5]:
            sc = shift_comparison(h[h["machine_id"] == mid])
            if sc:
                st.markdown(
                    f"**Machine #{mid}** — Day {sc['day_shift']:.0%} vs Night {sc['night_shift']:.0%} "
                    f"(Δ {sc['delta']:+.1%})"
                )
    else:
        st.info("Need historical data for shift analysis.")

st.caption(APP_NAME)
