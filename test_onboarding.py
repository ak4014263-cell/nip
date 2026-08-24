import requests
import time

def main():
    url = "http://localhost:8012/onboard-new-user"
    payload = {
        "candidate_id": "test_onboard_001",
        "career_site": "WTTJ",
        "email": "k45490335@gmail.com",
        "password": "Wttj@Hon05ed2026!",
        "resume_path": "scratch/resume.pdf",
        "first_name": "HON",
        "last_name": "Dupont",
        "location": "Paris",
        "is_existing": True
    }
    print("Starting onboarding...")
    try:
        response = requests.post(url, json=payload)
        print(response.json())
    except Exception as e:
        print(e)

    # Since it runs in the background, let's poll the live-status endpoint
    print("Polling live status...")
    last_progress = 0
    for _ in range(60):
        try:
            res = requests.get("http://localhost:8012/live-status")
            data = res.json()
            progress = data.get('progress', 0)
            print(f"[{progress}%] {data.get('step_name')} - Running: {data.get('is_running')}")
            if not data.get('is_running'):
                break
        except Exception:
            pass
        time.sleep(2)

if __name__ == "__main__":
    main()
