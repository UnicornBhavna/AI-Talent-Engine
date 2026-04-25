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
# THEME (UI LAYER ONLY)
# -----------------------------
"""
WHY:
- Keeps UI visually consistent
- Ensures analytics view is readable for recruiters
- No impact on logic or scoring
"""

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
# DATA LOADING (HUGGING FACE)
# -----------------------------
"""
WHY THIS APPROACH:
- Uses HF dataset as single source of truth
- Avoids local file dependency (Streamlit Cloud safe)
- Ensures reproducibility across environments

LIMITATION:
- Requires dataset repo to be public OR authenticated
- Assumes dataset has a default 'train' split
"""

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

if "final_score" not in df.columns:
    st.error("Missing required column: final_score")
    st.stop()

# -----------------------------
# TIERING LOGIC
# -----------------------------
"""
WHY:
- Converts continuous score into interpretable recruiter buckets
- Enables filtering + segmentation in UI
- Makes ranking explainable
"""

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
# DIVERSITY FLAG EXTRACTION
# -----------------------------
"""
WHY:
- Extracts structured demographic signal safely
- Prevents runtime crashes from malformed HF data

LIMITATION:
- This is heuristic-based upstream output
- Should NOT be used for decision-making or ranking
"""

def extract_female(x):
    if isinstance(x, dict):
        return x.get("is_female", False)
    return False

df["is_female"] = df["diversity_flag"].apply(extract_female) if "diversity_flag" in df.columns else False

# -----------------------------
# SIDEBAR CONTROLS
# -----------------------------

st.sidebar.header("Filters")

st.sidebar.markdown("""
Use filters to refine candidate shortlist.
All metrics are derived from precomputed scoring pipeline.
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
    help="Uses heuristic gender proxy (low confidence, non-decision feature)."
)

# -----------------------------
# APPLY FILTERS
# -----------------------------
"""
WHY:
- Ensures filtering does NOT modify original dataset
- Keeps UI state independent of underlying data
"""

filtered = df[df["final_score"] >= min_score]
filtered = filtered[filtered["tier"].isin(tier_filter)]

if diversity_only:
    filtered = filtered[filtered["is_female"] == True]

filtered = filtered.sort_values("final_score", ascending=False)

# -----------------------------
# KPI SECTION
# -----------------------------
"""
WHY:
- Shows full dataset distribution (not filtered view)
- Helps understand pipeline bias and tier spread
"""

st.divider()
st.subheader("Dataset Overview")

total = len(df)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Candidates", total)
col2.metric("Tier A", len(df[df["tier"] == "A"]))
col3.metric("Tier B", len(df[df["tier"] == "B"]))
col4.metric("Tier C + Below", len(df[df["tier"].isin(["C", "Below"])]))

# -----------------------------
# TABLE VIEW
# -----------------------------

st.subheader("Ranked Shortlist")

st.markdown("""
This table shows filtered candidates ranked by AI score.

Signals used upstream:
- Employer tier (IB / PE / Hedge Fund proxy)
- Returnee signal (geographic + education heuristic)
- Experience alignment
- Education quality proxy
""")

display_cols = [
    "id",
    "full_name",
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
# VISUALIZATION
# -----------------------------

st.subheader("Score Distribution")

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
    "text/csv",
    help="Exports current filtered dataset for offline analysis or recruiter use."
)
