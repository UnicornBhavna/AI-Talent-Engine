from faker import Faker
import random
import pandas as pd

fake = Faker()

# -----------------------------
# REALISTIC SEGMENTATION POOLS
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

ASIA_LOCATIONS = [
    "Singapore", "Hong Kong", "Shanghai", "Beijing",
    "Mumbai", "Bengaluru", "Tokyo", "Seoul"
]

WEST_LOCATIONS = [
    "New York", "London", "San Francisco", "Chicago",
    "Boston", "Toronto"
]

ELITE_UNI = [
    "Oxford", "Cambridge", "Harvard", "Stanford",
    "NUS", "NTU", "LSE", "MIT"
]

MID_UNI = [
    "University of Melbourne", "NYU", "University of Toronto",
    "National University of Singapore", "University of Hong Kong"
]

JOB_TITLES = [
    "Investment Analyst",
    "Equity Research Analyst",
    "Investment Banking Analyst",
    "Private Equity Associate",
    "Hedge Fund Analyst"
]

# -----------------------------
# PROFILE GENERATORS (KEY FIX)
# -----------------------------

def generate_tier_a():
    return {
        "id": fake.uuid4(),
        "full_name": fake.name(),
        "current_company": random.choice(TIER_A_FIRMS),
        "job_title": random.choice(JOB_TITLES),
        "location": random.choice(ASIA_LOCATIONS),   # forced returnee signal
        "education": random.choice(ELITE_UNI),
        "years_experience": random.randint(2, 8),
        "linkedin_url": f"https://linkedin.com/in/{fake.user_name()}"
    }

def generate_tier_b():
    return {
        "id": fake.uuid4(),
        "full_name": fake.name(),
        "current_company": random.choice(TIER_B_FIRMS + PE_HEDGE),
        "job_title": random.choice(JOB_TITLES),
        "location": random.choice(WEST_LOCATIONS + ASIA_LOCATIONS),
        "education": random.choice(MID_UNI + ELITE_UNI),
        "years_experience": random.randint(1, 10),
        "linkedin_url": f"https://linkedin.com/in/{fake.user_name()}"
    }

def generate_tier_c():
    return {
        "id": fake.uuid4(),
        "full_name": fake.name(),
        "current_company": random.choice(TIER_B_FIRMS),
        "job_title": random.choice(JOB_TITLES),
        "location": random.choice(WEST_LOCATIONS),
        "education": random.choice(MID_UNI),
        "years_experience": random.randint(0, 6),
        "linkedin_url": f"https://linkedin.com/in/{fake.user_name()}"
    }

def generate_below():
    return {
        "id": fake.uuid4(),
        "full_name": fake.name(),
        "current_company": "Unknown Firm",
        "job_title": "Analyst",
        "location": random.choice(WEST_LOCATIONS),
        "education": "Unknown University",
        "years_experience": random.randint(0, 2),
        "linkedin_url": f"https://linkedin.com/in/{fake.user_name()}"
    }

# -----------------------------
# MAIN GENERATOR
# -----------------------------

def generate_candidates(n=10000):
    data = []

    for _ in range(n):
        r = random.random()

        if r < 0.20:
            data.append(generate_tier_a())
        elif r < 0.55:
            data.append(generate_tier_b())
        elif r < 0.85:
            data.append(generate_tier_c())
        else:
            data.append(generate_below())

    return pd.DataFrame(data)


# -----------------------------
# SAVE
# -----------------------------

df = generate_candidates(10000)
df.to_csv("candidates.csv", index=False)

print("Generated realistic candidates.csv ✔")