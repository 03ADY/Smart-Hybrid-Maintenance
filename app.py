"""PredictiveOps Enterprise — navigation router."""

import streamlit as st

from maintenance.bootstrap import init_app
from maintenance.config import APP_NAME
from maintenance.theme import inject_theme

st.set_page_config(page_title=APP_NAME, page_icon="⚙️", layout="wide")
inject_theme()
init_app()

PAGES = [
    st.Page("views/dashboard.py", title="Dashboard", icon="🏠", default=True),
    st.Page("pages/0_🌐_Fleet_Command_Center.py", title="Fleet Command", icon="🌐"),
    st.Page("pages/5_🚨_Alert_Center.py", title="Alert Center", icon="🚨"),
    st.Page("pages/1_📈_Live_Dashboard.py", title="Live Dashboard", icon="📈"),
    st.Page("pages/2_🏛️_Historical_Explorer.py", title="Historical", icon="🏛️"),
    st.Page("pages/3_📅_Maintenance_Planner.py", title="Maintenance Planner", icon="📅"),
    st.Page("pages/4_🔬_Model_Insights.py", title="Model Insights", icon="🔬"),
]

pg = st.navigation(PAGES)
pg.run()
