"""
Quick test to verify jobs appear in JobSwipe
Uses direct database population instead of scraping
"""
import requests

API_BASE = "http://localhost:8000"

def test_job_visibility():
    print("Testing Job Visibility...")
    print("=" * 60)
    
    # 1. Populate demo jobs directly
    print("\n1. Populating demo WTTJ jobs...")
    try:
        response = requests.post(f"{API_BASE}/populate-demo-jobs", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success!")
            print(f"   Added: {result.get('added', 0)} new jobs")
            print(f"   Updated: {result.get('updated', 0)} existing jobs")
            print(f"   Total WTTJ jobs: {result.get('total_wttj_jobs', 0)}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Make sure the API Gateway is running on port 8000")
    
    # 2. Check job recommendations
    print("\n2. Checking job recommendations...")
    try:
        response = requests.get(f"http://localhost:8003/recommendations", timeout=10)
        if response.status_code == 200:
            result = response.json()
            jobs = result.get('jobs', [])
            print(f"✅ Found {len(jobs)} jobs in recommendations")
            
            # Show first few jobs
            if jobs:
                print("\n   Sample jobs:")
                for job in jobs[:3]:
                    print(f"   - {job.get('title')} at {job.get('company')}")
                    print(f"     Match: {job.get('match_score')}% | Remote: {job.get('remote')}")
            else:
                print("   ⚠️  No jobs found in recommendations")
                print("   This might be because you've already swiped all jobs")
        else:
            print(f"❌ Error: {response.status_code}")
            print("   Make sure the Job Service is running on port 8003")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete! Check your JobSwipe UI now.")
    print("   URL: http://localhost:3000/candidate/job-swipe")

if __name__ == "__main__":
    test_job_visibility()

if __name__ == "__main__":
    test_job_visibility()
