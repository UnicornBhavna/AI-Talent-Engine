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
# TARGET LOCATIONS (MANDATORY)
# -----------------------------
ALLOWED_LOCATIONS = ["USA", "UK", "Australia", "Hong Kong"]

CITIES = {
    "USA": ["New York"],
    "UK": ["London"],
    "Australia": ["Sydney", "Melbourne"],
    "Hong Kong": ["Hong Kong"]
}

# -----------------------------
# TRACK-SPECIFIC EMPLOYERS
# -----------------------------
IB_COMPANIES = [
    "Goldman Sachs", "Morgan Stanley", "JPMorgan",
    "Bank of America", "Barclays", "Deutsche Bank", "UBS"
]

BUYSIDE_COMPANIES = [
    "BlackRock", "Fidelity", "Wellington", "Schroders", "T. Rowe Price"
]

MBB_COMPANIES = [
    "McKinsey", "BCG", "Bain"
]

# -----------------------------
# ROLES
# -----------------------------
IB_ROLES = [
    "Investment Banking Analyst", "M&A Analyst",
    "Capital Markets Analyst", "Leveraged Finance Analyst"
]

BUYSIDE_ROLES = [
    "Investment Analyst", "Research Analyst"
]

MBB_ROLES = [
    "Associate", "Consultant"
]

# -----------------------------
# EDUCATION
# -----------------------------
TARGET_UNIS = [
    "LSE", "Oxford", "Cambridge", "Imperial", "UCL",
    "NUS", "NTU", "HKU",
    "University of Melbourne", "ANU", "University of Sydney",
    "Harvard", "Stanford", "Yale", "Princeton"
]

# -----------------------------
# ASIA SIGNAL
# -----------------------------
ASIA_COUNTRIES = ["Singapore", "India", "China", "Malaysia"]

ASIAN_NAMES = [
    "Aarav", "Arjun", "Wei", "Li", "Chen", "Ananya",
    "Rahul", "Kumar", "Tan", "Lim"
]

# -----------------------------
# HELPERS
# -----------------------------
def random_phone():
    return f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}"

def random_email(name):
    return f"{name.lower().replace(' ','.')}@gmail.com"

def random_date():
    return fake.date_between(
        start_date=datetime(2015, 1, 1),
        end_date=datetime(2024, 12, 31)
    ).isoformat()

def generate_location(country):
    return f"{random.choice(CITIES[country])}, {country}"

def generate_linkedin(name):
    if random.random() < 0.8:
        handle = name.lower().replace(" ", "-")
        return f"https://www.linkedin.com/in/{handle}", handle
    return None, None

# -----------------------------
# PROFILE BUILDER
# -----------------------------
def build_profile(i):

    # Identity
    first_name = random.choice(ASIAN_NAMES) if random.random() < 0.7 else fake.first_name()
    last_name = fake.last_name()
    full_name = f"{first_name} {last_name}"

    # Location
    country = random.choice(ALLOWED_LOCATIONS)

    # Track selection
    track = random.choice(["IB", "BUYSIDE", "MBB"])

    if track == "IB":
        company = random.choice(IB_COMPANIES)
        job_title = random.choice(IB_ROLES)
        industry = "Investment Banking"

    elif track == "BUYSIDE":
        company = random.choice(BUYSIDE_COMPANIES)
        job_title = random.choice(BUYSIDE_ROLES)
        industry = "Asset Management / Private Equity"

    else:
        company = random.choice(MBB_COMPANIES)
        job_title = random.choice(MBB_ROLES) + " - Private Equity / Corporate Finance"
        industry = "Consulting (MBB - PE/CF)"

    # Experience
    years_experience = random.randint(2, 4)

    # Education
    university = random.choice(TARGET_UNIS)

    # Asia signal
    asia_link = random.choice(ASIA_COUNTRIES)

    # LinkedIn
    linkedin_url, linkedin_id = generate_linkedin(full_name)

    profile = {
        "id": str(i),
        "full_name": full_name,
        "first_name": first_name,
        "last_name": last_name,
        "sex": random.choice(["M", "F"]),

        "mobile_phone": random_phone(),
        "emails": random_email(full_name),

        # FIXED FIELDS
        "location": generate_location(country),
        "countries": [country, asia_link],
        "industry": industry,

        "location_last_updated": random_date(),

        "current_company": company,
        "job_title": job_title,
        "years_experience": years_experience,

        "experience": [
            {
                "company": company,
                "title": job_title,
                "level": "Analyst" if years_experience < 3 else "Associate",
                "industry": industry,
                "country": country
            }
        ],

        "education": [
            {
                "school": university,
                "degree": random.choice(["Bachelors", "Masters"]),
                "end_date": random_date()
            }
        ],

        "linkedin_url": linkedin_url,
        "linkedin_id": linkedin_id,

        "asia_connection": asia_link
    }

    return profile

# -----------------------------
# GENERATE
# -----------------------------
def generate():
    return [build_profile(i) for i in range(TOTAL)]

data = generate()
df = pd.DataFrame(data)

df.to_csv("candidates.csv", index=False)

print("DONE ✔ Generated:", df.shape)