import asyncio
import sys
import os

# Fix encoding
sys.stdout.reconfigure(encoding="utf-8")

# Add paths
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("services/wttj"))

async def test_apply_job():
    try:
        print("Testing job application flow...")
        
        # Import the applier
        from services.wttj.app.wttj_firefox_applier import WTTJFirefoxApplier
        print("OK - WTTJFirefoxApplier imported")
        
        # Create instance
        applier = WTTJFirefoxApplier()
        print("OK - Applier instance created")
        
        # Test data
        profile_data = {
            "first_name": "Test",
            "last_name": "User",
            "phone": "+33 6 12 34 56 78",
            "location": "Paris, France",
            "title": "Software Engineer",
            "linkedin_url": "",
            "github_url": "",
            "portfolio_url": "",
            "availability": "Immediately",
            "salary_expectation": "50000",
            "custom_pitch": None,
            "email": "test@example.com"
        }
        
        print("OK - Profile data prepared")
        print("\nStarting job application automation...")
        
        # Call apply_to_job
        result = await applier.apply_to_job(
            email="test@example.com",
            password="TestPassword123!",
            job_url="https://www.welcometothejungle.com/en/companies/test/jobs/test-job",
            profile_data=profile_data,
            headless=True
        )
        
        print(f"\nOK - Result: {result}")
        return result
        
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(test_apply_job())
    print(f"\nFinal result: {result}")
