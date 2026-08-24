import os
import re

frontend_dir = r"c:\Users\hp\Downloads\IOP\WTJ\frontend\src"

def fix_file(path, replacements):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = content
    for old, new in replacements:
        new_content = new_content.replace(old, new)
    if new_content != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Fixed {path}")

# Fix the self-referencing API_BASE in all files
for root, _, files in os.walk(frontend_dir):
    for file in files:
        if file.endswith(".ts") or file.endswith(".tsx"):
            path = os.path.join(root, file)
            fix_file(path, [
                ("|| `${API_BASE}`", "|| 'https://swiply.io:8000'"),
                ("|| `${API_BASE_URL}`", "|| 'https://swiply.io:8000'")
            ])

# Fix Credentials.tsx order specifically
cred_path = os.path.join(frontend_dir, "pages", "candidate", "Credentials.tsx")
with open(cred_path, "r", encoding="utf-8") as f:
    cred_content = f.read()
if "const CREDENTIAL_SERVICE" in cred_content and "const API_BASE =" in cred_content:
    cred_content = cred_content.replace("const CREDENTIAL_SERVICE = `${API_BASE}/credentials`\nconst WTTJ_SERVICE = `${API_BASE}/wttj`\nconst API_BASE = ((import.meta as any).env?.VITE_API_URL) || 'https://swiply.io:8000'", "const API_BASE = ((import.meta as any).env?.VITE_API_URL) || 'https://swiply.io:8000'\nconst CREDENTIAL_SERVICE = `${API_BASE}/credentials`\nconst WTTJ_SERVICE = `${API_BASE}/wttj`")
    with open(cred_path, "w", encoding="utf-8") as f:
        f.write(cred_content)
        print("Fixed Credentials.tsx order")

# Fix wttjSync.ts order specifically
wttj_path = os.path.join(frontend_dir, "services", "wttjSync.ts")
with open(wttj_path, "r", encoding="utf-8") as f:
    wttj_content = f.read()
if "const SYNC_SERVICE_URL = `${API_BASE}/wttj`;\nconst API_BASE =" in wttj_content:
    wttj_content = wttj_content.replace("const SYNC_SERVICE_URL = `${API_BASE}/wttj`;\nconst API_BASE = ((import.meta as any).env?.VITE_API_URL) || 'https://swiply.io:8000';", "const API_BASE = ((import.meta as any).env?.VITE_API_URL) || 'https://swiply.io:8000';\nconst SYNC_SERVICE_URL = `${API_BASE}/wttj`;")
    with open(wttj_path, "w", encoding="utf-8") as f:
        f.write(wttj_content)
        print("Fixed wttjSync.ts order")

