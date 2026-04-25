from typing import Dict, Any
import re
import pandas as pd
import ast
import difflib

# -----------------------------
# NORMALIZATION
# -----------------------------
def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", str(text).lower()) if text else ""


# -----------------------------
# CONFIG: WEIGHTS
# -----------------------------
WEIGHTS = {
    "employer_pedigree": 40,
    "role_relevance": 15,
    "tenure_fit": 20,
    "returnee_signal": 25
}


# -----------------------------
# EMPLOYER TIERS
# -----------------------------
EMPLOYER_TIERS = {
    "BB_IB": [
        "Goldman Sachs", "Morgan Stanley", "JPMorgan",
        "Bank of America", "UBS", "Barclays", "Deutsche Bank"
    ],
    "BUYSIDE": [
        "Blackstone", "KKR", "Carlyle", "Apollo", "BlackRock"
    ],
    "MBB": [
        "McKinsey", "BCG", "Bain"
    ]
}

ALL_COMPANIES = sum(EMPLOYER_TIERS.values(), [])


# -----------------------------
# EMPLOYER CLASSIFICATION
# -----------------------------
def classify_employer(company_name: str) -> dict:
    """
    Uses fuzzy matching to map company to known tier.

    WHY:
    Real data has inconsistent naming (e.g., "Goldman", "GS").
    Fuzzy matching improves recall vs exact match.

    LIMITATIONS:
    - Short aliases (GS) may fail
    """

    matches = difflib.get_close_matches(company_name, ALL_COMPANIES, n=1, cutoff=0.6)

    if matches:
        matched = matches[0]
        for tier, companies in EMPLOYER_TIERS.items():
            if matched in companies:
                return {"tier": tier, "confidence": 0.9, "matched_name": matched}

    return {"tier": "OTHER", "confidence": 0.5, "matched_name": company_name}


# -----------------------------
# ROLE RELEVANCE
# -----------------------------
def score_role_relevance(title: str) -> int:
    t = normalize(title)

    if any(k in t for k in ["investment banking", "private equity", "research"]):
        return WEIGHTS["role_relevance"]

    if "analyst" in t:
        return int(WEIGHTS["role_relevance"] * 0.6)

    return int(WEIGHTS["role_relevance"] * 0.3)


# -----------------------------
# TENURE FIT
# -----------------------------
def score_tenure(exp: int) -> int:
    if 2 <= exp <= 4:
        return WEIGHTS["tenure_fit"]
    elif 1 <= exp < 2 or 4 < exp <= 6:
        return int(WEIGHTS["tenure_fit"] * 0.6)
    else:
        return int(WEIGHTS["tenure_fit"] * 0.3)


# -----------------------------
# RETURN SIGNAL (FIXED)
# -----------------------------
ASIA = {"singapore", "hong kong", "india", "china", "japan"}
ASIA_UNIS = {"nus", "ntu", "hku", "tsinghua", "peking"}

def detect_returnee_signal(record: Dict[str, Any]) -> dict:
    """
    Uses proxies:
    - Asia education
    - Asia experience
    - Asia countries field
    - Location string
    - Weak name heuristic

    LIMITATIONS:
    - Noisy + proxy-based
    """

    score = 0
    signals = []

    # education
    for edu in record.get("education", []):
        if any(u in normalize(edu.get("school")) for u in ASIA_UNIS):
            score += 8
            signals.append("asia_education")

    # experience
    for exp in record.get("experience", []):
        if normalize(exp.get("country")) in ASIA:
            score += 8
            signals.append("asia_experience")

    # countries (FIXED)
    for c in record.get("countries", []):
        if normalize(c) in ASIA:
            score += 5
            signals.append("asia_country")

    # location string (NEW)
    loc = normalize(record.get("location"))
    if any(a in loc for a in ASIA):
        score += 5
        signals.append("asia_location")

    # name proxy
    if any(x in normalize(record.get("full_name")) for x in ["singh", "li", "chen"]):
        score += 4
        signals.append("name_proxy")

    return {
        "score": min(score, WEIGHTS["returnee_signal"]),
        "signals_found": signals
    }


# -----------------------------
# DIVERSITY FLAG
# -----------------------------
def detect_diversity_flag(record: Dict[str, Any]) -> dict:
    """
    Simple first-name heuristic.

    LIMITATIONS:
    - Not reliable globally
    - Misses non-binary identities
    """

    first = record.get("full_name", "").split(" ")[0].lower()
    is_female = first.endswith(("a", "e", "i"))
    confidence = "medium" if is_female else "low"

    return {"is_female": is_female, "confidence": confidence}


# -----------------------------
# FINAL SCORING
# -----------------------------
def score_candidate(record: Dict[str, Any]) -> dict:

    employer = classify_employer(record.get("current_company"))
    returnee = detect_returnee_signal(record)
    diversity = detect_diversity_flag(record)

    # employer score
    if employer["tier"] == "BB_IB":
        employer_score = WEIGHTS["employer_pedigree"]
    elif employer["tier"] == "BUYSIDE":
        employer_score = int(WEIGHTS["employer_pedigree"] * 0.9)
    elif employer["tier"] == "MBB":
        employer_score = int(WEIGHTS["employer_pedigree"] * 0.8)
    else:
        employer_score = int(WEIGHTS["employer_pedigree"] * 0.4)

    role_score = score_role_relevance(record.get("job_title", ""))
    tenure_score = score_tenure(record.get("years_experience", 0))
    returnee_score = returnee["score"]

    total = employer_score + role_score + tenure_score + returnee_score

    if total >= 75:
        tier = "A"
    elif total >= 55:
        tier = "B"
    elif total >= 40:
        tier = "C"
    else:
        tier = "Below"

    return {
        "total_score": total,
        "shortlist_tier": tier,
        "score_breakdown": {
            "employer_pedigree": employer_score,
            "role_relevance": role_score,
            "tenure_fit": tenure_score,
            "returnee_signal": returnee_score
        },
        "employer_tier": employer["tier"],
        "employer_match": employer["matched_name"],
        "returnee_signals": returnee["signals_found"],
        "diversity_flag": diversity
    }


# -----------------------------
# PIPELINE (UNCHANGED)
# -----------------------------
def load_input(path: str):
    df = pd.read_csv(path)
    records = df.to_dict(orient="records")

    for r in records:
        if isinstance(r.get("experience"), str):
            r["experience"] = ast.literal_eval(r["experience"])
        if isinstance(r.get("education"), str):
            r["education"] = ast.literal_eval(r["education"])

    return records


def run_pipeline(input_path="candidates.csv", output_path="scored_output.csv"):
    records = load_input(input_path)

    output = []

    for r in records:
        enriched = score_candidate(r)

        current_title_employer = f"{r.get('job_title')} at {r.get('current_company')}"
        location = r.get("location")

        diversity = enriched.get("diversity_flag")
        diversity_flag = f"{diversity['is_female']} ({diversity['confidence']})"

        score_rationale = f"{r.get('job_title')} at {r.get('current_company')} with {r.get('years_experience')} years experience. Strong profile based on employer pedigree and role alignment."

        final_record = {
            "full_name": r.get("full_name"),
            "current_title + employer": current_title_employer,
            "current_location": location,
            "employer_tier": enriched.get("employer_tier"),
            "total_score": enriched.get("total_score"),
            "score_breakdown": enriched.get("score_breakdown"),
            "shortlist_tier": enriched.get("shortlist_tier"),
            "diversity_flag": diversity_flag,
            "linkedin_url": r.get("linkedin_url"),
            "score_rationale": score_rationale
        }

        output.append(final_record)

    pd.DataFrame(output).to_csv(output_path, index=False)
    print(f"Saved → {output_path}")


if __name__ == "__main__":
    run_pipeline()