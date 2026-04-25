"""
Responsibilities:
1. Authenticate API via .env
2. Fetch paginated candidate data with rate-limit handling
3. Clean/normalize + FLATTEN important fields
4. Preserve raw payload for debugging
5. Persist structured dataset for scoring + UI
"""

import requests
import os
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
import time

# -----------------------------
# CONFIG
# -----------------------------

BASE_URL = "https://api.coresignal.com/cdapi/v1/professional_network/person/search"
PER_PAGE = 100
MAX_PAGES = 50
SLEEP_BETWEEN_CALLS = 1

# -----------------------------
# AUTH
# -----------------------------

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")
API_KEY = os.getenv("API_KEY")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# -----------------------------
# GENDER NORMALIZATION
# -----------------------------

def normalize_gender(value):
    if value is None:
        return "U"

    v = str(value).strip().lower()

    if v in ["m", "male", "man", "mr"]:
        return "M"

    if v in ["f", "female", "woman", "ms", "mrs"]:
        return "F"

    return "U"


# -----------------------------
# FETCH LAYER
# -----------------------------

def fetch_all() -> list:

    all_records = []
    page = 1

    while page <= MAX_PAGES:

        payload = {
            "page": page,
            "per_page": PER_PAGE,
            "filters": {
                "location": ["United States", "United Kingdom", "Australia", "Hong Kong"],
                "job_title": [
                    "Analyst", "Investment Analyst",
                    "Investment Banking Analyst", "Research Analyst", "Associate"
                ]
            }
        }

        try:
            res = requests.post(BASE_URL, json=payload, headers=HEADERS, timeout=30)

        except requests.exceptions.RequestException as e:
            print(f"Request failed on page {page}: {e}")
            time.sleep(5)
            continue

        if res.status_code == 429:
            time.sleep(5)
            continue

        if res.status_code != 200:
            print(f"API Error: {res.status_code}")
            break

        data = res.json().get("results", [])

        if not data:
            break

        all_records.extend(data)
        print(f"Page {page} | total: {len(all_records)}")

        page += 1
        time.sleep(SLEEP_BETWEEN_CALLS)

    return all_records


# -----------------------------
# TRANSFORM LAYER (IMPORTANT FIX)
# -----------------------------

def extract(records: list) -> list:

    cleaned = []

    for r in records:

        cleaned.append({

            # ---------------- Identity ----------------
            "id": r.get("id"),
            "full_name": r.get("full_name"),

            # ---------------- Job ----------------
            "job_title": r.get("job_title"),
            "current_company": r.get("current_company"),
            "industry": r.get("industry"),

            # ---------------- Location ----------------
            "location": r.get("location"),
            "countries": r.get("countries"),

            # ---------------- Social ----------------
            "linkedin_url": r.get("linkedin_url"),
            "linkedin_id": r.get("linkedin_id"),

            # ---------------- Contact ----------------
            "mobile_phone": r.get("mobile_phone"),
            "emails": r.get("emails"),

            # ---------------- Gender ----------------
            "sex": normalize_gender(r.get("sex") or r.get("gender")),

            # ---------------- Experience (structured) ----------------
            "experience": r.get("experience"),

            # ---------------- Education (structured) ----------------
            "education": r.get("education"),

            # ---------------- Metadata ----------------
            "location_last_updated": r.get("location_last_updated"),

            # ---------------- FULL RAW ----------------
            "raw": r
        })

    return cleaned


# -----------------------------
# SAVE
# -----------------------------

def save_csv(data: list):
    df = pd.DataFrame(data)
    df.to_csv("candidates.csv", index=False)
    print(f"Saved {len(df)} records → candidates.csv")


# -----------------------------
# MAIN
# -----------------------------

def main():
    print("Starting ingestion pipeline...")

  #  records = fetch_all()
    df = pd.read_csv("candidates.csv")
    records = df.to_dict(orient="records")

    print(f"Fetched: {len(records)} records")

    cleaned = extract(records)

    print(f"Cleaned: {len(cleaned)} records")

    save_csv(cleaned)


if __name__ == "__main__":
    main()