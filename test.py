import requests
import os
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
import time

# Load API key
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")
API_KEY = os.getenv("API_KEY")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# ------------------------
# STEP 1: SEARCH COMPANIES
# ------------------------
search_url = "https://api.coresignal.com/cdapi/v1/companies/search"

payload = {
    "query": "Goldman Sachs",
    "size": 100   # max per request
}

company_ids = []
page = 1

while True:
    payload["page"] = page
    res = requests.post(search_url, json=payload, headers=headers)

    print(f"Page {page}:", res.status_code)

    data = res.json().get("data", [])
    if not data:
        break

    company_ids.extend([item["id"] for item in data])

    page += 1
    time.sleep(1)  # avoid rate limits

print("Total IDs:", len(company_ids))


# ------------------------
# STEP 2: FETCH DETAILS
# ------------------------
details = []

for i, cid in enumerate(company_ids):
    url = f"https://api.coresignal.com/cdapi/v1/companies/{cid}"
    res = requests.get(url, headers=headers)

    if res.status_code == 200:
        details.append(res.json())

    # rate limit protection
    if i % 50 == 0:
        time.sleep(1)

print("Fetched:", len(details))


# ------------------------
# STEP 3: SAVE CSV
# ------------------------
df = pd.json_normalize(details)
df.to_csv("companies.csv", index=False)

print("Final shape:", df.shape)