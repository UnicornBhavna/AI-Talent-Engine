from faker import Faker
import random
import pandas as pd
from datetime import datetime

fake = Faker()

# -----------------------------
# CONFIG
# -----------------------------

TOTAL = int(input("Enter total records: "))

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
]

COUNTRIES = ["USA", "UK", "Singapore", "Germany", "Switzerland", "Canada"]

ROLES = [
    "Investment Banking Analyst",
    "Equity Research Analyst",
    "Private Equity Associate",
    "Hedge Fund Analyst"
]

JOB_LEVELS = ["Analyst", "Associate", "Senior Associate", "VP"]

# -----------------------------
# HELPERS
# -----------------------------

def maybe_null(value, prob=0.02):
    return None if random.random() < prob else value


def random_phone():
    return f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}"


def random_email(name):
    return f"{name.lower().replace(' ','.')}@gmail.com"


def random_date():
    return fake.date_between(start_date=datetime(2010,1,1), end_date=datetime(2024,12,31)).isoformat()

# -----------------------------
# PROFILE BUILDER
# -----------------------------

def build_profile(i):

    full_name = fake.name()
    first_name = full_name.split()[0]
    last_name = full_name.split()[-1]

    company, industry, company_country = random.choice(COMPANIES)
    uni, uni_country, school_type = random.choice(UNIVERSITIES)

    job_title = random.choice(ROLES)
    sex = random.choice(["M", "F"])

    return {
        # ---------------- Identity ----------------
        "id": str(i),
        "full_name": full_name,
        "first_name": first_name,
        "last_name": last_name,
        "sex": sex,

        # ---------------- Contact ----------------
        "mobile_phone": random_phone(),
        "emails": random_email(full_name),

        # ---------------- Location ----------------
        "all_countries": random.sample(COUNTRIES, k=random.randint(1,2)),
        "location_last_updated": random_date(),

        # ---------------- Job Context (IMPORTANT for scoring) ----------------
        "current_company": company,
        "job_title": job_title,
        "years_experience": random.randint(0, 12),

        # ---------------- Experience (FIXED STRUCTURE) ----------------
        "experience": [
            {
                "company": company,
                "title": job_title,
                "level": random.choice(JOB_LEVELS),
                "industry": industry,
                "country": company_country
            }
        ],

        # ---------------- Education (FIXED STRUCTURE) ----------------
        "education": [
            {
                "school": uni,
                "degree": random.choice(["Bachelors", "Masters"]),
                "end_date": random_date()
            }
        ]
    }

# -----------------------------
# GENERATE
# -----------------------------

def generate():
    return [build_profile(i) for i in range(TOTAL)]

data = generate()

df = pd.DataFrame(data)

df.to_csv("candidates.csv", index=False)

print("DONE ✔ Generated:", df.shape)