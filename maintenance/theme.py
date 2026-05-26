"""PredictiveOps — dark enterprise Streamlit theme."""

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

ACCENT = ("#0f766e", "#0369a1")
PRIMARY = "#2dd4bf"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
  font-family: 'Inter', system-ui, sans-serif !important;
}

/* Full app canvas — fixes white main area on Cloud */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
section[data-testid="stMain"],
.main,
.main > div {
  background-color: #0b1120 !important;
  color: #f1f5f9 !important;
}

.block-container {
  padding-top: 1.25rem;
  max-width: 1400px;
  background-color: transparent !important;
}

[data-testid="stHeader"] {
  background-color: rgba(11, 17, 32, 0.92) !important;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
}

section[data-testid="stMain"] h1,
section[data-testid="stMain"] h2,
section[data-testid="stMain"] h3,
section[data-testid="stMain"] h4,
section[data-testid="stMain"] p,
section[data-testid="stMain"] li,
section[data-testid="stMain"] [data-testid="stMarkdownContainer"] p {
  color: #e2e8f0 !important;
}

.ep-hero {
  background: linear-gradient(135deg, ACCENT_A, ACCENT_B);
  padding: 1.75rem 2rem;
  border-radius: 16px;
  margin-bottom: 1.25rem;
  color: #fff !important;
  box-shadow: 0 16px 48px rgba(15, 118, 110, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.08);
}
.ep-hero h1, .ep-hero p { color: #fff !important; }
.ep-hero h1 { margin: 0; font-size: 1.85rem; font-weight: 700; }
.ep-hero p { margin: 0.5rem 0 0; opacity: 0.92; }

/* KPI / OEE metric row */
div[data-testid="stMetric"] {
  background: rgba(30, 41, 59, 0.92) !important;
  border: 1px solid rgba(148, 163, 184, 0.18) !important;
  border-radius: 12px !important;
  padding: 0.75rem 0.6rem !important;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);
}
div[data-testid="stMetricLabel"] p,
div[data-testid="stMetricLabel"] {
  color: #94a3b8 !important;
  font-size: 0.78rem !important;
}
div[data-testid="stMetricValue"],
div[data-testid="stMetricDelta"] {
  color: #f8fafc !important;
}

/* Sidebar — force dark background + light text (Streamlit nests white layers) */
section[data-testid="stSidebar"],
div[data-testid="stSidebar"],
div[data-testid="stSidebar"] > div,
[data-testid="stSidebarContent"],
[data-testid="stSidebarUserContent"],
[data-testid="stSidebarNav"],
[data-testid="stSidebarNav"] > ul {
  background-color: #0f172a !important;
  background-image: linear-gradient(180deg, #0f172a 0%, #134e4a 100%) !important;
  color: #f1f5f9 !important;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
  color: #e2e8f0 !important;
}

/* Multipage navigation links */
[data-testid="stSidebarNav"] a,
[data-testid="stSidebarNav"] span,
[data-testid="stSidebarNav"] li {
  color: #cbd5e1 !important;
}
[data-testid="stSidebarNav"] a[aria-current="page"] {
  background-color: rgba(45, 212, 191, 0.18) !important;
  color: #2dd4bf !important;
  font-weight: 600 !important;
}

/* Inputs in sidebar */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
  background-color: #1e293b !important;
  color: #f8fafc !important;
  border-color: rgba(148, 163, 184, 0.35) !important;
}

[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] .stSlider [data-testid="stTickBarMin"],
[data-testid="stSidebar"] .stSlider [data-testid="stTickBarMax"] {
  color: #94a3b8 !important;
}

[data-testid="stSidebar"] .stButton > button {
  background: linear-gradient(135deg, ACCENT_A, ACCENT_B) !important;
  color: #ffffff !important;
  border: none !important;
  font-weight: 600 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  border-color: #2dd4bf !important;
  color: #ffffff !important;
}

[data-testid="stSidebar"] [data-testid="stExpander"] {
  background-color: rgba(30, 41, 59, 0.85) !important;
  border: 1px solid rgba(148, 163, 184, 0.2) !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary p,
[data-testid="stSidebar"] [data-testid="stExpander"] svg {
  color: #e2e8f0 !important;
  fill: #e2e8f0 !important;
}

[data-testid="stSidebar"] hr {
  border-color: rgba(148, 163, 184, 0.25) !important;
}

[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stRadio label p,
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
  color: #e2e8f0 !important;
}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label {
  background-color: rgba(30, 41, 59, 0.65) !important;
  border: 1px solid rgba(148, 163, 184, 0.2) !important;
  border-radius: 8px !important;
}

div[data-testid="stExpander"] {
  background-color: rgba(30, 41, 59, 0.75) !important;
  border: 1px solid rgba(148, 163, 184, 0.15) !important;
  border-radius: 12px !important;
}

[data-testid="stDataFrame"],
.stDataFrame {
  background-color: rgba(30, 41, 59, 0.5) !important;
}

/* Quick nav page links */
a[data-testid="stPageLink-NavLink"] {
  background: rgba(30, 41, 59, 0.9) !important;
  border: 1px solid rgba(45, 212, 191, 0.25) !important;
  border-radius: 10px !important;
  padding: 0.5rem !important;
}
a[data-testid="stPageLink-NavLink"]:hover {
  border-color: PRIMARY !important;
}

.ep-fleet-card {
  text-align: center;
  padding: 0.65rem;
  border-radius: 10px;
  background: rgba(30, 41, 59, 0.92);
  color: #e2e8f0;
  border: 2px solid var(--fleet-color, #2dd4bf);
}

.stTabs [data-baseweb="tab"] {
  border-radius: 10px;
  background: rgba(30, 41, 59, 0.6);
  color: #e2e8f0;
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, ACCENT_A, ACCENT_B) !important;
  color: #fff !important;
}

hr { border-color: rgba(148, 163, 184, 0.2) !important; }
</style>
""".replace("ACCENT_A", ACCENT[0]).replace("ACCENT_B", ACCENT[1]).replace("PRIMARY", PRIMARY)


def inject_theme() -> None:
    try:
        pio.templates.default = "plotly_dark"
    except (KeyError, ValueError):
        pass
    st.markdown(_CSS, unsafe_allow_html=True)


def page_setup(page_title: str, page_icon: str = "⚙️", layout: str = "wide") -> None:
    """Must be the first Streamlit call on each page."""
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)
    inject_theme()


def hero_html(title: str, subtitle: str, icon: str = "") -> str:
    return f'<div class="ep-hero"><h1>{icon} {title}</h1><p>{subtitle}</p></div>'


def fleet_card_html(machine_id: int, score: float, color: str) -> str:
    return (
        f'<div class="ep-fleet-card" style="--fleet-color:{color}; border-color:{color};">'
        f'<b>#{machine_id}</b><br>'
        f'<span style="color:{color};font-size:1.2rem;font-weight:600;">{score:.0%}</span></div>'
    )


def style_fig(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.5)",
        font=dict(color="#e2e8f0"),
    )
    return fig
