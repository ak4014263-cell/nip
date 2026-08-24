"""
Populate database with demo WTTJ jobs for testing JobSwipe
No external dependencies - just direct database insertion
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from shared.database import SessionLocal
from shared.models import Job
from datetime import datetime
import uuid

def populate_demo_jobs():
    """Add sample WTTJ jobs directly to database"""
    db = SessionLocal()
    
    demo_jobs = [
        {
            "title": "Senior Full Stack Engineer",
            "company": "Inato",
            "location": "Paris, France (Remote)",
            "logo": "https://cdn-images.welcometothejungle.com/VYyfSEOUPnGHos7u7u7jMNgp-uBh3EiPjyGmhFVXQf4/rs:auto:300:300:1/g:ce/q:85/czM6Ly93dGotcHJvZHVjdGlvbi91cGxvYWRzL29yZ2FuaXphdGlvbi9sb2dvLzYzNi9lNjE3YWQ0NS1jMzk2LTQxZGQtYTMwZC0yYzc2YzE5YWFmOTAuanBn",
            "salaryMin": 55000,
            "salaryMax": 85000,
            "employmentType": "Full-Time (CDI)",
            "description": "Join Inato to build the future of clinical research. We're looking for a talented Full Stack Engineer to work on our platform connecting research sites with clinical trials.",
            "requirements": ["React", "TypeScript", "Python", "FastAPI", "PostgreSQL"],
            "externalUrl": "https://www.welcometothejungle.com/en/companies/inato/jobs/senior-product-engineer_paris_INATO_7ZmJa0k",
            "remote": True
        },
        {
            "title": "Backend Engineer - Python",
            "company": "Doctolib",
            "location": "Paris, France (Hybrid)",
            "logo": "https://cdn-images.welcometothejungle.com/rOlMHU8pNv8eoGNI3d3Xr-62PY_FwGqS3zNvN6AqJp0/rs:auto:300:300:1/g:ce/q:85/czM6Ly93dGotcHJvZHVjdGlvbi91cGxvYWRzL29yZ2FuaXphdGlvbi9sb2dvLzYwNy9lOWRhMzA1ZC04NzJmLTRiZTgtOTM3YS05ZWE0NDEzYzg1YzIuanBn",
            "salaryMin": 50000,
            "salaryMax": 75000,
            "employmentType": "Full-Time (CDI)",
            "description": "Doctolib is looking for Backend Engineers to help scale our healthcare platform serving millions of patients across Europe.",
            "requirements": ["Python", "Django", "PostgreSQL", "Redis", "Docker"],
            "externalUrl": "https://www.welcometothejungle.com/en/companies/doctolib/jobs",
            "remote": True
        },
        {
            "title": "Frontend Developer - React",
            "company": "Alan",
            "location": "Paris, France (Remote)",
            "logo": "https://cdn-images.welcometothejungle.com/JjTf8KxPBvvB7PXdhJXwKLdGFbLNGVzjgfBmPrUjFrE/rs:auto:300:300:1/g:ce/q:85/czM6Ly93dGotcHJvZHVjdGlvbi91cGxvYWRzL29yZ2FuaXphdGlvbi9sb2dvLzMxMS8xOTQ0YzYyNS05NTkwLTQ2NDMtYmQ3Yi0yNGNjYmQyNzBkZTcuanBn",
            "salaryMin": 48000,
            "salaryMax": 70000,
            "employmentType": "Full-Time (CDI)",
            "description": "Join Alan to reinvent health insurance. We're building a modern, digital-first health insurance platform.",
            "requirements": ["React", "TypeScript", "GraphQL", "Testing Library"],
            "externalUrl": "https://www.welcometothejungle.com/en/companies/alan/jobs",
            "remote": True
        },
        {
            "title": "Full Stack Developer",
            "company": "Spendesk",
            "location": "Paris, France (Hybrid)",
            "logo": "https://cdn-images.welcometothejungle.com/L_OqFWDpDmFiYqL35hOLXRG7jR7vhNfC0LjXW5vPJQw/rs:auto:300:300:1/g:ce/q:85/czM6Ly93dGotcHJvZHVjdGlvbi91cGxvYWRzL29yZ2FuaXphdGlvbi9sb2dvLzIyOS9lNjJhMzA1Zi1lODQyLTQ5NzMtYTNmYy02NTNkNWMzMjU5YmUuanBn",
            "salaryMin": 52000,
            "salaryMax": 78000,
            "employmentType": "Full-Time (CDI)",
            "description": "Spendesk is revolutionizing spend management for modern companies. Build the future of business payments with us.",
            "requirements": ["Python", "React", "TypeScript", "AWS", "Kubernetes"],
            "externalUrl": "https://www.welcometothejungle.com/en/companies/spendesk/jobs",
            "remote": True
        },
        {
            "title": "Software Engineer - Platform",
            "company": "Datadog",
            "location": "Paris, France (Hybrid)",
            "logo": "https://cdn-images.welcometothejungle.com/ORHzsOeqkZRe_MjB5dXQOJ4g7n9hL2DYX8c24gZ3G4U/rs:auto:300:300:1/g:ce/q:85/czM6Ly93dGotcHJvZHVjdGlvbi91cGxvYWRzL29yZ2FuaXphdGlvbi9sb2dvLzIyMi9lNmQ5NDA1ZS0yMzZjLTRhMGEtYTMwYy02YzQwNWMzYTM2YmUuanBn",
            "salaryMin": 60000,
            "salaryMax": 90000,
            "employmentType": "Full-Time (CDI)",
            "description": "Datadog is building the next generation of monitoring and analytics platform. Join our Platform team to work on large-scale distributed systems.",
            "requirements": ["Python", "Go", "Kubernetes", "Distributed Systems", "Monitoring"],
            "externalUrl": "https://www.welcometothejungle.com/en/companies/datadog/jobs",
            "remote": True
        },
        {
            "title": "Senior Frontend Engineer",
            "company": "Qonto",
            "location": "Paris, France (Remote)",
            "logo": "https://cdn-images.welcometothejungle.com/eAqbXUo1rXLIgMwCqzSA9HI5vD5_nHGPCJ-ZmGS6kqE/rs:auto:300:300:1/g:ce/q:85/czM6Ly93dGotcHJvZHVjdGlvbi91cGxvYWRzL29yZ2FuaXphdGlvbi9sb2dvLzQwNy9lODBlMzA1NC05MjZlLTRhNzEtYTQ0YS02YzQwNWMzYTM2YmUuanBn",
            "salaryMin": 55000,
            "salaryMax": 80000,
            "employmentType": "Full-Time (CDI)",
            "description": "Qonto is the leading business banking solution. Help us build beautiful, intuitive interfaces for our customers.",
            "requirements": ["React", "TypeScript", "Redux", "Testing", "Design Systems"],
            "externalUrl": "https://www.welcometothejungle.com/en/companies/qonto/jobs",
            "remote": True
        },
        {
            "title": "DevOps Engineer",
            "company": "Contentsquare",
            "location": "Paris, France (Hybrid)",
            "logo": "https://cdn-images.welcometothejungle.com/6gGQg8r4BVlLy7qe5dZ5OqLPFNK3Rz3xDzL4JZD8GXE/rs:auto:300:300:1/g:ce/q:85/czM6Ly93dGotcHJvZHVjdGlvbi91cGxvYWRzL29yZ2FuaXphdGlvbi9sb2dvLzE3My9lNmQ5NDA1ZS0yMzZjLTRhMGEtYTMwYy02YzQwNWMzYTM2YmUuanBn",
            "salaryMin": 58000,
            "salaryMax": 82000,
            "employmentType": "Full-Time (CDI)",
            "description": "Contentsquare is a leading digital experience analytics platform. Join our DevOps team to manage our cloud infrastructure.",
            "requirements": ["AWS", "Kubernetes", "Terraform", "CI/CD", "Python"],
            "externalUrl": "https://www.welcometothejungle.com/en/companies/contentsquare/jobs",
            "remote": False
        },
        {
            "title": "Backend Engineer - Node.js",
            "company": "Livestorm",
            "location": "Paris, France (Remote)",
            "logo": "https://cdn-images.welcometothejungle.com/kZXGT3B9nVYuG7dN2hC8qLPFNK3Rz3xDzL4JZD8GXE/rs:auto:300:300:1/g:ce/q:85/czM6Ly93dGotcHJvZHVjdGlvbi91cGxvYWRzL29yZ2FuaXphdGlvbi9sb2dvLzI4Ny9lNmQ5NDA1ZS0yMzZjLTRhMGEtYTMwYy02YzQwNWMzYTM2YmUuanBn",
            "salaryMin": 50000,
            "salaryMax": 72000,
            "employmentType": "Full-Time (CDI)",
            "description": "Livestorm is building the next generation of video engagement platform. Work on real-time video streaming systems.",
            "requirements": ["Node.js", "TypeScript", "WebRTC", "Redis", "PostgreSQL"],
            "externalUrl": "https://www.welcometothejungle.com/en/companies/livestorm/jobs",
            "remote": True
        },
        {
            "title": "Machine Learning Engineer",
            "company": "Hugging Face",
            "location": "Paris, France (Remote)",
            "logo": "https://cdn-images.welcometothejungle.com/D4J3xL8g9Vh5yK2dN3xC8qLPFNK3Rz3xDzL4JZD8GXE/rs:auto:300:300:1/g:ce/q:85/czM6Ly93dGotcHJvZHVjdGlvbi91cGxvYWRzL29yZ2FuaXphdGlvbi9sb2dvLzM0NS9lNmQ5NDA1ZS0yMzZjLTRhMGEtYTMwYy02YzQwNWMzYTM2YmUuanBn",
            "salaryMin": 65000,
            "salaryMax": 95000,
            "employmentType": "Full-Time (CDI)",
            "description": "Hugging Face is democratizing AI. Join us to build the future of Natural Language Processing and Machine Learning.",
            "requirements": ["Python", "PyTorch", "TensorFlow", "NLP", "ML Engineering"],
            "externalUrl": "https://www.welcometothejungle.com/en/companies/hugging-face/jobs",
            "remote": True
        },
        {
            "title": "Full Stack Engineer",
            "company": "Payfit",
            "location": "Paris, France (Hybrid)",
            "logo": "https://cdn-images.welcometothejungle.com/M5T8gL9h3Vk6yN3dP4zD9rLQGOL4Tz4yEzM5K[A9HYF/rs:auto:300:300:1/g:ce/q:85/czM6Ly93dGotcHJvZHVjdGlvbi91cGxvYWRzL29yZ2FuaXphdGlvbi9sb2dvLzI1Ni9lNmQ5NDA1ZS0yMzZjLTRhMGEtYTMwYy02YzQwNWMzYTM2YmUuanBn",
            "salaryMin": 52000,
            "salaryMax": 76000,
            "employmentType": "Full-Time (CDI)",
            "description": "Payfit is simplifying payroll and HR management. Build scalable solutions for thousands of European companies.",
            "requirements": ["Ruby", "React", "PostgreSQL", "AWS", "Microservices"],
            "externalUrl": "https://www.welcometothejungle.com/en/companies/payfit/jobs",
            "remote": True
        }
    ]
    
    added = 0
    updated = 0
    
    try:
        for job_data in demo_jobs:
            # Check if job already exists by external URL
            existing = db.query(Job).filter(Job.externalUrl == job_data["externalUrl"]).first()
            
            if existing:
                # Update existing job
                existing.can_apply = True
                existing.expires_at = None
                updated += 1
            else:
                # Create new job
                new_job = Job(
                    id=f"wttj-demo-{uuid.uuid4().hex[:10]}",
                    title=job_data["title"],
                    company=job_data["company"],
                    location=job_data["location"],
                    logo=job_data["logo"],
                    salaryMin=job_data["salaryMin"],
                    salaryMax=job_data["salaryMax"],
                    employmentType=job_data["employmentType"],
                    description=job_data["description"],
                    requirements=job_data["requirements"],
                    sourceCareerSite="WTTJ",
                    externalUrl=job_data["externalUrl"],
                    remote=job_data["remote"],
                    created_at=datetime.utcnow(),
                    expires_at=None,
                    can_apply=True
                )
                db.add(new_job)
                added += 1
        
        db.commit()
        print(f"✅ Successfully populated demo jobs!")
        print(f"   📝 Added: {added}")
        print(f"   🔄 Updated: {updated}")
        print(f"   🎯 Total: {added + updated}")
        
        # Count total WTTJ jobs
        total_wttj = db.query(Job).filter(Job.sourceCareerSite == "WTTJ").count()
        print(f"   📊 Total WTTJ jobs in database: {total_wttj}")
        
        return {"added": added, "updated": updated, "total": total_wttj}
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Populating database with demo WTTJ jobs...")
    print("=" * 60)
    result = populate_demo_jobs()
    print("=" * 60)
    print("✨ Done! Check your JobSwipe interface now.")
