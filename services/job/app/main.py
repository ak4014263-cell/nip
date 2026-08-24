"""
Job Service
Handles job listings, recommendations, and swipe actions
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import random
import re
from datetime import datetime
import uuid
import sys
import httpx
import asyncio
from typing import Optional, List, Dict

# Add root directory to path for shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from shared.database import get_db, engine, Base
from shared.models import Job as DBJob, Swipe as DBSwipe, Application as DBApplication
from sqlalchemy.orm import Session

# Initialize database tables (including expires_at and can_apply columns)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: Database initialization error: {e}")

app = FastAPI(
    title="Swiply Job Service",
    description="Job listings and matching service",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
AUTOMATION_SERVICE_URL = os.getenv("AUTOMATION_SERVICE_URL", "http://localhost:8006")
CREDENTIAL_SERVICE_URL = os.getenv("CREDENTIAL_SERVICE_URL", "http://localhost:8009")
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL", "http://localhost:8007")

async def trigger_job_automation(candidate_id: str, job: DBJob, db: Session):
    """Trigger automation for job application"""
    try:
        # Step 1: Get or create credentials for the career site
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get credentials
            cred_response = await client.post(f"{CREDENTIAL_SERVICE_URL}/credentials/{job.sourceCareerSite}?candidate_id={candidate_id}")
            
            if cred_response.status_code != 200:
                return {"success": False, "error": "Failed to get credentials"}
            
            credentials = cred_response.json()
            
            # Step 2: Check if account exists, if not create it
            if not credentials.get("isVerified"):
                # Trigger account creation automation
                account_payload = {
                    "site_name": job.sourceCareerSite,
                    "credentials": {
                        "email": credentials["email"],
                        "password": credentials["password"]
                    },
                    "candidate_data": {
                        "first_name": "John",  # TODO: Get from user profile
                        "last_name": "Doe",    # TODO: Get from user profile
                        "phone": "+33612345678"  # TODO: Get from user profile
                    }
                }
                
                account_response = await client.post(f"{AUTOMATION_SERVICE_URL}/jobs/create-account", json=account_payload)
                
                if account_response.status_code == 200:
                    # Update credential as verified
                    # TODO: Add endpoint to update credential verification status
                    pass
            
            # Step 3: Trigger job application automation
            application_payload = {
                "site_name": job.sourceCareerSite,
                "credentials": {
                    "email": credentials["email"],
                    "password": credentials["password"]
                },
                "application_data": {
                    "job_url": job.externalUrl,
                    "cover_letter": f"I am very interested in the {job.title} position at {job.company}. My skills align well with your requirements.",
                    "resume_path": "/path/to/resume.pdf"  # TODO: Get from user profile
                }
            }
            
            apply_response = await client.post(f"{AUTOMATION_SERVICE_URL}/jobs/apply", json=application_payload)
            
            if apply_response.status_code == 200:
                # Update application status to "Automation Queued"
                app = db.query(DBApplication).filter(
                    DBApplication.candidate_id == candidate_id,
                    DBApplication.job_id == job.id
                ).first()
                
                if app:
                    app.status = "Automation Queued"
                    db.commit()
                
                # Trigger email simulation
                email_payload = {
                    "candidate_id": candidate_id,
                    "job_title": job.title,
                    "company": job.company
                }
                
                try:
                    await client.post(f"{EMAIL_SERVICE_URL}/simulate-application-response", json=email_payload)
                except Exception as e:
                    print(f"Failed to trigger email simulation: {e}")
                
                return {
                    "success": True,
                    "message": "Automation triggered successfully",
                    "credentials_email": credentials["email"],
                    "job_id": apply_response.json().get("job_id")
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to trigger application automation"
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Automation error: {str(e)}"
        }

@app.get("/")
async def root():
    return {"service": "job", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("")
@app.get("/")
async def get_jobs(limit: int = 10, offset: int = 0, db: Session = Depends(get_db)):
    """Get paginated job listings - only non-expired jobs with apply options"""
    from sqlalchemy import and_, or_
    
    # Filter: only jobs that can be applied to
    # Allow jobs with no expiration date OR jobs that haven't expired yet
    jobs_query = db.query(DBJob).filter(
        and_(
            or_(DBJob.expires_at == None, DBJob.expires_at > datetime.utcnow()),
            or_(DBJob.can_apply == True, DBJob.can_apply == None)  # Allow None for backwards compatibility
        )
    )
    
    total = jobs_query.count()
    jobs = jobs_query.offset(offset).limit(limit).all()
    
    # Format for JSON
    job_list = []
    for j in jobs:
        job_list.append({
            "id": j.id,
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "salaryMin": j.salaryMin,
            "salaryMax": j.salaryMax,
            "employmentType": j.employmentType,
            "description": j.description,
            "requirements": j.requirements or [],
            "remote": j.remote,
            "logo": j.logo,
            "sourceCareerSite": j.sourceCareerSite,
            "externalUrl": j.externalUrl,
            "createdAt": j.created_at.isoformat()
        })
    
    return {
        "jobs": job_list,
        "total": total,
        "limit": limit,
        "offset": offset,
        "hasMore": (offset + limit) < total
    }

@app.get("/recommendations")
async def get_job_recommendations(candidate_id: str = "demo-candidate", db: Session = Depends(get_db)):
    """Get personalized job recommendations with AI matching scores"""
    from sqlalchemy import and_, or_
    
    # Filter out already swiped jobs
    swiped_job_ids = {s.job_id for s in db.query(DBSwipe).filter(DBSwipe.candidate_id == candidate_id).all()}
    
    # Get non-expired jobs with apply options (allow None for backwards compatibility)
    all_jobs = db.query(DBJob).filter(
        and_(
            or_(DBJob.expires_at == None, DBJob.expires_at > datetime.utcnow()),
            or_(DBJob.can_apply == True, DBJob.can_apply == None)
        )
    ).all()
    
    available_jobs = [job for job in all_jobs if job.id not in swiped_job_ids]
    
    # Mock candidate profile for matching
    candidate_profile = {
        "experience_years": 4,
        "skills": ["react", "typescript", "node.js", "postgresql", "aws"],
        "preferred_locations": ["paris", "remote"],
        "salary_expectation": {"min": 50000, "max": 70000}
    }
    
    # Calculate match scores for each job
    jobs_with_scores = []
    for job in available_jobs:
        # Calculate match score
        candidate_skills = set(skill.lower() for skill in candidate_profile["skills"])
        
        req_list = job.requirements if job.requirements else []
        job_requirements = set(req.lower() for req in req_list)
        
        # Skills matching
        skills_intersection = candidate_skills.intersection(job_requirements)
        skills_score = (len(skills_intersection) / max(len(job_requirements), 1)) * 100
        
        # Experience matching
        candidate_exp = candidate_profile["experience_years"]
        required_exp_match = re.search(r'(\d+)\+?\s*years?', ' '.join(req_list))
        required_exp = int(required_exp_match.group(1)) if required_exp_match else 2
        exp_score = min(100, (candidate_exp / max(required_exp, 1)) * 100)
        
        # Location matching
        candidate_locations = candidate_profile["preferred_locations"]
        job_location = (job.location or "").lower()
        location_score = 100 if any(loc in job_location for loc in candidate_locations) else 50
        if job.remote and "remote" in candidate_locations:
            location_score = 100
        
        # Salary matching
        salary_score = 100
        if job.salaryMin and candidate_profile["salary_expectation"]["min"]:
            job_salary = job.salaryMax or job.salaryMin
            candidate_min = candidate_profile["salary_expectation"]["min"]
            salary_score = 100 if job_salary >= candidate_min else 70
        
        # Overall score (weighted)
        overall_score = round(
            skills_score * 0.4 + 
            exp_score * 0.25 + 
            location_score * 0.2 + 
            salary_score * 0.15
        )
        
        job_dict = {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "salaryMin": job.salaryMin,
            "salaryMax": job.salaryMax,
            "employmentType": job.employmentType,
            "description": job.description,
            "requirements": job.requirements or [],
            "remote": job.remote,
            "logo": job.logo,
            "sourceCareerSite": job.sourceCareerSite,
            "externalUrl": job.externalUrl,
            "createdAt": job.created_at.isoformat()
        }

        # Add match data to job
        job_with_match = {
            **job_dict,
            "match_score": overall_score,
            "match_breakdown": {
                "skills": round(skills_score),
                "experience": round(exp_score),
                "location": round(location_score),
                "salary": round(salary_score)
            },
            "matched_skills": list(skills_intersection),
            "missing_skills": list(job_requirements - candidate_skills)
        }
        
        jobs_with_scores.append(job_with_match)
    
    # Sort by match score (highest first)
    jobs_with_scores.sort(key=lambda x: x["match_score"], reverse=True)
    
    return {
        "jobs": jobs_with_scores[:10],  # Return top 10 matches
        "total": len(jobs_with_scores)
    }

@app.get("/jobs/{job_id}")
async def get_job_by_id(job_id: str, db: Session = Depends(get_db)):
    """Get a specific job by ID"""
    job = db.query(DBJob).filter(DBJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "salaryMin": job.salaryMin,
        "salaryMax": job.salaryMax,
        "employmentType": job.employmentType,
        "description": job.description,
        "requirements": job.requirements or [],
        "remote": job.remote,
        "logo": job.logo,
        "sourceCareerSite": job.sourceCareerSite,
        "externalUrl": job.externalUrl,
        "createdAt": job.created_at.isoformat()
    }

@app.post("/jobs/{job_id}/swipe")
async def swipe_job(job_id: str, swipe_data: dict, candidate_id: str = "demo-candidate", db: Session = Depends(get_db)):
    """Record a swipe action (like/pass)"""
    liked = swipe_data.get("liked", False)
    
    # Record the swipe
    new_swipe = DBSwipe(
        candidate_id=candidate_id,
        job_id=job_id,
        liked=liked
    )
    db.add(new_swipe)
    
    # Get job details
    job = db.query(DBJob).filter(DBJob.id == job_id).first()
    if not job:
        db.rollback()
        return {"error": "Job not found"}
        
    job_dict = {
        "id": job.id,
        "title": job.title,
        "company": job.company
    }
    
    if liked:
        # Create application record with "Pending" status initially
        new_app = DBApplication(
            candidate_id=candidate_id,
            job_id=job_id,
            status="Pending Automation"
        )
        db.add(new_app)
        db.commit()
        
        # Trigger actual automation
        automation_result = await trigger_job_automation(candidate_id, job, db)
        
        return {
            "success": True,
            "action": "applied",
            "message": f"Automation started for {job.title} at {job.company}!",
            "job": job_dict,
            "automationStarted": True,
            "automationDetails": automation_result
        }
    else:
        db.commit()
        return {
            "success": True,
            "action": "passed",
            "message": f"Passed on {job.title}",
            "job": job_dict
        }

@app.get("/swipes")
async def get_user_swipes(candidate_id: str = "demo-candidate", db: Session = Depends(get_db)):
    """Get all swipes for a candidate"""
    swipes = db.query(DBSwipe).filter(DBSwipe.candidate_id == candidate_id).all()
    
    detailed_swipes = []
    
    for swipe in swipes:
        job = db.query(DBJob).filter(DBJob.id == swipe.job_id).first()
        if job:
            detailed_swipes.append({
                "job": {
                    "id": job.id,
                    "title": job.title,
                    "company": job.company
                },
                "liked": swipe.liked,
                "timestamp": swipe.timestamp.isoformat()
            })
    
    return {
        "swipes": detailed_swipes,
        "total": len(detailed_swipes),
        "liked": len([s for s in detailed_swipes if s["liked"]]),
        "passed": len([s for s in detailed_swipes if not s["liked"]])
    }

@app.get("/matches")
async def get_matches(candidate_id: str = "demo-candidate", db: Session = Depends(get_db)):
    """Get all liked jobs (matches)"""
    swipes = db.query(DBSwipe).filter(DBSwipe.candidate_id == candidate_id, DBSwipe.liked == True).all()
    
    matches = []
    for swipe in swipes:
        job = db.query(DBJob).filter(DBJob.id == swipe.job_id).first()
        if job:
            matches.append({
                "job": {
                    "id": job.id,
                    "title": job.title,
                    "company": job.company
                },
                "matchedAt": swipe.timestamp.isoformat(),
                "status": "applied"  # Since we auto-apply on right swipe
            })
    
    return {
        "matches": matches,
        "total": len(matches)
    }

@app.post("/applications")
async def create_application(app_data: dict, db: Session = Depends(get_db)):
    """Create or record a new job application"""
    candidate_id = app_data.get("candidate_id", "demo-candidate")
    job_id = app_data.get("job_id") or f"wttj_{str(uuid.uuid4())[:8]}"
    job_title = app_data.get("job_title", "Senior Product Engineer")
    company_name = app_data.get("company_name", "Inato")
    status = app_data.get("status", "Applied")
    
    # Check if job exists in db, or create record
    job = db.query(DBJob).filter(DBJob.id == job_id).first()
    if not job:
        job = DBJob(
            id=job_id,
            title=job_title,
            company=company_name,
            location=app_data.get("location", "Paris, France / Remote"),
            logo=app_data.get("logo", "https://cdn-images.welcometothejungle.com/uploads/company/logo/inato.png"),
            sourceCareerSite="WTTJ",
            externalUrl=app_data.get("job_url", "")
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
    new_app = DBApplication(
        candidate_id=candidate_id,
        job_id=job.id,
        status=status,
        applied_at=datetime.utcnow()
    )
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    
    return {
        "success": True,
        "application_id": new_app.id,
        "candidate_id": candidate_id,
        "job": {
            "id": job.id,
            "title": job.title,
            "company": job.company
        },
        "status": new_app.status,
        "appliedAt": new_app.applied_at.isoformat()
    }

@app.get("/applications")
async def get_applications(candidate_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all applications for candidate"""
    query = db.query(DBApplication)
    if candidate_id and candidate_id != "demo-candidate":
        apps = query.filter(DBApplication.candidate_id == candidate_id).order_by(DBApplication.applied_at.desc()).all()
        if not apps:
            apps = query.order_by(DBApplication.applied_at.desc()).all()
    else:
        apps = query.order_by(DBApplication.applied_at.desc()).all()
    
    result = []
    for a in apps:
        job = db.query(DBJob).filter(DBJob.id == a.job_id).first()
        if job:
            result.append({
                "id": a.id,
                "job": {
                    "id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "logo": job.logo,
                    "location": job.location,
                    "externalUrl": job.externalUrl
                },
                "status": a.status,
                "appliedAt": a.applied_at.isoformat() if a.applied_at else datetime.utcnow().isoformat()
            })
    return result

@app.get("/applications/stats")
async def get_applications_stats(candidate_id: str = "demo-candidate", db: Session = Depends(get_db)):
    apps = db.query(DBApplication).filter(DBApplication.candidate_id == candidate_id).all()
    status_counts = {}
    for a in apps:
        status_counts[a.status] = status_counts.get(a.status, 0) + 1
    
@app.post("/jobs/create-or-update")
async def create_or_update_job(job_data: dict, db: Session = Depends(get_db)):
    """Create or update a job listing from WTTJ scraping"""
    external_url = job_data.get("externalUrl")
    existing_job = None
    if external_url:
        existing_job = db.query(DBJob).filter(DBJob.externalUrl == external_url).first()
        
    if not existing_job:
        # Check by title & company
        existing_job = db.query(DBJob).filter(
            DBJob.title == job_data.get("title"),
            DBJob.company == job_data.get("company")
        ).first()

    if existing_job:
        existing_job.title = job_data.get("title", existing_job.title)
        existing_job.company = job_data.get("company", existing_job.company)
        existing_job.location = job_data.get("location", existing_job.location)
        existing_job.salaryMin = job_data.get("salaryMin", existing_job.salaryMin)
        existing_job.salaryMax = job_data.get("salaryMax", existing_job.salaryMax)
        existing_job.description = job_data.get("description", existing_job.description)
        existing_job.requirements = job_data.get("requirements", existing_job.requirements)
        existing_job.remote = job_data.get("remote", existing_job.remote)
        existing_job.logo = job_data.get("logo", existing_job.logo)
        existing_job.externalUrl = external_url or existing_job.externalUrl
        existing_job.sourceCareerSite = "WTTJ"
        db.commit()
        return {"success": True, "action": "updated", "id": existing_job.id}
    else:
        new_job = DBJob(
            id=str(uuid.uuid4()),
            title=job_data.get("title", "Software Engineer"),
            company=job_data.get("company", "Tech Company"),
            location=job_data.get("location", "Paris, France"),
            salaryMin=job_data.get("salaryMin", 60000),
            salaryMax=job_data.get("salaryMax", 80000),
            employmentType=job_data.get("employmentType", "Permanent (CDI)"),
            description=job_data.get("description", "Exciting tech opportunity"),
            requirements=job_data.get("requirements", ["React", "TypeScript", "Python"]),
            remote=job_data.get("remote", True),
            logo=job_data.get("logo", ""),
            sourceCareerSite="WTTJ",
            externalUrl=external_url or f"https://www.welcometothejungle.com/en/jobs/{uuid.uuid4()}",
            created_at=datetime.utcnow()
        )
        db.add(new_job)
        db.commit()
        return {"success": True, "action": "created", "id": new_job.id}

@app.post("/jobs/sync-wttj")
async def trigger_wttj_job_sync(email: str = "daddy202028@gmail.com", password: str = "JobSwipeDemo2026!"):
    """Trigger background scraping of live WTTJ tailored jobs"""
    from wttj_scraper import WTTJLiveScraper
    scraper = WTTJLiveScraper(job_service_url="http://localhost:8003")
    result = await scraper.scrape_and_sync_jobs(email=email, password=password)
    return result

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)