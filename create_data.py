from faker import Faker
import random
import pandas as pd
from datetime import datetime

fake = Faker()

# -----------------------------
# CORE POOLS
# -----------------------------

COMPANIES = [
    ("Goldman Sachs", "Investment Banking", "USA"),
    ("Morgan Stanley", "Investment Banking", "USA"),
    ("JPMorgan", "Investment Banking", "USA"),
    ("BlackRock", "Asset Management", "USA"),
    ("HSBC", "Banking", "UK"),
    ("Barclays", "Banking", "UK"),
    ("UBS", "Wealth Management", "Switzerland"),
    ("Deutsche Bank", "Banking", "Germany"),
    ("Blackstone", "Private Equity", "USA"),
    ("KKR", "Private Equity", "USA"),
    ("Carlyle", "Private Equity", "USA"),
    ("Bain", "Consulting", "USA"),
]

UNIVERSITIES = [
    ("Harvard University", "USA", "University"),
    ("Stanford University", "USA", "University"),
    ("Oxford University", "UK", "University"),
    ("Cambridge University", "UK", "University"),
    ("National University of Singapore", "Singapore", "University"),
    ("Nanyang Technological University", "Singapore", "University"),
    ("University of Toronto", "Canada", "University"),
]

JOB_LEVELS = ["Analyst", "Associate", "Senior Associate", "VP"]

ROLES = {
    "Investment Banking Analyst": "Investment Banking",
    "Equity Research Analyst": "Research",
    "Private Equity Associate": "Private Equity",
    "Hedge Fund Analyst": "Hedge Fund",
}

INDUSTRIES = ["Banking", "Asset Management", "Private Equity", "Consulting"]

COUNTRIES = ["USA", "UK", "Singapore", "Germany", "Switzerland", "Canada"]

# -----------------------------
# HELPERS
# -----------------------------

def maybe_null(value, prob=0.05):
    """Controlled sparsity (only 5% null max)"""
    return None if random.random() < prob else value


def random_phone():
    return maybe_null(f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}", 0.03)


def random_email(name):
    return maybe_null(f"{name.lower().replace(' ','.')}@gmail.com", 0.02)


def random_date(start=2010, end=2024):
    return fake.date_between(
        start_date=datetime(start, 1, 1),
        end_date=datetime(end, 12, 31)
    )

# -----------------------------
# MAIN PROFILE
# -----------------------------

def build_profile(i):

    full_name = fake.name()
    first_name = full_name.split()[0]
    last_name = full_name.split()[-1]

    company, industry, company_country = random.choice(COMPANIES)
    uni, uni_country, school_type = random.choice(UNIVERSITIES)

    job_title = random.choice(list(ROLES.keys()))

    sex = random.choice(["M", "F"])

    return {
        # ---------------- Identity ----------------
        "id": str(i),
        "full_name": full_name,
        "first_name": first_name,
        "last_name": last_name,
        "sex": sex,

        # ---------------- Social ----------------
        "linkedin_id": maybe_null(fake.random_number(9), 0.02),

        # ---------------- Contact ----------------
        "mobile_phone": random_phone(),
        "emails": random_email(full_name),

        # ---------------- Industry ----------------
        "industry": industry,

        # ---------------- Job ----------------
        "job_title": job_title,
        "job_company_name": company,
        "job_company_industry": industry,

        # ---------------- Location ----------------
        "all_countries": random.sample(COUNTRIES, k=random.randint(1, 2)),
        "location_last_updated": str(random_date(2020, 2024)),

        # ---------------- Experience ----------------
        "experience": [
            {
                "title": job_title,
                "clean_title": job_title,
                "role": ROLES[job_title],
                "levels": random.choice(JOB_LEVELS),
                "company": company,
                "company_name_clean": company,
                "company_country": company_country
            }
        ],

        # ---------------- Education ----------------
        "education": [
            {
                "school": uni,
                "school_country": uni_country,
                "school_type": school_type,
                "end_date": str(random_date(2015, 2022)),
                "degree": random.choice(["Bachelors", "Masters"])
            }
        ]
    }


# -----------------------------
# GENERATE DATASET
# -----------------------------

def generate(n):
    data = []
    for i in range(n):
        data.append(build_profile(i))
        if i % 5000 == 0:
            print(f"Generated {i} records...")
    return data


# -----------------------------
# SAVE
# -----------------------------

data = generate(50000)

print("Generation complete. Converting to DataFrame...")

df = pd.DataFrame(data)

print("DataFrame created:", df.shape)

df.to_csv("candidates.csv", index=False)

print("Generated clean structured candidates.csv ✔")