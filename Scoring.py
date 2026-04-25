"""
Core functions:
- classify_employer
- detect_returnee_signal
- detect_diversity_flag
- score_candidate

Design notes:
- Fully defensive against missing fields
- Uses lightweight heuristics (no external ML dependency)
- Returns explainable score breakdown for downstream ranking
"""

from difflib import SequenceMatcher
from typing import Dict, Any
import re
import pandas as pd

# -----------------------------
# CONFIGURATION
# -----------------------------

EMPLOYER_TIERS = {
    "tier_1_ib": [
        "goldman sachs", "morgan stanley", "jpmorgan", "jp morgan", "Bank of America",
        "ubs", "barclays", "deutsche bank"
    ],
    "tier_2_ib": [ "blackrock", "Fidelity investments", 'wellington', "Schroders",
        "hsbc", "standard chartered", "nomura", "mizuho", "rbc",
         "bofa", "citi", "T. Rowe Price"
    ],
    "pe_hedge_top": [
        "blackstone", "kkr", "carlyle", "apollo", "brookfield",
        "bridgewater", "renaissance technologies", "BCG", "Bain", "BCN"
    ]
}

ASIA_KEYWORDS = {
    "singapore", "hong kong", "shanghai", "beijing", "mumbai", "Japan",
    "bengaluru", "jakarta", "kuala lumpur", "seoul", "tokyo", "India",
    "China", "Taiwan", "Malaysia", "Thailand", "Bangkok", "Indonesia"
}

ASIAN_UNIVERSITIES = {
    "nus", "national university of singapore", "ntu", "tsinghua",
    "peking university", "university of hong kong", "hku",
   "LSE", "Oxford", "Cambridge", "Imperial", "UCL", "Nanyang Technological University", "Melbourne", "ANU", "Sydney", "Ivy League"
}

# -----------------------------
# UTILITIES
# -----------------------------

def normalize(text: str) -> str:
    """Lowercase + strip noise for stable matching."""
    if not text:
        return ""
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


# -----------------------------
# EMPLOYER CLASSIFICATION
# -----------------------------

def classify_employer(company_name: str) -> Dict[str, Any]:
    """
    Maps employer to tier using fuzzy string matching.
    Returns: tier, confidence, matched_name
    """

    name = normalize(company_name)

    for c in EMPLOYER_TIERS["tier_1_ib"]:
        if normalize(c) in name:
            return {"tier": "tier_1_ib", "confidence": 1.0, "matched_name": c}

    for c in EMPLOYER_TIERS["tier_2_ib"]:
        if normalize(c) in name:
            return {"tier": "tier_2_ib", "confidence": 1.0, "matched_name": c}

    for c in EMPLOYER_TIERS["pe_hedge_top"]:
        if normalize(c) in name:
            return {"tier": "pe_hedge_top", "confidence": 1.0, "matched_name": c}

    return {"tier": "other", "confidence": 0.0, "matched_name": None}


# -----------------------------
# RETURNEE SIGNAL
# -----------------------------

def detect_returnee_signal(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Heuristic proxy for "Asia-returnee likelihood".

    Signals used:
    - Geography mentions in profile text
    - Asian university education
    - Non-Latin name script detection

    Known limitation:
    - Cannot distinguish travel vs residence
    """

    text_blob = normalize(str(record))
    signals = []
    score = 0

    # Geography
    for kw in ASIA_KEYWORDS:
        if kw in text_blob:
            signals.append(f"geo:{kw}")
            score += 2

    # Education
    education = record.get("education") or []
    for edu in education:
        edu_text = normalize(str(edu))
        for uni in ASIAN_UNIVERSITIES:
            if uni in edu_text:
                signals.append("edu_asia")
                score += 3

    # Name script heuristic
    name = record.get("full_name") or ""
    if name and any(ord(c) > 127 for c in name):
        signals.append("non_latin_name")
        score += 1

    return {
        "score": min(score, 10),
        "signals_found": signals
    }


# -----------------------------
# DIVERSITY FLAG (HEURISTIC ONLY)
# -----------------------------

def detect_diversity_flag(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Weak heuristic gender inference based on first-name patterns.

    WARNING:
    - High error rate for global/Asian names
    - Not ground truth
    - Should only be used for aggregation-level analysis
    """

    name = record.get("full_name") or ""
    first_name = name.split(" ")[0].lower()

    vowel_endings = {"a", "e", "i", "y"}
    score = sum(first_name.endswith(v) for v in vowel_endings)

    return {
        "is_female": score > 0 and len(first_name) > 3,
        "confidence": "low" if score == 0 else "medium"
    }


# -----------------------------
# MAIN SCORING ENGINE
# -----------------------------

def score_candidate(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produces final candidate score (0–100) with explainability.
    """

    employer = classify_employer(record.get("current_company"))
    returnee = detect_returnee_signal(record)
    diversity = detect_diversity_flag(record)

    score = 0

    # Employer quality (40)
    tier = employer["tier"]
    if tier == "tier_1_ib":
        score += 45
    elif tier == "pe_hedge_top":
        score += 35
    elif tier == "tier_2_ib":
        score += 25
    else:
        score += 10

    # Returnee signal (30)
    score += min(returnee["score"] * 3, 30)

    # Experience proxy (20)
    # NOTE: API may not provide this reliably → defensive default
    exp = record.get("years_experience") or 0

    if 2 <= exp <= 6:
        score += 20
    elif exp < 2:
        score += 10
    else:
        score += 15

    # Education quality proxy (10)
    edu_blob = normalize(str(record.get("education") or ""))

    elite_schools = {"nus", "ntu", "oxford", "cambridge", "harvard", "stanford"}
    if any(s in edu_blob for s in elite_schools):
        score += 10
    else:
        score += 5

    return {
        "candidate_id": record.get("id"),
        "final_score": min(score, 100),
        "employer": employer,
        "returnee_signal": returnee,
        "diversity_flag": diversity
    }

# -----------------------------
# PIPELINE EXECUTION
# -----------------------------

def load_input(file_path: str):
    """
    Loads input dataset from CSV or JSON.
    Returns list of dict records.
    """

    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
        return df.to_dict(orient="records")

    elif file_path.endswith(".json"):
        import json
        with open(file_path, "r") as f:
            return json.load(f)

    else:
        raise ValueError("Unsupported file format. Use CSV or JSON.")


def run_pipeline(input_path: str, output_path: str = "scored_output.csv"):
    """
    End-to-end scoring pipeline:
    input → score → save output
    """

    print(f"Loading data from {input_path}...")

    records = load_input(input_path)

    print(f"Total records loaded: {len(records)}")

    scored = []

    for r in records:
        try:
            scored.append(score_candidate(r))
        except Exception as e:
            # skip bad rows safely
            continue

    print(f"Successfully scored: {len(scored)}")

    # convert to dataframe for saving
    df = pd.DataFrame(scored)

    df.to_csv(output_path, index=False)

    print(f"Saved output to {output_path}")


# -----------------------------
# ENTRY POINT
# -----------------------------

if __name__ == "__main__":
    run_pipeline("candidates.csv")