import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# CONFIG
# -----------------------------

st.set_page_config(
    page_title="Candidate Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# THEME
# -----------------------------

st.markdown("""
    <style>
        .main { background-color: white; color: black; }
        .stApp { background-color: white; }
        html, body, [class*="css"] {
            background-color: white !important;
            color: black !important;
        }
        .stMetric {
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------
# TITLE
# -----------------------------

st.markdown("""
<div style="font-size:14px; font-style:italic; font-weight:bold; line-height:1.4">
This dashboard ranks candidates based on AI-generated scoring pipeline and helps recruiters filter, compare, and export top candidates
</div>
""", unsafe_allow_html=True)

st.title("Candidate Intelligence Dashboard")
st.caption("AI-powered candidate ranking system for sourcing and screening")

# -----------------------------
# DATA LOADING
# -----------------------------

@st.cache_data
def load_data():
    return pd.read_csv("scored_output.csv")

df = load_data()

# -----------------------------
# SAFETY CHECKS
# -----------------------------

if df.empty:
    st.error("Dataset is empty or failed to load.")
    st.stop()

df["final_score"] = pd.to_numeric(df["final_score"], errors="coerce").fillna(0)

# -----------------------------
# FIX: NORMALIZE GENDER COLUMN (IMPORTANT)
# -----------------------------

if "sex" in df.columns:
    df["sex"] = df["sex"].astype(str).str.strip().str.upper()

# -----------------------------
# TIERING LOGIC
# -----------------------------

def assign_tier(score):
    if score >= 65:
        return "A"
    elif score >= 50:
        return "B"
    elif score >= 35:
        return "C"
    return "Below"

df["tier"] = df["final_score"].apply(assign_tier)

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------

st.sidebar.header("Filters")

st.sidebar.markdown("""
<div style="font-size:13px; line-height:1.4; font-style:italic">
Adjusts which candidates appear in the shortlist and chart based on score threshold and tier selection, without affecting overall dataset metrics.
</div>
""", unsafe_allow_html=True)

min_score = st.sidebar.slider("Minimum Score", 0, 100, 50)

st.sidebar.markdown("""
<div style="font-size:13px; line-height:1.4; font-style:italic">
<b>Score Bands</b><br><br>
• <b>Tier A</b> → top ~35% scores (high-confidence, strongest profiles)<br>
• <b>Tier B</b> → next strong cohort (competitive but not elite)<br>
• <b>Tier C</b> → mid-range candidates with mixed signals<br>
• <b>Below</b> → low-fit or weak signal profiles<br>
</div>
""", unsafe_allow_html=True)

tier_filter = st.sidebar.multiselect(
    "Tier Filter",
    ["A", "B", "C", "Below"],
    default=["A", "B", "C"]
)

st.sidebar.markdown("""
<div style="font-size:13px; line-height:1.4; font-style:italic">
Filters candidates by gender field present in the dataset (used only for segmentation, not scoring).
</div>
""", unsafe_allow_html=True)

gender_filter = st.sidebar.multiselect(
    "Gender Filter",
    ["M", "F"],
    default=["M", "F"]
)

# -----------------------------
# APPLY FILTERS
# -----------------------------

filtered = df[df["final_score"] >= min_score]
filtered = filtered[filtered["tier"].isin(tier_filter)]

if "sex" in df.columns:
    filtered = filtered[filtered["sex"].isin(gender_filter)]

filtered = filtered.sort_values("final_score", ascending=False)

# -----------------------------
# KPI SECTION (FULL DATASET)
# -----------------------------

st.divider()
st.subheader("Dataset Overview")

total = len(df)
tier_counts = df["tier"].value_counts()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total", total)
col2.metric("Tier A", f"{(tier_counts.get('A',0)/total)*100:.1f}%")
col3.metric("Tier B", f"{(tier_counts.get('B',0)/total)*100:.1f}%")
col4.metric("Tier C + Below", f"{((tier_counts.get('C',0)+tier_counts.get('Below',0))/total)*100:.1f}%")

# -----------------------------
# TABLE
# -----------------------------

st.subheader("Ranked Shortlist")

display_cols = ["id", "full_name", "final_score", "tier"]
available_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(
    filtered[available_cols],
    use_container_width=True,
    height=500
)

# -----------------------------
# CHART
# -----------------------------

st.subheader("Score Distribution (Filtered View)")

fig = px.histogram(
    filtered,
    x="final_score",
    color="tier",
    nbins=20,
    barmode="overlay"
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# EXPORT
# -----------------------------

csv = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇ Download Filtered Shortlist",
    csv,
    "shortlist.csv",
    "text/csv"
)