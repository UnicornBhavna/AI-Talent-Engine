from typing import Dict, Any
import re
import pandas as pd
import ast

# -----------------------------
# UTILITIES
# -----------------------------

def normalize(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"[^a-z0-9 ]", "", str(text).lower()).strip()


# -----------------------------
# EMPLOYER CLASSIFICATION
# -----------------------------

EMPLOYER_TIERS = {
    "tier_1_ib": [
        "goldman sachs", "morgan stanley", "jpmorgan", "jp morgan", "bank of america",
        "ubs", "barclays", "deutsche bank"
    ],
    "tier_2_ib": [
        "blackrock", "fidelity investments", "wellington", "schroders",
        "hsbc", "standard chartered", "nomura", "mizuho", "rbc",
        "bofa", "citi", "t. rowe price"
    ],
    "pe_hedge_top": [
        "blackstone", "kkr", "carlyle", "apollo", "brookfield",
        "bridgewater", "renaissance technologies", "bcg", "bain"
    ]
}


def classify_employer(company_name: str):
    name = normalize(company_name)

    for c in EMPLOYER_TIERS["tier_1_ib"]:
        if normalize(c) in name:
            return {"tier": "tier_1_ib", "matched": c}

    for c in EMPLOYER_TIERS["tier_2_ib"]:
        if normalize(c) in name:
            return {"tier": "tier_2_ib", "matched": c}

    for c in EMPLOYER_TIERS["pe_hedge_top"]:
        if normalize(c) in name:
            return {"tier": "pe_hedge_top", "matched": c}

    return {"tier": "other", "matched": None}


# -----------------------------
# RETURN SIGNAL
# -----------------------------

ASIA_KEYWORDS = {
    "singapore", "hong kong", "shanghai", "beijing", "mumbai",
    "bengaluru", "jakarta", "kuala lumpur", "seoul", "tokyo", "india",
    "china", "taiwan", "malaysia", "thailand", "indonesia"
}

ASIAN_UNIVERSITIES = {
    "nus", "ntu", "tsinghua", "peking university",
    "university of hong kong", "hku",
    "oxford", "cambridge", "harvard", "stanford"
}


def detect_returnee_signal(record: Dict[str, Any]):
    text = normalize(str(record))
    score = 0

    for kw in ASIA_KEYWORDS:
        if kw in text:
            score += 2

    education = record.get("education") or []
    for edu in education:
        edu_text = normalize(str(edu))
        for uni in ASIAN_UNIVERSITIES:
            if uni in edu_text:
                score += 3

    return {"score": min(score, 10)}


# -----------------------------
# DIVERSITY FLAG (HEURISTIC ONLY)
# -----------------------------

def detect_diversity_flag(record: Dict[str, Any]):
    name = record.get("full_name") or ""
    first = str(name).split(" ")[0].lower()

    vowel_endings = {"a", "e", "i", "y"}
    score = sum(first.endswith(v) for v in vowel_endings)

    return {
        "is_female": score > 0 and len(first) > 3,
        "confidence": "low" if score == 0 else "medium"
    }


# -----------------------------
# SCORING ENGINE
# -----------------------------

def score_candidate(record: Dict[str, Any]):
    employer = classify_employer(record.get("current_company"))
    returnee = detect_returnee_signal(record)
    diversity = detect_diversity_flag(record)

    score = 0

    if employer["tier"] == "tier_1_ib":
        score += 45
    elif employer["tier"] == "pe_hedge_top":
        score += 35
    elif employer["tier"] == "tier_2_ib":
        score += 25
    else:
        score += 10

    score += min(returnee["score"] * 3, 30)

    exp = record.get("years_experience") or 0

    if 2 <= exp <= 6:
        score += 20
    elif exp < 2:
        score += 10
    else:
        score += 15

    edu_blob = normalize(record.get("education"))

    elite = {"nus", "ntu", "oxford", "cambridge", "harvard", "stanford"}

    if any(e in edu_blob for e in elite):
        score += 10
    else:
        score += 5

    return {
        "final_score": min(score, 100),
        "employer_tier": employer["tier"],
        "employer_match": employer["matched"],
        "returnee_score": returnee["score"],
        "is_female": diversity["is_female"],
        "gender_confidence": diversity["confidence"]
    }


# -----------------------------
# LOAD + FIX CSV (IMPORTANT)
# -----------------------------

def load_input(path: str):
    df = pd.read_csv(path)

    records = df.to_dict(orient="records")

    for r in records:
        # FIX: nested fields stored as strings in CSV
        if isinstance(r.get("experience"), str):
            try:
                r["experience"] = ast.literal_eval(r["experience"])
            except:
                r["experience"] = []

        if isinstance(r.get("education"), str):
            try:
                r["education"] = ast.literal_eval(r["education"])
            except:
                r["education"] = []

    return records


# -----------------------------
# PIPELINE
# -----------------------------

def run_pipeline(input_path="candidates.csv", output_path="scored_output.csv"):

    records = load_input(input_path)

    print(f"Loaded records: {len(records)}")

    output = []

    for i, r in enumerate(records):
        try:
            scored = score_candidate(r)
            merged = {**r, **scored}
            output.append(merged)

        except Exception as e:
            print(f"Row {i} failed: {e}")
            continue

    df = pd.DataFrame(output)

    print(f"Successfully processed: {len(df)} rows")

    df.to_csv(output_path, index=False)

    print(f"Saved → {output_path}")


# -----------------------------
# ENTRY
# -----------------------------

if __name__ == "__main__":
    run_pipeline()