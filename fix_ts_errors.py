import os

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

# api.ts
fix_file(os.path.join(frontend_dir, "services", "api.ts"), [
    ("|| `${API_BASE}`", "|| 'https://swiply.io:8000'"),
    ("|| `${API_BASE_URL}`", "|| 'https://swiply.io:8000'")
])

# JobSwipe.tsx, Dashboard.tsx, Credentials.tsx, Profile.tsx, Applications.tsx, EmailInbox.tsx
for file in ["pages/candidate/JobSwipe.tsx", "pages/candidate/Dashboard.tsx", "pages/candidate/Credentials.tsx", "pages/candidate/Profile.tsx", "pages/candidate/Applications.tsx", "pages/candidate/EmailInbox.tsx"]:
    fix_file(os.path.join(frontend_dir, file), [
        ("|| `${API_BASE}`", "|| 'https://swiply.io:8000'"),
        ("const API_BASE = `${API_BASE}`", "const API_BASE = ((import.meta as any).env?.VITE_API_URL) || 'https://swiply.io:8000'")
    ])

# wttjSync.ts
fix_file(os.path.join(frontend_dir, "services", "wttjSync.ts"), [
    ("`${API_BASE}/wttj`", "(((import.meta as any).env?.VITE_API_URL) || 'https://swiply.io:8000') + '/wttj'")
])
