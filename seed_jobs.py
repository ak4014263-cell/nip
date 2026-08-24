import sys
import os
sys.path.append(os.path.abspath("."))
from shared.database import SessionLocal
from shared.models import Job

db = SessionLocal()
jobs = [
    {
        "title": "Senior Product Engineer",
        "company": "Inato",
        "location": "Paris (Remote)",
        "salaryMin": 70000,
        "salaryMax": 90000,
        "employmentType": "Full-time",
        "description": "Build innovative clinical trial solutions...",
        "requirements": ["React", "TypeScript", "Node.js"],
        "remote": True,
        "logo": "https://cdn-images.welcometothejungle.com/O618QJvB97L-2s8f2249-R-m3gUxtc_yK0XpEQiA/rs:auto:200::/q:85/czM6Ly93dHRqLXByb2R1Y3Rpb24vdXBsb2Fkcy9jb21wYW55L2xvZ28vNjg3NS8xNTQ5NjcvaW5hdG8uanBn",
        "sourceCareerSite": "WTTJ",
        "externalUrl": "https://www.welcometothejungle.com/en/companies/inato/jobs/senior-product-engineer_paris_INATO_7ZmJa0k",
        "can_apply": True
    },
    {
        "title": "Full Stack Developer",
        "company": "Oodrive",
        "location": "Paris, France",
        "salaryMin": 60000,
        "salaryMax": 80000,
        "employmentType": "Full-time",
        "description": "Join our core engineering team to build secure cloud solutions...",
        "requirements": ["Python", "React", "PostgreSQL"],
        "remote": False,
        "logo": "https://cdn-images.welcometothejungle.com/HnK25Z1f8K4Q1h8v15s5mJ4_O2vW3L-V24z59x2V5y0/rs:auto:200::/q:85/czM6Ly93dHRqLXByb2R1Y3Rpb24vdXBsb2Fkcy9jb21wYW55L2xvZ28vNjc0LzE1NTU1MS9vb2RyaXZlLnBuZw",
        "sourceCareerSite": "WTTJ",
        "externalUrl": "https://www.welcometothejungle.com/en/companies/oodrive/jobs/full-stack-developer_paris",
        "can_apply": True
    },
    {
        "title": "Senior Fullstack Developer",
        "company": "Sunstice",
        "location": "Boulogne-Billancourt, France",
        "salaryMin": 65000,
        "salaryMax": 85000,
        "employmentType": "Full-time",
        "description": "Help us revolutionize renewable energy transition...",
        "requirements": ["Vue.js", "Node.js", "AWS"],
        "remote": True,
        "logo": "https://cdn-images.welcometothejungle.com/cW3ZzX1QpM88R5X85xYx411pU_m4F_9L8K0vO6YV9wA/rs:auto:200::/q:85/czM6Ly93dHRqLXByb2R1Y3Rpb24vdXBsb2Fkcy9jb21wYW55L2xvZ28vMjU0LzE1Njc3MS9zdW5zdGljZS5wbmc",
        "sourceCareerSite": "WTTJ",
        "externalUrl": "https://www.welcometothejungle.com/en/companies/sunstice/jobs/senior-fullstack-developer_boulogne-billancourt_SUNST_KWRZDOj",
        "can_apply": True
    }
]

added = 0
for j_data in jobs:
    if not db.query(Job).filter_by(externalUrl=j_data["externalUrl"]).first():
        job = Job(**j_data)
        db.add(job)
        added += 1

db.commit()
print(f"Added {added} jobs successfully!")
