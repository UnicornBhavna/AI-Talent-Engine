import streamlit as st
import pandas as pd
import plotly.express as px
from datasets import load_dataset

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
    dataset = load_dataset("Bhavna1998/scored_output", split="train")
    return dataset.to_pandas()

df = load_data()

# -----------------------------
# SAFETY CHECKS
# -----------------------------

if df.empty:
    st.error("Dataset is empty or failed to load.")
    st.stop()

full_df = df.copy()

# -----------------------------
# CLEAN ONLY (NO NEW FEATURES)
# -----------------------------

if "tier" in full_df.columns:
    full_df["tier"] = full_df["tier"].astype(str).str.strip()

if "sex" in full_df.columns:
    full_df["sex"] = full_df["sex"].astype(str).str.strip().str.upper()

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------

st.sidebar.header("Filters")

st.sidebar.markdown("""
<div style="font-size:13px; font-style:italic; line-height:1.4">
Adjusts shortlist and chart view only. Does NOT change dataset-level KPIs.
</div>
""", unsafe_allow_html=True)

min_score = st.sidebar.slider("Minimum Score", 0, 100, 50)

# dynamic tiers from dataset (IMPORTANT FIX)
VALID_TIERS = sorted(full_df["tier"].dropna().unique().tolist())

tier_filter = st.sidebar.multiselect(
    "Tier Filter",
    VALID_TIERS,
    default=VALID_TIERS
)

gender_filter = st.sidebar.multiselect(
    "Gender Filter",
    ["M", "F"],
    default=["M", "F"]
)

# -----------------------------
# APPLY FILTERS (SAFE)
# -----------------------------

filtered = full_df.copy()

filtered = filtered[filtered["final_score"] >= min_score]

if "tier" in filtered.columns:
    filtered = filtered[filtered["tier"].isin(tier_filter)]

if "sex" in filtered.columns:
    filtered = filtered[filtered["sex"].isin(gender_filter)]

filtered = filtered.sort_values("final_score", ascending=False)

# -----------------------------
# KPI SECTION (FULL DATASET)
# -----------------------------

st.divider()
st.subheader("Dataset Overview")

total = len(full_df)
tier_counts = full_df["tier"].value_counts()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total", total)
col2.metric("Tier A", tier_counts.get("A", 0))
col3.metric("Tier B", tier_counts.get("B", 0))
col4.metric("Tier C + Below", tier_counts.get("C", 0) + tier_counts.get("Below", 0))

# -----------------------------
# TABLE
# -----------------------------

st.subheader("Ranked Shortlist (Filtered)")

display_cols = ["id", "full_name", "final_score", "tier", "sex"]
available_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(
    filtered[available_cols],
    use_container_width=True,
    height=500
)

# -----------------------------
# CHART
# -----------------------------

st.subheader("Score Distribution (Tier + Gender)")

plot_df = filtered.copy()

if "sex" in plot_df.columns:
    plot_df["tier_gender"] = plot_df["tier"] + " | " + plot_df["sex"]
else:
    plot_df["tier_gender"] = plot_df["tier"]

fig = px.histogram(
    plot_df,
    x="final_score",
    color="tier_gender",
    nbins=20,
    barmode="overlay"
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# EXPORT
# -----------------------------

st.download_button(
    "⬇ Download Filtered Shortlist",
    filtered.to_csv(index=False).encode("utf-8"),
    "shortlist.csv",
    "text/csv",
    help="Exports exactly what is shown in the filtered view."
)
