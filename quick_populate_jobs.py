"""
Quick script to populate jobs using direct SQLite connection
No service dependencies needed
"""
import sqlite3
import uuid
from datetime import datetime

def populate_jobs():
    """Populate database with demo WTTJ jobs directly via SQLite"""
    
    db_path = "swiply.db"
    
    demo_jobs = [
        ("Senior Full Stack Engineer", "Inato", "Paris, France (Remote)", "https://cdn-images.welcometothejungle.com/VYyfSEOUPnGHos7u7u7jMNgp-uBh3EiPjyGmhFVXQf4/rs:auto:300:300:1/g:ce/q:85/czM6Ly93dGotcHJvZHVjdGlvbi91cGxvYWRzL29yZ2FuaXphdGlvbi9sb2dvLzYzNi9lNjE3YWQ0NS1jMzk2LTQxZGQtYTMwZC0yYzc2YzE5YWFmOTAuanBn", 55000, 85000, "https://www.welcometothejungle.com/en/companies/inato/jobs/senior-product-engineer_paris_INATO_7ZmJa0k"),
        ("Backend Engineer - Python", "Doctolib", "Paris, France (Hybrid)", "https://cdn-images.welcometothejungle.com/rOlMHU8pNv8eoGNI3d3Xr-62PY_FwGqS3zNvN6AqJp0/rs:auto:300:300:1/g:ce/q:85/czM6Ly93dGotcHJvZHVjdGlvbi91cGxvYWRzL29yZ2FuaXphdGlvbi9sb2dvLzYwNy9lOWRhMzA1ZC04NzJmLTRiZTgtOTM3YS05ZWE0NDEzYzg1YzIuanBn", 50000, 75000, "https://www.welcometothejungle.com/en/companies/doctolib/jobs/backend-engineer-python"),
        ("Frontend Developer - React", "Alan", "Paris, France (Remote)", "https://cdn-images.welcometothejungle.com/JjTf8KxPBvvB7PXdhJXwKLdGFbLNGVzjgfBmPrUjFrE/rs:auto:300:300:1/g:ce/q:85/czM6Ly93dGotcHJvZHVjdGlvbi91cGxvYWRzL29yZ2FuaXphdGlvbi9sb2dvLzMxMS8xOTQ0YzYyNS05NTkwLTQ2NDMtYmQ3Yi0yNGNjYmQyNzBkZTcuanBn", 48000, 70000, "https://www.welcometothejungle.com/en/companies/alan/jobs/frontend-developer-react"),
        ("Full Stack Developer", "Spendesk", "Paris, France (Hybrid)", "https://cdn-images.welcometothejungle.com/L_OqFWDpDmFiYqL35hOLXRG7jR7vhNfC0LjXW5vPJQw/rs:auto:300:300:1/g:ce/q:85/czM6Ly93dGotcHJvZHVjdGlvbi91cGxvYWRzL29yZ2FuaXphdGlvbi9sb2dvLzIyOS9lNjJhMzA1Zi1lODQyLTQ5NzMtYTNmYy02NTNkNWMzMjU5YmUuanBn", 52000, 78000, "https://www.welcometothejungle.com/en/companies/spendesk/jobs/fullstack-developer"),
        ("Software Engineer - Platform", "Datadog", "Paris, France (Hybrid)", "https://cdn-images.welcometothejungle.com/ORHzsOeqkZRe_MjB5dXQOJ4g7n9hL2DYX8c24gZ3G4U/rs:auto:300:300:1/g:ce/q:85/czM6Ly93dGotcHJvZHVjdGlvbi91cGxvYWRzL29yZ2FuaXphdGlvbi9sb2dvLzIyMi9lNmQ5NDA1ZS0yMzZjLTRhMGEtYTMwYy02YzQwNWMzYTM2YmUuanBn", 60000, 90000, "https://www.welcometothejungle.com/en/companies/datadog/jobs/platform-engineer"),
        ("Senior Frontend Engineer", "Qonto", "Paris, France (Remote)", "https://cdn-images.welcometothejungle.com/eAqbXUo1rXLIgMwCqzSA9HI5vD5_nHGPCJ-ZmGS6kqE/rs:auto:300:300:1/g:ce/q:85/czM6Ly93dGotcHJvZHVjdGlvbi91cGxvYWRzL29yZ2FuaXphdGlvbi9sb2dvLzQwNy9lODBlMzA1NC05MjZlLTRhNzEtYTQ0YS02YzQwNWMzYTM2YmUuanBn", 55000, 80000, "https://www.welcometothejungle.com/en/companies/qonto/jobs/senior-frontend-engineer"),
        ("DevOps Engineer", "Contentsquare", "Paris, France (Hybrid)", "https://www.welcometothejungle.com/favicon.ico", 58000, 82000, "https://www.welcometothejungle.com/en/companies/contentsquare/jobs/devops-engineer"),
        ("Backend Engineer - Node.js", "Livestorm", "Paris, France (Remote)", "https://www.welcometothejungle.com/favicon.ico", 50000, 72000, "https://www.welcometothejungle.com/en/companies/livestorm/jobs/backend-nodejs"),
        ("Machine Learning Engineer", "Hugging Face", "Paris, France (Remote)", "https://www.welcometothejungle.com/favicon.ico", 65000, 95000, "https://www.welcometothejungle.com/en/companies/hugging-face/jobs/ml-engineer"),
        ("Full Stack Engineer", "Payfit", "Paris, France (Hybrid)", "https://www.welcometothejungle.com/favicon.ico", 52000, 76000, "https://www.welcometothejungle.com/en/companies/payfit/jobs/fullstack"),
    ]
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        added = 0
        updated = 0
        
        for job_data in demo_jobs:
            title, company, location, logo, salary_min, salary_max, external_url = job_data
            
            # Check if job exists
            cursor.execute("SELECT id FROM jobs WHERE externalUrl = ?", (external_url,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing job
                cursor.execute("""
                    UPDATE jobs 
                    SET can_apply = 1, expires_at = NULL 
                    WHERE externalUrl = ?
                """, (external_url,))
                updated += 1
            else:
                # Insert new job
                job_id = f"wttj-demo-{uuid.uuid4().hex[:10]}"
                cursor.execute("""
                    INSERT INTO jobs (
                        id, title, company, location, logo, 
                        salaryMin, salaryMax, employmentType, 
                        description, requirements, sourceCareerSite, 
                        externalUrl, remote, created_at, expires_at, can_apply
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job_id,
                    title,
                    company,
                    location,
                    logo,
                    salary_min,
                    salary_max,
                    "Full-Time (CDI)",
                    f"Exciting opportunity at {company}. Join us to build amazing products.",
                    '["React", "TypeScript", "Python", "FastAPI"]',
                    "WTTJ",
                    external_url,
                    1,  # remote
                    datetime.utcnow().isoformat(),
                    None,  # expires_at
                    1  # can_apply
                ))
                added += 1
        
        conn.commit()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE sourceCareerSite = 'WTTJ'")
        total_wttj = cursor.fetchone()[0]
        
        print("=" * 60)
        print("✅ Successfully populated demo jobs!")
        print(f"   📝 Added: {added}")
        print(f"   🔄 Updated: {updated}")
        print(f"   🎯 Total WTTJ jobs in database: {total_wttj}")
        print("=" * 60)
        print("\n🎉 Done! Refresh your JobSwipe page to see the jobs!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Populating database with demo WTTJ jobs...")
    populate_jobs()
