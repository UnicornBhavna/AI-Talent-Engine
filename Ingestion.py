"""
Responsibilities:
1. Authenticate API via .env
2. Fetch paginated candidate data with rate-limit handling
3. Clean/normalize raw response
4. Persist raw + cleaned datasets for downstream scoring
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
MAX_PAGES = 50  # safety cap to avoid infinite loops
SLEEP_BETWEEN_CALLS = 1

# -----------------------------
# AUTH
# -----------------------------

# Load API key
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")
API_KEY = os.getenv("API_KEY")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# -----------------------------
# FETCH LAYER
# -----------------------------

def fetch_all() -> list:
    """
    Fetches paginated candidate data from API.

    Handles:
    - pagination
    - rate limiting (429)
    - basic retry logic
    """

    all_records = []
    page = 1

    while page <= MAX_PAGES:

        payload = {
            "page": page,
            "per_page": PER_PAGE,
            "filters": {
                "location": [
                    "United States",
                    "United Kingdom",
                    "Australia",
                    "Hong Kong"
                ],
                "job_title": [
                    "Analyst",
                    "Investment Analyst",
                    "Investment Banking Analyst",
                    "Research Analyst",
                    "Associate"
                ]
            }
        }

        try:
            res = requests.post(BASE_URL, json=payload, headers=HEADERS, timeout=30)

        except requests.exceptions.RequestException as e:
            print(f"Request failed on page {page}: {e}")
            time.sleep(5)
            continue

        # Rate limit handling
        if res.status_code == 429:
            print("Rate limited — sleeping before retry...")
            time.sleep(5)
            continue

        if res.status_code != 200:
            print(f"API Error (page {page}): {res.status_code} - {res.text}")
            break

        data = res.json().get("results", [])

        if not data:
            print("No more data returned — stopping pagination.")
            break

        all_records.extend(data)
        print(f"Page {page} fetched | Total records: {len(all_records)}")

        page += 1
        time.sleep(SLEEP_BETWEEN_CALLS)

    return all_records

# -----------------------------
# TRANSFORM LAYER
# -----------------------------

def extract(records: list) -> list:
    """
    Extracts only relevant fields for downstream scoring.
    Keeps schema lightweight and stable.
    """

    cleaned = []

    for r in records:
        cleaned.append({
            "full_name": r['full_name'],     #r.get("full_name"),
            "job_title": r['job_title'],                 #r.get("job_title"),
            "current_company": r['current_company'],          #r.get("current_company"),
            "location": r['location'],              #r.get("location"),
            "linkedin_url": r['linkedin_url'],             #r.get("linkedin_url"),
            "raw": r  # keep full payload for debugging/scoring enrichment
        })

    return cleaned

# -----------------------------
# PERSISTENCE LAYER
# -----------------------------

def save_csv(data: list) -> None:
    """Saves cleaned dataset for audit + downstream reuse."""

    df = pd.DataFrame(data)
    df.to_csv("candidates.csv", index=False)
    print(f"Saved {len(df)} records to candidates.csv")

# -----------------------------
# ORCHESTRATION
# -----------------------------

def main():
    """
    End-to-end ingestion run:
    API → Raw → Clean → CSV
    """

    print("Starting ingestion pipeline...")

    #records = fetch_all()
    df = pd.read_csv("candidates.csv")
    records = df.to_dict(orient="records")

    print(f"Raw records fetched: {len(records)}")

    cleaned = extract(records)
    print(f"Cleaned records: {len(cleaned)}")

    save_csv(cleaned)


if __name__ == "__main__":
    main()
