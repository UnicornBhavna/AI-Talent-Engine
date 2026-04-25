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
full_df = df.copy()

# -----------------------------
# CLEANING (SAFE ONLY)
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
Adjusts shortlist and charts only. Does NOT affect dataset-level KPIs.
</div>
""", unsafe_allow_html=True)

min_score = st.sidebar.slider("Minimum Score", 0, 100, 50)

tier_filter = st.sidebar.multiselect(
    "Tier Filter",
    sorted(full_df["tier"].dropna().unique().tolist()) if "tier" in full_df.columns else [],
    default=sorted(full_df["tier"].dropna().unique().tolist()) if "tier" in full_df.columns else []
)

gender_filter = st.sidebar.multiselect(
    "Gender Filter",
    ["M", "F"],
    default=["M", "F"]
)

# -----------------------------
# APPLY FILTERS
# -----------------------------
filtered = full_df.copy()

if "final_score" in filtered.columns:
    filtered = filtered[filtered["final_score"] >= min_score]

if "tier" in filtered.columns:
    filtered = filtered[filtered["tier"].isin(tier_filter)]

if "sex" in filtered.columns:
    filtered = filtered[filtered["sex"].isin(gender_filter)]

filtered = filtered.sort_values("final_score", ascending=False)

# -----------------------------
# KPI SECTION (PERCENTAGES)
# -----------------------------
st.divider()
st.subheader("Dataset Overview")

total = len(full_df)
tier_counts = full_df["tier"].value_counts() if "tier" in full_df.columns else {}

col1, col2, col3, col4 = st.columns(4)

col1.metric("Tier A", f"{(tier_counts.get('A',0)/total)*100:.1f}%")
col2.metric("Tier B", f"{(tier_counts.get('B',0)/total)*100:.1f}%")
col3.metric("Tier C", f"{(tier_counts.get('C',0)/total)*100:.1f}%")
col4.metric("Below", f"{(tier_counts.get('Below',0)/total)*100:.1f}%")

# -----------------------------
# TABLE (FILTERED)
# -----------------------------
st.subheader("Ranked Shortlist")

display_cols = ["id", "full_name", "final_score", "tier", "sex"]
available_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(
    filtered[available_cols],
    use_container_width=True,
    height=500
)

st.subheader("Tier Distribution with Gender Overlay")

import plotly.graph_objects as go

plot_df = full_df.copy()

# jitter so points don't overlap perfectly
plot_df["jitter"] = plot_df["final_score"] + (plot_df["sex"].map({"M": -0.5, "F": 0.5}).fillna(0))

fig = go.Figure()

st.subheader("Tier Distribution + Gender Overlay (Dual Axis)")

import plotly.graph_objects as go

plot_df = full_df.copy()

# -----------------------------
# TIER COUNTS (HISTOGRAM DATA)
# -----------------------------
tier_counts = plot_df["tier"].value_counts().reset_index()
tier_counts.columns = ["tier", "count"]

# -----------------------------
# GENDER COUNTS
# -----------------------------
gender_counts = plot_df["sex"].value_counts().reset_index()
gender_counts.columns = ["sex", "count"]

st.subheader("Score Distribution: Tier vs Gender (Dual Axis)")

import numpy as np
import plotly.graph_objects as go

plot_df = full_df.copy()

# -----------------------------
# CREATE SCORE BINS
# -----------------------------
bins = list(range(0, 101, 5))  # 0-100 in steps of 5
plot_df["score_bin"] = pd.cut(plot_df["final_score"], bins=bins)

bin_centers = [interval.mid for interval in plot_df["score_bin"].cat.categories]

# -----------------------------
# TIER COUNTS PER BIN (Y1)
# -----------------------------
tier_pivot = plot_df.groupby(["score_bin", "tier"]).size().unstack(fill_value=0)

# -----------------------------
# GENDER COUNTS PER BIN (Y2)
# -----------------------------
gender_pivot = plot_df.groupby(["score_bin", "sex"]).size().unstack(fill_value=0)

# -----------------------------
# FIGURE
# -----------------------------
fig = go.Figure()

# --- Tier (Y1: bars stacked feel via multiple traces)
for tier in ["A", "B", "C", "Below"]:
    if tier in tier_pivot.columns:
        fig.add_trace(go.Bar(
            x=bin_centers,
            y=tier_pivot[tier],
            name=f"Tier {tier}",
            opacity=0.7
        ))

# --- Gender (Y2: line plot)
for gender in ["M", "F"]:
    if gender in gender_pivot.columns:
        fig.add_trace(go.Scatter(
            x=bin_centers,
            y=gender_pivot[gender],
            name=f"Gender {gender}",
            mode="lines+markers",
            yaxis="y2"
        ))

# -----------------------------
# LAYOUT (DUAL AXIS)
# -----------------------------
fig.update_layout(
    barmode="stack",
    xaxis=dict(title="Score (Binned)"),

    yaxis=dict(
        title="Tier Count"
    ),

    yaxis2=dict(
        title="Gender Count",
        overlaying="y",
        side="right"
    ),

    legend=dict(title="Legend"),
    height=550
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
    help="Exports exactly what is shown in filtered view"
)
