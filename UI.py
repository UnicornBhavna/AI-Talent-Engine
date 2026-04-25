"""
Analytics Dashboard

Responsibilities:
1. Load precomputed candidates.csv
2. Apply tiering + filtering
3. Provide interactive shortlist view
4. Export results to CSV

Design:
- Stateless UI layer
- No scoring logic (precomputed pipeline output)
- Safe handling of missing/malformed data
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

# -----------------------------
# STREAMLIT CONFIG (MUST BE FIRST)
# -----------------------------

st.set_page_config(
    page_title="Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# THEME (OPTIONAL UI UPGRADE)
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

        html, body, [class*="css"]  {
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
st.caption("AI-powered sourcing analytics for Global Investment & Strategic Research")

# -----------------------------
# DATA LOADING
# -----------------------------

@st.cache_data
def load_data():
    try:
        return pd.read_csv("scored_output.csv")
    except Exception:
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("scored_output.csv not found or empty. Run pipeline first.")
    st.stop()

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

if "final_score" not in df.columns:
    st.error("Missing required column: final_score")
    st.stop()

df["tier"] = df["final_score"].apply(assign_tier)

# -----------------------------
# SAFE COLUMN HANDLING
# -----------------------------

df["company_tier"] = df["employer"].apply(
    lambda x: x.get("tier") if isinstance(x, dict) else None
) if "employer" in df.columns else None

df["returnee_score"] = df["returnee_signal"].apply(
    lambda x: x.get("score") if isinstance(x, dict) else 0
) if "returnee_signal" in df.columns else 0

df["is_female"] = df["diversity_flag"].apply(
    lambda x: x.get("is_female") if isinstance(x, dict) else False
) if "diversity_flag" in df.columns else False

# -----------------------------
# FILTERS
# -----------------------------

st.sidebar.header("Controls")

st.sidebar.markdown("""
**How to use:**
- Filter and rank candidates from the AI scoring pipeline
- Adjust thresholds to refine shortlist quality
""")

st.sidebar.markdown("""
**Tier definitions:**
- **A:** Top-tier (elite firms / strongest returnee + profile match)
- **B:** Strong candidates (good firms + solid signals)
- **C:** Moderate fit (mixed signals)
- **Below:** Low relevance to mandate
""")

st.sidebar.markdown("**Minimum Score**: Filters out low-fit candidates based on AI composite scoring (0–100).")

min_score = st.sidebar.slider("Minimum Score", 0, 100, 50)

tier_filter = st.sidebar.multiselect(
    "Tier Filter",
    ["A", "B", "C", "Below"],
    default=["A", "B", "C"]
)

diversity_only = st.sidebar.checkbox("Diversity Only (Female flagged)")

st.sidebar.caption(
    "When enabled, shows only candidates inferred as female using heuristic name-based signals (low confidence proxy)."
)

# -----------------------------
# APPLY FILTERS
# -----------------------------

filtered = df[df["final_score"] >= min_score]
filtered = filtered[filtered["tier"].isin(tier_filter)]

if diversity_only and "is_female" in df.columns:
    filtered = filtered[filtered["is_female"] == True]

filtered = filtered.sort_values("final_score", ascending=False)

# -----------------------------
# KPI METRICS
# -----------------------------

st.divider()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Candidates", len(df))
col2.metric("Tier A", len(df[df["tier"] == "A"]))
col3.metric("Tier B", len(df[df["tier"] == "B"]))
col4.metric("Filtered Output", len(filtered))

st.divider()

# -----------------------------
# TABLE OUTPUT
# -----------------------------

st.subheader("Ranked Shortlist")

st.markdown("""
This table shows **AI-ranked candidates** based on:
- Employer quality (investment banking / PE / hedge fund tiering)
- Returnee signal strength (Asia linkage probability)
- Experience alignment
- Education quality proxy

Sorted from highest to lowest overall score.
""")

display_cols = [
    "candidate_id",
    "final_score",
    "tier",
    "returnee_score",
    "is_female"
]

available_cols = [c for c in display_cols if c in filtered.columns]

st.subheader("Score Distribution Overview")

st.markdown("""
This histogram shows the distribution of candidate scores across the dataset.
It helps identify how selective the pipeline is and where candidates cluster.
""")

# -----------------------------
# EXPORT
# -----------------------------

csv = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇ Download Shortlist CSV",
    csv,
    "shortlist.csv",
    "text/csv"
)

# -----------------------------
# INSIGHT VISUALIZATION
# -----------------------------

st.subheader("Score Distribution")

fig = px.histogram(
    df,
    x="final_score",
    color="tier",
    nbins=20,
    barmode="overlay"
)

st.plotly_chart(fig, use_container_width=True)

