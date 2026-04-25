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

df["final_score"] = pd.to_numeric(df["final_score"], errors="coerce").fillna(0)

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

# IMPORTANT: clean + normalize gender
if "sex" in df.columns:
    df["sex"] = df["sex"].astype(str).str.upper().str.strip()
    df.loc[~df["sex"].isin(["M", "F"]), "sex"] = "U"

full_df = df.copy()

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

tier_filter = st.sidebar.multiselect(
    "Tier Filter",
    ["A", "B", "C", "Below"],
    default=["A", "B", "C"]
)

gender_filter = st.sidebar.multiselect(
    "Gender Filter",
    ["M", "F"],
    default=["M", "F"]
)

# -----------------------------
# APPLY FILTERS (SOURCE OF TRUTH)
# -----------------------------

filtered = full_df.copy()

filtered = filtered[
    (filtered["final_score"] >= min_score) &
    (filtered["tier"].isin(tier_filter))
]

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
col2.metric("Tier A", f"{(tier_counts.get('A',0)/total)*100:.1f}%")
col3.metric("Tier B", f"{(tier_counts.get('B',0)/total)*100:.1f}%")
col4.metric("Tier C + Below", f"{((tier_counts.get('C',0)+tier_counts.get('Below',0))/total)*100:.1f}%")

# -----------------------------
# TABLE (FILTERED)
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
# CHART (FILTERED + GENDER INCLUDED)
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
    barmode="overlay",
    category_orders={
        "tier_gender": [
            "A | M", "A | F",
            "B | M", "B | F",
            "C | M", "C | F",
            "Below | M", "Below | F"
        ]
    }
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# EXPORT (FILTERED ONLY)
# -----------------------------

st.download_button(
    "⬇ Download Filtered Shortlist",
    filtered.to_csv(index=False).encode("utf-8"),
    "shortlist.csv",
    "text/csv",
    help="Exports exactly what is shown in the filtered view."
)
