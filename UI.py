import streamlit as st
import pandas as pd
import plotly.express as px
from datasets import load_dataset
import plotly.graph_objects as go
import numpy as np
import ast
import streamlit as st

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
This dashboard ranks candidates based on a scoring pipeline and helps recruiters filter, compare, and export top candidates
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
    df = dataset.to_pandas()

    # -----------------------------
    # FIX: Parse structured columns
    # -----------------------------
    cols_to_parse = ["countries", "experience", "education", "score_breakdown"]

    for col in cols_to_parse:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )

    # -----------------------------
    # FIX: Clean null-like values
    # -----------------------------
    df = df.fillna("")

    return df


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
Sets the minimum AI score threshold; only candidates above this score appear in the shortlist and charts.
</div>
""", unsafe_allow_html=True)

min_score = st.sidebar.slider("Minimum Score", 0, 100, 0)

st.sidebar.markdown("""
<div style="font-size:13px; font-style:italic; line-height:1.5">

<b>Tier Definition (Based on AI Score)</b><br><br>

• <b>Tier A</b> → final_score ≥ 75 (elite candidates)<br>
• <b>Tier B</b> → 60–74 (strong candidates)<br>
• <b>Tier C</b> → 50–59 (mid-range candidates)<br>
• <b>Below</b> → < 50 (low-fit candidates)<br>

</div>
""", unsafe_allow_html=True)

tier_filter = st.sidebar.multiselect(
    "Tier Filter",
    sorted(full_df["tier"].dropna().unique().tolist()) if "tier" in full_df.columns else [],
    default=sorted(full_df["tier"].dropna().unique().tolist()) if "tier" in full_df.columns else []
)

st.sidebar.markdown("""
<div style="font-size:13px; font-style:italic; line-height:1.4">
Filters candidates by gender for segmentation analysis; does not influence scoring or ranking.
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

col1, col2, col3, col4, col5 = st.columns(5)

col5.metric("Total Candidates", total)

col1.metric("Tier A", f"{(tier_counts.get('A',0)/total)*100:.1f}%")
col2.metric("Tier B", f"{(tier_counts.get('B',0)/total)*100:.1f}%")
col3.metric("Tier C", f"{(tier_counts.get('C',0)/total)*100:.1f}%")
col4.metric("Below", f"{(tier_counts.get('Below',0)/total)*100:.1f}%")

# -----------------------------
# TABLE (FILTERED)
# -----------------------------
st.subheader("Filtered Data")

#display_cols = ["id", "full_name", "final_score", "tier", "sex"]
#available_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(
    filtered,   #[available_cols],
    use_container_width=True,
    height=500
)


# -----------------------------
# Visual
# -----------------------------

st.subheader("Filtered Data Visualisation")

plot_df = filtered.copy()

# CREATE SCORE BINS
bins = list(range(0, 101, 10))

plot_df["score_bin"] = pd.cut(
    plot_df["final_score"],
    bins=bins,
    include_lowest=True
)

bin_index = plot_df["score_bin"].cat.categories

# PIVOT TABLES
tier_pivot = pd.crosstab(plot_df["score_bin"], plot_df["tier"]).reindex(columns=["A", "B", "C", "Below"], fill_value=0)
gender_pivot = pd.crosstab(plot_df["score_bin"], plot_df["sex"]).reindex(columns=["M", "F"], fill_value=0)

# X axis
x_vals = tier_pivot.index.astype(str)

# FIGURE
fig = go.Figure()

# TIER (Y1 - STACKED BARS)
for tier in ["A", "B", "C", "Below"]:
    fig.add_trace(go.Bar(
        x=x_vals,
        y=tier_pivot[tier],
        name=f"Tier {tier}"
    ))

# GENDER (Y2 - LINES)
for gender in ["M", "F"]:
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=gender_pivot[gender],
        name=f"Gender {gender}",
        mode="lines+markers",
        yaxis="y2"
    ))

# LAYOUT (DUAL AXIS)
fig.update_layout(
    barmode="stack",

    xaxis=dict(title="Score Bins"),

    yaxis=dict(
        title="Tier Count"
    ),

    yaxis2=dict(
        title="Gender Count",
        overlaying="y",
        side="right"
    ),

    legend=dict(title="Legend"),
    height=650
)

st.plotly_chart(fig, use_container_width=True)


# -----------------------------
# EXPORT
# -----------------------------

export_df = filtered[
    [
        "full_name",
        "current_title + employer",
        "current_location",
        "employer_tier",
        "total_score",
        "score_breakdown",
        "shortlist_tier",
        "diversity_flag",
        "linkedin_url",
        "score_rationale"
    ]
]

st.download_button(
    "⬇ Download Filtered Shortlist",
    export_df.to_csv(index=False).encode("utf-8"),
    "shortlist.csv",
    "text/csv",
    help="Exports only required columns in correct format"
)
