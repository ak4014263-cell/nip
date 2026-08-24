import sys
import os
sys.path.append(os.path.abspath("."))
from shared.database import SessionLocal
from shared.models import Job

db = SessionLocal()
jobs = db.query(Job).all()
count = 0
for j in jobs:
    if not j.can_apply:
        j.can_apply = True
        count += 1

db.commit()
print(f"Updated {count} jobs")
