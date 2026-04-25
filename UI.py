import streamlit as st
import pandas as pd
import plotly.express as px
from datasets import load_dataset

# -----------------------------
# STREAMLIT CONFIG (MUST BE FIRST)
# -----------------------------

st.set_page_config(
    page_title="Candidate Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# THEME (CLEAN WHITE UI)
# -----------------------------

st.markdown("""
    <style>
        .main {
            background-color: white;
            color: black;
        }

        .stApp {
            background-color: white;
        }

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

st.title("Candidate Intelligence Dashboard")
st.caption("AI-powered sourcing analytics for talent screening and ranking")

# -----------------------------
# DATA LOADING
# -----------------------------

@st.cache_data
def load_data():
    dataset = load_dataset("Bhavna1998/scored_output", split="train")
    return dataset.to_pandas()

df = load_data()

if df.empty:
    st.error("Dataset is empty or failed to load.")
    st.stop()

if "final_score" not in df.columns:
    st.error("Missing required column: final_score")
    st.stop()
    

# -----------------------------
# TIERING
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
# SAFE FEMALE FLAG EXTRACTION
# -----------------------------

def extract_female(x):
    if isinstance(x, dict):
        return x.get("is_female", False)
    return False

if "diversity_flag" in df.columns:
    df["is_female"] = df["diversity_flag"].apply(extract_female)
else:
    df["is_female"] = False

# -----------------------------
# SIDEBAR CONTROLS
# -----------------------------

st.sidebar.header("Filters")

st.sidebar.markdown("""
Use filters to refine candidate shortlist.
All metrics above remain constant for dataset comparison.
""")

min_score = st.sidebar.slider(
    "Minimum Score (0–100)",
    0, 100, 50,
    help="Filters out candidates below this AI composite score threshold."
)

tier_filter = st.sidebar.multiselect(
    "Tier Filter",
    ["A", "B", "C", "Below"],
    default=["A", "B", "C"]
)

diversity_only = st.sidebar.checkbox(
    "Diversity Only (Female candidates)",
    help="Filters candidates flagged as female using heuristic signal (low confidence)."
)

# -----------------------------
# APPLY FILTERS (VIEW DATA ONLY)
# -----------------------------

filtered = df[df["final_score"] >= min_score]
filtered = filtered[filtered["tier"].isin(tier_filter)]

if diversity_only:
    filtered = filtered[filtered["is_female"] == True]

filtered = filtered.sort_values("final_score", ascending=False)

# -----------------------------
# KPI SECTION (CONSTANT - FULL DATASET)
# -----------------------------

st.divider()
st.subheader("Dataset Overview")

total = len(df)

tier_a = df[df["tier"] == "A"]
tier_b = df[df["tier"] == "B"]
tier_c = df[df["tier"] == "C"]
tier_below = df[df["tier"] == "Below"]

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total", f"{total}")

col2.metric("Tier A", f"{len(tier_a)/total:.1%}")
col3.metric("Tier B", f"{len(tier_b)/total:.1%}")
col4.metric("Tier C", f"{len(tier_c)/total:.1%}")
col5.metric("Below", f"{len(tier_below)/total:.1%}")

# -----------------------------
# TABLE
# -----------------------------

st.subheader("Ranked Shortlist")

st.markdown("""
This table shows **filtered candidates only**, ranked by AI score.
Higher scores indicate stronger fit based on:
- Employer tier
- Returnee signal
- Experience fit
- Education quality
""")

display_cols = [
    "candidate_id",
    "final_score",
    "tier",
    "is_female"
]

available_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(
    filtered[available_cols],
    use_container_width=True,
    height=500
)

# -----------------------------
# HISTOGRAM (FILTER-AWARE)
# -----------------------------

st.subheader("Score Distribution (Filtered View)")

fig = px.histogram(
    filtered,
    x="final_score",
    color="tier",
    nbins=20,
    barmode="overlay",
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
    "text/csv",
    help="Downloads the currently filtered candidate shortlist including score, tier, and flags for offline analysis or reporting."
)
