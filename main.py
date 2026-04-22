import re
import csv
from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime

# ---------------- CONFIG ---------------- 
CITIES = [
    "Bangalore, Karnataka, India",
    "Hyderabad, Telangana, India",
    "Chennai, Tamil Nadu, India",
    "Kochi, Kerela, India"
]

SEARCH_TERMS = (
    "data analyst OR data engineer OR business analyst "
    "OR software engineer OR associate software engineer "
    "OR junior software engineer OR software developer "
    "OR python developer OR java developer"
)

# ---------------- SCRAPE ---------------- 
all_jobs = []
for city in CITIES:
    print(f"🔍 Scraping jobs for {city}")
    try:
        jobs = scrape_jobs(
            site_name=["indeed", "zip_recruiter", "linkedin"],
            search_term=SEARCH_TERMS,
            location=city,
            results_wanted=120,
            hours_old=168,
            country_indeed="INDIA",
        )
        if jobs is not None and not jobs.empty:
            all_jobs.append(jobs)
    except Exception as e:
        print(f"❌ Error scraping {city}: {e}")
        continue

if not all_jobs:
    print("❌ No jobs scraped from any city")
    exit()

jobs = pd.concat(all_jobs, ignore_index=True)
jobs = jobs.dropna(subset=["title", "company", "job_url"])
print(f"✅ Total jobs scraped: {len(jobs)}")

# ---------------- IT ROLE FILTER ---------------- 
IT_ROLES = [
    "data analyst", "data engineer", "business analyst",
    "software engineer", "associate software engineer", "ase",
    "junior software", "software developer", "developer",
    "programmer", "python developer", "java developer",
]

def is_it_role(title):
    if not title:
        return False
    title = title.lower()
    return any(role in title for role in IT_ROLES)

jobs = jobs[jobs["title"].apply(is_it_role)]
print(f"✅ IT roles after title filter: {len(jobs)}")

def fresher_acceptable(row):
    """
    VERY STRICT filter:
    Accept ONLY 0-1 year jobs.
    Reject everything else.
    """

    title = str(row.get("title", "")).lower()
    desc = str(row.get("description", "")).lower()

    text = f"{title} {desc}"

    # ---------------- HARD REJECT: Senior Roles ----------------
    senior_words = [
        "senior", "sr", "lead", "manager", "architect",
        "principal", "director", "head", "vp",
        "consultant", "expert"
    ]

    if any(w in title for w in senior_words):
        return False

    # ---------------- HARD REJECT: ANY 2+ YEARS ----------------
    reject_patterns = [

        # 2 years / 3 years / 4+ years etc
        r'\b[2-9]\s*\+?\s*(year|yr)s?\b',

        # 1-3 years, 2-5 years
        r'\b[1-9]\s*(to|-)\s*[1-9]\s*(year|yr)s?\b',

        # minimum / at least
        r'\b(minimum|at\s*least|min)\s*[2-9]\b',

        # experience: 2 / exp: 3
        r'\b(experience|exp)\s*[:\-]?\s*[2-9]\b',

        # more than 1 year
        r'\bmore than\s*1\s*(year|yr)\b',

        # preferred experience
        r'\b[2-9]\+?\s*(year|yr)s?\s*(preferred|required)?\b'
    ]

    for p in reject_patterns:
        if re.search(p, text):
            return False

    # ---------------- ACCEPT ONLY CLEAR 0–1 ----------------

    accept_patterns = [

        r'\bfresher\b',
        r'\bno experience\b',
        r'\b0\s*(year|yr)\b',
        r'\b0-1\s*(year|yr)\b',
        r'\b1\s*(year|yr)\b',
        r'\bentry[\s-]?level\b',
        r'\bgraduate trainee\b',
        r'\btrainee\b',
        r'\brecent graduate\b'
    ]

    for p in accept_patterns:
        if re.search(p, text):
            return True

    # ---------------- IF NO CLEAR SIGNAL → REJECT ----------------
    return False

jobs = jobs[jobs.apply(fresher_acceptable, axis=1)]
print(f"✅ Fresher-acceptable IT jobs: {len(jobs)}")

# ---------------- DEBUG ----------------
print("\n" + "="*70)
print("📋 SAMPLE OF JOBS BEING KEPT:")
print("="*70)

sample_kept = jobs[["title", "description"]].head(5)
for idx, row in sample_kept.iterrows():
    print(f"\n✅ {row['title']}")
    desc_preview = str(row['description'])[:200] if row['description'] else "No description"
    print(f"   {desc_preview}...")

# ---------------- FINAL OUTPUT ----------------

final_jobs = jobs.rename(columns={
    "title": "role",
    "job_url": "link",
    "site": "source",
    "location": "location",
    "date_posted": "posted_date"
})

final_jobs = final_jobs[[
    "company",
    "role",
    "location",
    "source",
    "posted_date",
    "link"
]]

final_jobs = final_jobs.drop_duplicates(subset=["company", "role", "link"])

today = datetime.now().strftime("%Y-%m-%d")
file_name = f"main2fresher_jobs_india_{today}.csv"

final_jobs.to_csv(
    file_name,
    index=False,
    quoting=csv.QUOTE_NONNUMERIC,
    encoding="utf-8"
)

print("\n" + "="*70)
print(f"🎉 CSV GENERATED SUCCESSFULLY")
print(f"📁 File Name: {file_name}")
print(f"📊 Total Fresher Jobs: {len(final_jobs)}")
print("="*70)

print("\n📋 SAMPLE DATA:")
print(final_jobs.head(10).to_string())
