"""
Enhanced Profile Management API
Complete user profile, preferences, and jobs database system
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.database import get_db, engine, Base
from shared.models import User, UserProfile, UserPreferences, UserJob, JobApplication, PlatformAccount

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Swiply Profile Management Service",
    description="Complete user profile, preferences, and jobs management system",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# PYDANTIC MODELS FOR REQUEST/RESPONSE
# ============================================================================

class UserProfileCreate(BaseModel):
    """Request model for creating/updating user profile"""
    user_id: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    current_location: Optional[str] = None
    preferred_locations: Optional[List[str]] = None
    willing_to_relocate: Optional[bool] = False
    current_title: Optional[str] = None
    professional_headline: Optional[str] = None
    bio: Optional[str] = None
    summary: Optional[str] = None
    total_experience_years: Optional[int] = None
    current_company: Optional[str] = None
    current_role: Optional[str] = None
    education_level: Optional[str] = None
    field_of_study: Optional[str] = None
    university: Optional[str] = None
    graduation_year: Optional[int] = None
    skills: Optional[List[str]] = None
    languages: Optional[List[Dict[str, str]]] = None
    certifications: Optional[List[str]] = None
    achievements: Optional[List[str]] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    personal_website: Optional[str] = None
    resume_path: Optional[str] = None
    cover_letter_template: Optional[str] = None
    portfolio_files: Optional[List[str]] = None
    availability: Optional[str] = None
    notice_period: Optional[str] = None
    start_date: Optional[str] = None

class UserPreferencesCreate(BaseModel):
    """Request model for creating/updating user preferences"""
    user_id: str
    job_title_keywords: Optional[List[str]] = None
    job_categories: Optional[List[str]] = None
    job_levels: Optional[List[str]] = None
    employment_types: Optional[List[str]] = None
    remote_work_preference: Optional[str] = None
    hybrid_days_per_week: Optional[int] = None
    travel_willingness: Optional[str] = None
    salary_currency: Optional[str] = "EUR"
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_type: Optional[str] = "annual"
    salary_negotiable: Optional[bool] = True
    benefits_important: Optional[List[str]] = None
    company_size_preference: Optional[List[str]] = None
    company_stage_preference: Optional[List[str]] = None
    company_culture_values: Optional[List[str]] = None
    industry_preferences: Optional[List[str]] = None
    industry_blacklist: Optional[List[str]] = None
    preferred_work_locations: Optional[List[str]] = None
    commute_max_time: Optional[int] = None
    willing_to_relocate: Optional[bool] = False
    relocation_preferences: Optional[List[str]] = None
    auto_apply_enabled: Optional[bool] = False
    auto_apply_criteria: Optional[Dict[str, Any]] = None
    application_frequency: Optional[str] = "Daily"
    max_applications_per_day: Optional[int] = 5
    career_goals: Optional[str] = None
    learning_interests: Optional[List[str]] = None
    career_change_interest: Optional[bool] = False
    target_career_field: Optional[str] = None
    email_notifications: Optional[bool] = True
    sms_notifications: Optional[bool] = False
    job_alert_frequency: Optional[str] = "Daily"
    recruiter_contact_preference: Optional[str] = "Email"

class UserJobCreate(BaseModel):
    """Request model for adding a job to user's job list"""
    user_id: str
    job_title: str
    company_name: str
    job_url: str
    platform: Optional[str] = None
    job_description: Optional[str] = None
    job_requirements: Optional[str] = None
    job_benefits: Optional[str] = None
    location: Optional[str] = None
    remote_option: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = "EUR"
    salary_disclosed: Optional[bool] = False
    company_size: Optional[str] = None
    company_industry: Optional[str] = None
    company_description: Optional[str] = None
    company_website: Optional[str] = None
    company_logo_url: Optional[str] = None
    match_score: Optional[float] = None
    match_reasons: Optional[List[str]] = None
    skill_matches: Optional[List[str]] = None
    missing_skills: Optional[List[str]] = None
    job_posted_date: Optional[str] = None
    job_deadline: Optional[str] = None
    is_bookmarked: Optional[bool] = False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_profile_completion(profile: UserProfile) -> int:
    """Calculate profile completion percentage"""
    total_fields = 0
    filled_fields = 0
    
    # Basic fields (weight: 30%)
    basic_fields = [profile.first_name, profile.last_name, profile.phone, 
                   profile.current_location, profile.date_of_birth]
    total_fields += 5
    filled_fields += sum(1 for field in basic_fields if field)
    
    # Professional fields (weight: 40%)
    professional_fields = [profile.current_title, profile.professional_headline,
                          profile.bio, profile.total_experience_years, 
                          profile.current_company, profile.skills]
    total_fields += 6
    filled_fields += sum(1 for field in professional_fields if field)
    
    # Education fields (weight: 15%)
    education_fields = [profile.education_level, profile.university, 
                       profile.graduation_year]
    total_fields += 3
    filled_fields += sum(1 for field in education_fields if field)
    
    # Social/Links fields (weight: 10%)
    social_fields = [profile.linkedin_url, profile.github_url]
    total_fields += 2
    filled_fields += sum(1 for field in social_fields if field)
    
    # Documents fields (weight: 5%)
    doc_fields = [profile.resume_path]
    total_fields += 1
    filled_fields += sum(1 for field in doc_fields if field)
    
    return int((filled_fields / total_fields) * 100)

def serialize_profile(profile: UserProfile) -> Dict[str, Any]:
    """Serialize profile to dictionary"""
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "basic_info": {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "phone": profile.phone,
            "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            "gender": profile.gender,
            "nationality": profile.nationality
        },
        "location": {
            "current_location": profile.current_location,
            "preferred_locations": profile.preferred_locations or [],
            "willing_to_relocate": profile.willing_to_relocate
        },
        "professional": {
            "current_title": profile.current_title,
            "professional_headline": profile.professional_headline,
            "bio": profile.bio,
            "summary": profile.summary,
            "total_experience_years": profile.total_experience_years,
            "current_company": profile.current_company,
            "current_role": profile.current_role
        },
        "education": {
            "education_level": profile.education_level,
            "field_of_study": profile.field_of_study,
            "university": profile.university,
            "graduation_year": profile.graduation_year
        },
        "skills": {
            "skills": profile.skills or [],
            "languages": profile.languages or [],
            "certifications": profile.certifications or [],
            "achievements": profile.achievements or []
        },
        "links": {
            "linkedin_url": profile.linkedin_url,
            "github_url": profile.github_url,
            "portfolio_url": profile.portfolio_url,
            "personal_website": profile.personal_website
        },
        "documents": {
            "resume_path": profile.resume_path,
            "cover_letter_template": profile.cover_letter_template,
            "portfolio_files": profile.portfolio_files or []
        },
        "availability": {
            "availability": profile.availability,
            "notice_period": profile.notice_period,
            "start_date": profile.start_date.isoformat() if profile.start_date else None
        },
        "meta": {
            "profile_completion_percentage": profile.profile_completion_percentage,
            "last_updated_section": profile.last_updated_section,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat()
        }
    }

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {
        "service": "profile-management",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "User Profile Management",
            "Job Preferences",
            "Job Matching & Tracking",
            "Application Tracking",
            "Platform Account Management"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ============================================================================
# USER PROFILE ENDPOINTS
# ============================================================================

@app.post("/profile/create")
async def create_user_profile(
    profile_data: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """Create or update user profile"""
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == profile_data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if profile already exists
        existing_profile = db.query(UserProfile).filter(
            UserProfile.user_id == profile_data.user_id
        ).first()
        
        if existing_profile:
            # Update existing profile
            for key, value in profile_data.dict(exclude={'user_id'}, exclude_none=True).items():
                setattr(existing_profile, key, value)
            
            # Recalculate completion percentage
            existing_profile.profile_completion_percentage = calculate_profile_completion(existing_profile)
            existing_profile.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(existing_profile)
            
            return {
                "success": True,
                "message": "Profile updated successfully",
                "profile": serialize_profile(existing_profile)
            }
        else:
            # Create new profile
            new_profile = UserProfile(
                user_id=profile_data.user_id,
                **profile_data.dict(exclude={'user_id'}, exclude_none=True)
            )
            
            # Calculate completion percentage
            new_profile.profile_completion_percentage = calculate_profile_completion(new_profile)
            
            db.add(new_profile)
            db.commit()
            db.refresh(new_profile)
            
            return {
                "success": True,
                "message": "Profile created successfully",
                "profile": serialize_profile(new_profile)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create/update profile: {str(e)}")

@app.get("/profile/{user_id}")
async def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    """Get user profile"""
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if not profile:
            return {
                "success": False,
                "message": "Profile not found",
                "profile": None
            }
        
        return {
            "success": True,
            "profile": serialize_profile(profile)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")

@app.delete("/profile/{user_id}")
async def delete_user_profile(user_id: str, db: Session = Depends(get_db)):
    """Delete user profile"""
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        db.delete(profile)
        db.commit()
        
        return {
            "success": True,
            "message": "Profile deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete profile: {str(e)}")

# ============================================================================
# USER PREFERENCES ENDPOINTS
# ============================================================================

@app.post("/preferences/create")
async def create_user_preferences(
    pref_data: UserPreferencesCreate,
    db: Session = Depends(get_db)
):
    """Create or update user preferences"""
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == pref_data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if preferences already exist
        existing_prefs = db.query(UserPreferences).filter(
            UserPreferences.user_id == pref_data.user_id
        ).first()
        
        if existing_prefs:
            # Update existing preferences
            for key, value in pref_data.dict(exclude={'user_id'}, exclude_none=True).items():
                setattr(existing_prefs, key, value)
            
            existing_prefs.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(existing_prefs)
            
            return {
                "success": True,
                "message": "Preferences updated successfully",
                "preferences": existing_prefs
            }
        else:
            # Create new preferences
            new_prefs = UserPreferences(
                user_id=pref_data.user_id,
                **pref_data.dict(exclude={'user_id'}, exclude_none=True)
            )
            
            db.add(new_prefs)
            db.commit()
            db.refresh(new_prefs)
            
            return {
                "success": True,
                "message": "Preferences created successfully",
                "preferences": new_prefs
            }
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create/update preferences: {str(e)}")

@app.get("/preferences/{user_id}")
async def get_user_preferences(user_id: str, db: Session = Depends(get_db)):
    """Get user preferences"""
    try:
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        
        if not preferences:
            return {
                "success": False,
                "message": "Preferences not found",
                "preferences": None
            }
        
        return {
            "success": True,
            "preferences": preferences
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get preferences: {str(e)}")

# ============================================================================
# USER JOBS ENDPOINTS
# ============================================================================

@app.post("/jobs/add")
async def add_user_job(
    job_data: UserJobCreate,
    db: Session = Depends(get_db)
):
    """Add a job to user's job list"""
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == job_data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create new job
        new_job = UserJob(
            **job_data.dict(exclude_none=True)
        )
        
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        
        return {
            "success": True,
            "message": "Job added successfully",
            "job": new_job
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add job: {str(e)}")

@app.get("/jobs/{user_id}")
async def get_user_jobs(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get user's job list"""
    try:
        jobs = db.query(UserJob).filter(
            UserJob.user_id == user_id
        ).order_by(
            UserJob.discovered_date.desc()
        ).limit(limit).offset(offset).all()
        
        return {
            "success": True,
            "total": len(jobs),
            "jobs": jobs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get jobs: {str(e)}")

@app.get("/jobs/{user_id}/bookmarked")
async def get_bookmarked_jobs(user_id: str, db: Session = Depends(get_db)):
    """Get user's bookmarked jobs"""
    try:
        jobs = db.query(UserJob).filter(
            UserJob.user_id == user_id,
            UserJob.is_bookmarked == True
        ).all()
        
        return {
            "success": True,
            "total": len(jobs),
            "jobs": jobs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get bookmarked jobs: {str(e)}")

# ============================================================================
# COMPLETE USER DATA ENDPOINT
# ============================================================================

@app.get("/user/complete-data/{user_id}")
async def get_complete_user_data(user_id: str, db: Session = Depends(get_db)):
    """Get complete user data including profile, preferences, and jobs"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        preferences = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
        jobs = db.query(UserJob).filter(UserJob.user_id == user_id).limit(20).all()
        applications = db.query(JobApplication).filter(JobApplication.user_id == user_id).limit(20).all()
        platform_accounts = db.query(PlatformAccount).filter(PlatformAccount.user_id == user_id).all()
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "email_verified": user.email_verified,
                "created_at": user.created_at.isoformat()
            },
            "profile": serialize_profile(profile) if profile else None,
            "preferences": preferences,
            "jobs": {
                "total": len(jobs),
                "recent": jobs
            },
            "applications": {
                "total": len(applications),
                "recent": applications
            },
            "platform_accounts": platform_accounts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get complete user data: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PROFILE_PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
