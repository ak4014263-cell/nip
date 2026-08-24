import requests
import base64

try:
    res = requests.get("http://localhost:8012/live-status")
    data = res.json()
    b64 = data.get("last_screenshot_base64")
    if b64:
        with open("C:/Users/hp/.gemini/antigravity-ide/brain/98571319-8473-4e08-be9a-1fb27efe26ee/scratch/stuck_onboarding.jpg", "wb") as f:
            f.write(base64.b64decode(b64))
        print("Screenshot saved to scratch/stuck_onboarding.jpg")
    else:
        print("No screenshot in live status")
    print("Current status:", data.get("step_name"), "-", data.get("progress"), "%")
except Exception as e:
    print("Error:", e)
