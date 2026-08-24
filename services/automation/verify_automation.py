import asyncio
from playwright.async_api import async_playwright
import os
import sys

# Add adapters to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "app")))

from app.adapters.wttj_adapter import WTTJAdapter
from app.adapters.sncf_adapter import SNCFAdapter
from app.adapters.totalenergies_adapter import TotalEnergiesAdapter

async def run_verification(adapter, site_name, email, job_url):
    candidate_data = {
        "first_name": "Test",
        "last_name": "Candidate",
        "phone": "+33 6 12 34 56 78",
        "location": "Paris, France",
        "linkedin_url": "https://www.linkedin.com/in/testcandidate123",
        "experience_years": 4,
        "skills": ["Python", "React", "Playwright"],
        "bio": "A passionate software engineer specializing in test automation.",
        "work_preference": "Remote work preferred",
        "career_interests": "Software Engineering and AI",
        "salary_expectations": "70k EUR",
        "availability": "1 month notice",
        "resume_path": os.path.abspath("dummy_resume.pdf")
    }
    
    print(f"\n{'='*50}\nTesting {site_name}\n{'='*50}")
    try:
        async with async_playwright() as p:
            # We use headed mode so you can see it if you want, but default headless to avoid interrupting
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Test account creation (Simulated or real up to submission)
            print("1. Testing Account Creation/Navigation...")
            result = await adapter.create_account(
                page,
                email,
                "TestPassword123!",
                candidate_data
            )
            print(f"Result: {result}")
            
            # Test job apply
            print("2. Testing Job Application Navigation...")
            result = await adapter.apply_to_job(
                page,
                job_url,
                candidate_data
            )
            print(f"Result: {result}")
            
            await browser.close()
    except Exception as e:
        print(f"[X] Verification failed for {site_name}: {e}")

async def main():
    os.makedirs("screenshots", exist_ok=True)
    
    # Test WTTJ
    wttj = WTTJAdapter()
    await run_verification(
        wttj, 
        "Welcome to the Jungle", 
        "test+wttj_new5@example.com",
        "https://www.welcometothejungle.com/en/companies/wttj/jobs/senior-software-engineer-ruby_paris" # example url
    )
    
    # Test SNCF
    sncf = SNCFAdapter()
    await run_verification(
        sncf,
        "SNCF",
        "test+sncf@example.com",
        "https://www.emploi.sncf.com/offres/recherche"
    )
    
    # Test TotalEnergies
    total = TotalEnergiesAdapter()
    await run_verification(
        total,
        "TotalEnergies",
        "test+total@example.com",
        "https://totalenergies.com/careers/our-job-offers"
    )
    
    print("\n[OK] Verification complete. Check the screenshots folder.")

if __name__ == "__main__":
    asyncio.run(main())
