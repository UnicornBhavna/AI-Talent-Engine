from faker import Faker
import random
import pandas as pd
from datetime import datetime

fake = Faker()

# -----------------------------
# CORE CONFIG POOLS
# -----------------------------

TIER_A_FIRMS = [
    "Goldman Sachs", "Morgan Stanley", "JPMorgan", "Bank of America",
    "UBS", "Barclays", "Deutsche Bank"
]

TIER_B_FIRMS = [
    "BlackRock", "Fidelity Investments", "Wellington", "Schroders",
    "HSBC", "Standard Chartered", "Nomura", "Mizuho", "RBC",
    "Citi", "T. Rowe Price"
]

PE_HEDGE = [
    "Blackstone", "KKR", "Carlyle", "Apollo", "Brookfield",
    "Bridgewater", "Renaissance Technologies", "BCG", "Bain"
]

ASIA_LOCATIONS = ["Singapore", "Hong Kong", "Shanghai", "Mumbai", "Tokyo", "Seoul"]
WEST_LOCATIONS = ["New York", "London", "San Francisco", "Boston", "Toronto"]

UNIVERSITIES = [
    "Harvard University", "Stanford University", "Oxford University",
    "Cambridge University", "NUS", "NTU", "LSE", "MIT",
    "University of Melbourne"
]

INDUSTRIES = [
    "Investment Banking", "Private Equity", "Hedge Fund",
    "Asset Management", "Consulting"
]

# -----------------------------
# HELPERS
# -----------------------------

def random_date(start_year=2015, end_year=2024):
    return fake.date_between(
        start_date=datetime(start_year, 1, 1),
        end_date=datetime(end_year, 12, 31)
    )

def assign_tier(company):
    if company in TIER_A_FIRMS:
        return "A"
    elif company in TIER_B_FIRMS:
        return "B"
    else:
        return "C"

def generate_gender(tier):
    r = random.random()

    # realistic skew by tier
    if tier == "A":
        return "M" if r < 0.75 else "F"
    elif tier == "B":
        return "M" if r < 0.60 else "F"
    elif tier == "C":
        return "M" if r < 0.50 else "F"
    else:
        return "M" if r < 0.55 else "F"

# -----------------------------
# PROFILE GENERATOR
# -----------------------------

def build_profile(i):

    full_name = fake.name()
    first = full_name.split()[0]
    last = full_name.split()[-1]

    company = random.choice(TIER_A_FIRMS + TIER_B_FIRMS + PE_HEDGE)
    tier = assign_tier(company)

    sex = generate_gender(tier)

    return {
        "id": str(i),

        # Identity
        "full_name": full_name,
        "first_name": first,
        "middle_name": "",
        "middle_initial": "",
        "last_name": last,
        "last_initial": last[0],

        # Demographics
        "sex": sex,
        "birth_year": random.randint(1985, 2000),
        "birth_date": str(random_date(1985, 2000)),

        # Social
        "linkedin_url": f"https://linkedin.com/in/{fake.user_name()}",
        "linkedin_username": fake.user_name(),

        # Job
        "job_title": random.choice([
            "Investment Analyst", "Equity Research Analyst",
            "Private Equity Associate", "Hedge Fund Analyst"
        ]),

        "job_company_name": company,
        "job_company_industry": random.choice(INDUSTRIES),
        "job_company_size": random.choice(["1-10", "11-50", "51-200", "200-1000"]),

        # Location
        "location_name": random.choice(ASIA_LOCATIONS + WEST_LOCATIONS),
        "location_country": random.choice(["India", "USA", "UK", "Singapore"]),
        "location_continent": random.choice(["Asia", "North America", "Europe"]),

        # Skills
        "skills": random.sample([
            "financial modeling", "valuation", "equity research",
            "Python", "Excel", "portfolio management"
        ], 3),

        # Experience
        "experience": [
            {
                "company": company,
                "title": "Analyst",
                "start_date": str(random_date(2018, 2022)),
                "end_date": None,
                "is_primary": True
            }
        ],

        # Education
        "education": [
            {
                "school": random.choice(UNIVERSITIES),
                "degrees": ["Bachelors"],
                "majors": ["Finance"],
                "start_date": str(random_date(2010, 2016)),
                "end_date": str(random_date(2016, 2020))
            }
        ],

        "dataset_version": "1.1"
    }

# -----------------------------
# GENERATE DATASET
# -----------------------------

def generate(n=1000000):
    return [build_profile(i) for i in range(n)]

# -----------------------------
# SAVE
# -----------------------------

if __name__ == "__main__":
    data = generate(1000000)
    df = pd.DataFrame(data)
    df.to_csv("candidates.csv", index=False)
    print("Generated realistic candidates.csv ✔")