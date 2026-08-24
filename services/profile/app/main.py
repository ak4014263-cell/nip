"""
Profile Analysis Service
Complete user profile management system with database storage
Handles profile, preferences, and job data collection
"""
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import PyPDF2
import re
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.database import get_db, engine, Base
from shared.models import User, UserProfile, UserPreferences, UserJob, JobApplication, PlatformAccount

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Swiply Profile Service",
    description="Complete user profile management with database storage",
    version="2.0.0"
)

app = FastAPI(
    title="Swiply Profile Service",
    description="Complete user profile management with database storage",
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
# PYDANTIC MODELS FOR API
# ============================================================================

class ProfileCreateRequest(BaseModel):
    """Request to create/update user profile"""
    user_id: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    current_location: Optional[str] = None
    professional_headline: Optional[str] = None
    bio: Optional[str] = None
    summary: Optional[str] = None
    current_title: Optional[str] = None
    total_experience_years: Optional[int] = None
    current_company: Optional[str] = None
    current_role: Optional[str] = None
    education_level: Optional[str] = None
    field_of_study: Optional[str] = None
    university: Optional[str] = None
    graduation_year: Optional[int] = None
    skills: Optional[List[str]] = []
    languages: Optional[List[Dict[str, str]]] = []
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    resume_path: Optional[str] = None
    availability: Optional[str] = None


class PreferencesCreateRequest(BaseModel):
    """Request to create/update user preferences"""
    user_id: str
    job_title_keywords: Optional[List[str]] = []
    job_categories: Optional[List[str]] = []
    job_levels: Optional[List[str]] = []
    employment_types: Optional[List[str]] = []
    remote_work_preference: Optional[str] = "Any"
    salary_currency: Optional[str] = "EUR"
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_type: Optional[str] = "annual"
    company_size_preference: Optional[List[str]] = []
    industry_preferences: Optional[List[str]] = []
    preferred_work_locations: Optional[List[str]] = []
    willing_to_relocate: Optional[bool] = False
    auto_apply_enabled: Optional[bool] = False
    max_applications_per_day: Optional[int] = 5
    career_goals: Optional[str] = None
    email_notifications: Optional[bool] = True


class JobAddRequest(BaseModel):
    """Request to add a job to user's job list"""
    user_id: str
    job_title: str
    company_name: str
    job_url: str
    platform: str
    job_description: Optional[str] = None
    location: Optional[str] = None
    remote_option: Optional[str] = None
    employment_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = "EUR"
    match_score: Optional[float] = None
    match_reasons: Optional[List[str]] = []


class ProfileResponse(BaseModel):
    """Response with user profile data"""
    success: bool
    profile: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class PreferencesResponse(BaseModel):
    """Response with user preferences data"""
    success: bool
    preferences: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

# Skills database (simplified - in production, use comprehensive taxonomy)
TECH_SKILLS = {
    'frontend': ['react', 'vue', 'angular', 'javascript', 'typescript', 'html', 'css', 'sass', 'webpack', 'vite'],
    'backend': ['node.js', 'python', 'java', 'php', 'ruby', 'go', 'rust', 'c++', 'c#', 'scala'],
    'databases': ['postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'cassandra', 'oracle'],
    'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'gitlab'],
    'frameworks': ['express', 'django', 'flask', 'spring', 'laravel', 'rails', 'gin', 'fastapi'],
    'tools': ['git', 'jira', 'confluence', 'figma', 'sketch', 'postman', 'grafana', 'prometheus']
}

ALL_SKILLS = []
for category_skills in TECH_SKILLS.values():
    ALL_SKILLS.extend(category_skills)

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    try:
        import io
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"

def extract_skills(text: str) -> List[str]:
    """Extract technical skills from text"""
    text_lower = text.lower()
    found_skills = []
    
    for skill in ALL_SKILLS:
        # Look for skill as whole word
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill)
    
    return list(set(found_skills))  # Remove duplicates

def extract_experience_years(text: str) -> int:
    """Extract years of experience from text"""
    # Look for patterns like "5 years of experience", "3+ years", etc.
    patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
        r'(?:experience|exp).*?(\d+)\+?\s*years?',
        r'(\d+)\+?\s*ans?\s*d\'exp[eé]rience',
        r'exp[eé]rience.*?(\d+)\+?\s*ans?'
    ]
    
    years = []
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        for match in matches:
            try:
                years.append(int(match))
            except ValueError:
                continue
    
    return max(years) if years else 0

def extract_languages(text: str) -> List[Dict[str, str]]:
    """Extract languages and levels"""
    languages = []
    
    # Common language patterns
    lang_patterns = {
        'english': ['english', 'anglais'],
        'french': ['french', 'français', 'francais'],
        'spanish': ['spanish', 'español', 'espagnol'],
        'german': ['german', 'deutsch', 'allemand'],
        'italian': ['italian', 'italiano', 'italien']
    }
    
    level_patterns = {
        'native': ['native', 'natif', 'maternelle'],
        'fluent': ['fluent', 'fluide', 'courante'],
        'advanced': ['advanced', 'avancé', 'c1', 'c2'],
        'intermediate': ['intermediate', 'intermédiaire', 'b1', 'b2'],
        'beginner': ['beginner', 'débutant', 'a1', 'a2']
    }
    
    text_lower = text.lower()
    
    for lang, patterns in lang_patterns.items():
        for pattern in patterns:
            if pattern in text_lower:
                # Try to find level near the language
                level = 'intermediate'  # default
                for lvl, lvl_patterns in level_patterns.items():
                    for lvl_pattern in lvl_patterns:
                        # Look for level within 50 characters of language mention
                        lang_pos = text_lower.find(pattern)
                        if lang_pos != -1:
                            context = text_lower[lang_pos:lang_pos + 50]
                            if lvl_pattern in context:
                                level = lvl
                                break
                
                languages.append({
                    'language': lang.title(),
                    'level': level
                })
                break
    
    return languages

def extract_education(text: str) -> List[Dict[str, Any]]:
    """Extract education information"""
    education = []
    
    # Look for degree patterns
    degree_patterns = [
        r'(master|m\.?s\.?|m\.?a\.?|mba|masters?)',
        r'(bachelor|b\.?s\.?|b\.?a\.?|licence|bachelors?)',
        r'(phd|ph\.?d\.?|doctorate|doctorat)',
        r'(engineer|ingénieur|engineering)'
    ]
    
    university_indicators = ['university', 'université', 'college', 'école', 'institute', 'institut']
    
    lines = text.split('\n')
    for line in lines:
        line_lower = line.lower()
        
        # Check if line contains degree
        for pattern in degree_patterns:
            if re.search(pattern, line_lower):
                # Check if line also contains university indicator
                has_university = any(indicator in line_lower for indicator in university_indicators)
                
                if has_university or len(line.strip()) > 10:  # Reasonable length
                    education.append({
                        'degree': line.strip(),
                        'year': None  # Could extract year with more complex regex
                    })
                break
    
    return education[:3]  # Limit to 3 entries

@app.get("/")
async def root():
    return {"service": "profile", "status": "running", "version": "2.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# ============================================================================
# USER PROFILE ENDPOINTS
# ============================================================================

@app.post("/profile/create")
async def create_or_update_profile(
    request: ProfileCreateRequest,
    db: Session = Depends(get_db)
):
    """Create or update user profile"""
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if profile exists
        profile = db.query(UserProfile).filter(UserProfile.user_id == request.user_id).first()
        
        if profile:
            # Update existing profile
            profile.first_name = request.first_name
            profile.last_name = request.last_name
            profile.phone = request.phone
            profile.current_location = request.current_location
            profile.professional_headline = request.professional_headline
            profile.bio = request.bio
            profile.summary = request.summary
            profile.current_title = request.current_title
            profile.total_experience_years = request.total_experience_years
            profile.current_company = request.current_company
            profile.current_role = request.current_role
            profile.education_level = request.education_level
            profile.field_of_study = request.field_of_study
            profile.university = request.university
            profile.graduation_year = request.graduation_year
            profile.skills = request.skills
            profile.languages = request.languages
            profile.linkedin_url = request.linkedin_url
            profile.github_url = request.github_url
            profile.portfolio_url = request.portfolio_url
            profile.resume_path = request.resume_path
            profile.availability = request.availability
            profile.updated_at = datetime.utcnow()
            
            # Calculate profile completion
            profile.profile_completion_percentage = calculate_profile_completion(profile)
            
            message = "Profile updated successfully"
        else:
            # Create new profile
            profile = UserProfile(
                user_id=request.user_id,
                first_name=request.first_name,
                last_name=request.last_name,
                phone=request.phone,
                current_location=request.current_location,
                professional_headline=request.professional_headline,
                bio=request.bio,
                summary=request.summary,
                current_title=request.current_title,
                total_experience_years=request.total_experience_years,
                current_company=request.current_company,
                current_role=request.current_role,
                education_level=request.education_level,
                field_of_study=request.field_of_study,
                university=request.university,
                graduation_year=request.graduation_year,
                skills=request.skills,
                languages=request.languages,
                linkedin_url=request.linkedin_url,
                github_url=request.github_url,
                portfolio_url=request.portfolio_url,
                resume_path=request.resume_path,
                availability=request.availability
            )
            
            # Calculate profile completion
            profile.profile_completion_percentage = calculate_profile_completion(profile)
            
            db.add(profile)
            message = "Profile created successfully"
        
        db.commit()
        db.refresh(profile)
        
        return {
            "success": True,
            "message": message,
            "profile": profile_to_dict(profile),
            "completion_percentage": profile.profile_completion_percentage
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create/update profile: {str(e)}")


@app.get("/profile/{user_id}")
async def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    """Get user profile by user ID"""
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
            "profile": profile_to_dict(profile),
            "completion_percentage": profile.profile_completion_percentage
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")


# ============================================================================
# USER PREFERENCES ENDPOINTS
# ============================================================================

@app.post("/preferences/create")
async def create_or_update_preferences(
    request: PreferencesCreateRequest,
    db: Session = Depends(get_db)
):
    """Create or update user preferences"""
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if preferences exist
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == request.user_id
        ).first()
        
        if preferences:
            # Update existing preferences
            preferences.job_title_keywords = request.job_title_keywords
            preferences.job_categories = request.job_categories
            preferences.job_levels = request.job_levels
            preferences.employment_types = request.employment_types
            preferences.remote_work_preference = request.remote_work_preference
            preferences.salary_currency = request.salary_currency
            preferences.salary_min = request.salary_min
            preferences.salary_max = request.salary_max
            preferences.salary_type = request.salary_type
            preferences.company_size_preference = request.company_size_preference
            preferences.industry_preferences = request.industry_preferences
            preferences.preferred_work_locations = request.preferred_work_locations
            preferences.willing_to_relocate = request.willing_to_relocate
            preferences.auto_apply_enabled = request.auto_apply_enabled
            preferences.max_applications_per_day = request.max_applications_per_day
            preferences.career_goals = request.career_goals
            preferences.email_notifications = request.email_notifications
            preferences.updated_at = datetime.utcnow()
            
            message = "Preferences updated successfully"
        else:
            # Create new preferences
            preferences = UserPreferences(
                user_id=request.user_id,
                job_title_keywords=request.job_title_keywords,
                job_categories=request.job_categories,
                job_levels=request.job_levels,
                employment_types=request.employment_types,
                remote_work_preference=request.remote_work_preference,
                salary_currency=request.salary_currency,
                salary_min=request.salary_min,
                salary_max=request.salary_max,
                salary_type=request.salary_type,
                company_size_preference=request.company_size_preference,
                industry_preferences=request.industry_preferences,
                preferred_work_locations=request.preferred_work_locations,
                willing_to_relocate=request.willing_to_relocate,
                auto_apply_enabled=request.auto_apply_enabled,
                max_applications_per_day=request.max_applications_per_day,
                career_goals=request.career_goals,
                email_notifications=request.email_notifications
            )
            
            db.add(preferences)
            message = "Preferences created successfully"
        
        db.commit()
        db.refresh(preferences)
        
        return {
            "success": True,
            "message": message,
            "preferences": preferences_to_dict(preferences)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create/update preferences: {str(e)}")


@app.get("/preferences/{user_id}")
async def get_user_preferences(user_id: str, db: Session = Depends(get_db)):
    """Get user preferences by user ID"""
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
            "preferences": preferences_to_dict(preferences)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get preferences: {str(e)}")


# ============================================================================
# USER JOBS ENDPOINTS
# ============================================================================

@app.post("/jobs/add")
async def add_user_job(request: JobAddRequest, db: Session = Depends(get_db)):
    """Add a job to user's job list"""
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if job already exists for this user
        existing_job = db.query(UserJob).filter(
            UserJob.user_id == request.user_id,
            UserJob.job_url == request.job_url
        ).first()
        
        if existing_job:
            return {
                "success": False,
                "message": "Job already exists in user's list",
                "job": job_to_dict(existing_job)
            }
        
        # Create new job
        job = UserJob(
            user_id=request.user_id,
            job_title=request.job_title,
            company_name=request.company_name,
            job_url=request.job_url,
            platform=request.platform,
            job_description=request.job_description,
            location=request.location,
            remote_option=request.remote_option,
            employment_type=request.employment_type,
            salary_min=request.salary_min,
            salary_max=request.salary_max,
            salary_currency=request.salary_currency,
            match_score=request.match_score,
            match_reasons=request.match_reasons,
            job_status="active"
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        return {
            "success": True,
            "message": "Job added successfully",
            "job": job_to_dict(job)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add job: {str(e)}")


@app.get("/jobs/{user_id}")
async def get_user_jobs(
    user_id: str,
    status: Optional[str] = "active",
    db: Session = Depends(get_db)
):
    """Get all jobs for a user"""
    try:
        query = db.query(UserJob).filter(UserJob.user_id == user_id)
        
        if status:
            query = query.filter(UserJob.job_status == status)
        
        jobs = query.order_by(UserJob.discovered_date.desc()).all()
        
        return {
            "success": True,
            "jobs": [job_to_dict(job) for job in jobs],
            "total": len(jobs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get jobs: {str(e)}")


@app.get("/jobs/{user_id}/bookmarked")
async def get_bookmarked_jobs(user_id: str, db: Session = Depends(get_db)):
    """Get bookmarked jobs for a user"""
    try:
        jobs = db.query(UserJob).filter(
            UserJob.user_id == user_id,
            UserJob.is_bookmarked == True
        ).order_by(UserJob.discovered_date.desc()).all()
        
        return {
            "success": True,
            "jobs": [job_to_dict(job) for job in jobs],
            "total": len(jobs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get bookmarked jobs: {str(e)}")


@app.put("/jobs/{job_id}/bookmark")
async def toggle_job_bookmark(job_id: str, db: Session = Depends(get_db)):
    """Toggle bookmark status for a job"""
    try:
        job = db.query(UserJob).filter(UserJob.id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job.is_bookmarked = not job.is_bookmarked
        db.commit()
        
        return {
            "success": True,
            "message": "Bookmark toggled successfully",
            "is_bookmarked": job.is_bookmarked
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to toggle bookmark: {str(e)}")


# ============================================================================
# COMPLETE USER DATA ENDPOINT
# ============================================================================

@app.get("/user/{user_id}/complete")
async def get_complete_user_data(user_id: str, db: Session = Depends(get_db)):
    """Get complete user data including profile, preferences, and jobs"""
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get profile
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        # Get preferences
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == user_id
        ).first()
        
        # Get jobs
        jobs = db.query(UserJob).filter(
            UserJob.user_id == user_id,
            UserJob.job_status == "active"
        ).order_by(UserJob.discovered_date.desc()).limit(20).all()
        
        # Get applications
        applications = db.query(JobApplication).filter(
            JobApplication.user_id == user_id
        ).order_by(JobApplication.applied_date.desc()).limit(10).all()
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "email_verified": user.email_verified
            },
            "profile": profile_to_dict(profile) if profile else None,
            "preferences": preferences_to_dict(preferences) if preferences else None,
            "jobs": {
                "total": len(jobs),
                "recent": [job_to_dict(job) for job in jobs]
            },
            "applications": {
                "total": len(applications),
                "recent": [application_to_dict(app) for app in applications]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get complete user data: {str(e)}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_profile_completion(profile: UserProfile) -> int:
    """Calculate profile completion percentage"""
    total_fields = 20
    filled_fields = 0
    
    if profile.first_name: filled_fields += 1
    if profile.last_name: filled_fields += 1
    if profile.phone: filled_fields += 1
    if profile.current_location: filled_fields += 1
    if profile.professional_headline: filled_fields += 1
    if profile.bio: filled_fields += 1
    if profile.current_title: filled_fields += 1
    if profile.total_experience_years: filled_fields += 1
    if profile.current_company: filled_fields += 1
    if profile.education_level: filled_fields += 1
    if profile.field_of_study: filled_fields += 1
    if profile.university: filled_fields += 1
    if profile.skills and len(profile.skills) > 0: filled_fields += 1
    if profile.languages and len(profile.languages) > 0: filled_fields += 1
    if profile.linkedin_url: filled_fields += 1
    if profile.github_url: filled_fields += 1
    if profile.resume_path: filled_fields += 1
    if profile.availability: filled_fields += 1
    if profile.summary: filled_fields += 1
    if profile.graduation_year: filled_fields += 1
    
    return int((filled_fields / total_fields) * 100)


def profile_to_dict(profile: UserProfile) -> Dict[str, Any]:
    """Convert profile to dictionary"""
    if not profile:
        return None
    
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "phone": profile.phone,
        "current_location": profile.current_location,
        "professional_headline": profile.professional_headline,
        "bio": profile.bio,
        "summary": profile.summary,
        "current_title": profile.current_title,
        "total_experience_years": profile.total_experience_years,
        "current_company": profile.current_company,
        "current_role": profile.current_role,
        "education_level": profile.education_level,
        "field_of_study": profile.field_of_study,
        "university": profile.university,
        "graduation_year": profile.graduation_year,
        "skills": profile.skills,
        "languages": profile.languages,
        "linkedin_url": profile.linkedin_url,
        "github_url": profile.github_url,
        "portfolio_url": profile.portfolio_url,
        "resume_path": profile.resume_path,
        "availability": profile.availability,
        "profile_completion_percentage": profile.profile_completion_percentage,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
    }


def preferences_to_dict(preferences: UserPreferences) -> Dict[str, Any]:
    """Convert preferences to dictionary"""
    if not preferences:
        return None
    
    return {
        "id": preferences.id,
        "user_id": preferences.user_id,
        "job_title_keywords": preferences.job_title_keywords,
        "job_categories": preferences.job_categories,
        "job_levels": preferences.job_levels,
        "employment_types": preferences.employment_types,
        "remote_work_preference": preferences.remote_work_preference,
        "salary_currency": preferences.salary_currency,
        "salary_min": preferences.salary_min,
        "salary_max": preferences.salary_max,
        "salary_type": preferences.salary_type,
        "company_size_preference": preferences.company_size_preference,
        "industry_preferences": preferences.industry_preferences,
        "preferred_work_locations": preferences.preferred_work_locations,
        "willing_to_relocate": preferences.willing_to_relocate,
        "auto_apply_enabled": preferences.auto_apply_enabled,
        "max_applications_per_day": preferences.max_applications_per_day,
        "career_goals": preferences.career_goals,
        "email_notifications": preferences.email_notifications,
        "created_at": preferences.created_at.isoformat() if preferences.created_at else None,
        "updated_at": preferences.updated_at.isoformat() if preferences.updated_at else None
    }


def job_to_dict(job: UserJob) -> Dict[str, Any]:
    """Convert job to dictionary"""
    if not job:
        return None
    
    return {
        "id": job.id,
        "user_id": job.user_id,
        "job_title": job.job_title,
        "company_name": job.company_name,
        "job_url": job.job_url,
        "platform": job.platform,
        "job_description": job.job_description,
        "location": job.location,
        "remote_option": job.remote_option,
        "employment_type": job.employment_type,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "salary_currency": job.salary_currency,
        "match_score": job.match_score,
        "match_reasons": job.match_reasons,
        "job_status": job.job_status,
        "is_bookmarked": job.is_bookmarked,
        "discovered_date": job.discovered_date.isoformat() if job.discovered_date else None
    }


def application_to_dict(application: JobApplication) -> Dict[str, Any]:
    """Convert application to dictionary"""
    if not application:
        return None
    
    return {
        "id": application.id,
        "user_id": application.user_id,
        "job_id": application.job_id,
        "status": application.status,
        "application_method": application.application_method,
        "platform_used": application.platform_used,
        "applied_date": application.applied_date.isoformat() if application.applied_date else None,
        "auto_applied": application.auto_applied
    }


@app.get("/")
async def root():
    return {"service": "profile", "status": "running", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/analyze-cv")
async def analyze_cv(file: UploadFile = File(...)):
    """Analyze uploaded CV and extract candidate profile"""
    
    if not file.filename.lower().endswith('.pdf'):
        return {"error": "Only PDF files are supported"}
    
    # Read file content
    content = await file.read()
    
    # Extract text
    text = extract_text_from_pdf(content)
    
    if text.startswith("Error"):
        return {"error": text}
    
    # Extract information
    skills = extract_skills(text)
    experience_years = extract_experience_years(text)
    languages = extract_languages(text)
    education = extract_education(text)
    
    # Create profile
    profile = {
        "candidate": {
            "name": "Extracted from CV",  # Would need more sophisticated extraction
            "experience_years": experience_years,
            "skills": skills,
            "languages": languages,
            "education": education,
            "preferred_locations": ["Paris", "Remote"],  # Default - would ask user
            "preferred_contracts": ["CDI", "CDD"],
            "salary_expectation": {
                "min": 45000,
                "max": 65000,
                "currency": "EUR"
            }
        },
        "analysis": {
            "skills_count": len(skills),
            "experience_level": "senior" if experience_years >= 5 else "mid" if experience_years >= 2 else "junior",
            "text_length": len(text),
            "confidence": 0.8  # Placeholder confidence score
        }
    }
    
    return profile

@app.get("/candidate-profile/{candidate_id}")
async def get_candidate_profile(candidate_id: str):
    """Get stored candidate profile"""
    # Mock profile - in production, retrieve from database
    return {
        "candidate": {
            "id": candidate_id,
            "name": "John Doe",
            "experience_years": 4,
            "skills": ["react", "typescript", "node.js", "postgresql", "aws"],
            "languages": [
                {"language": "English", "level": "fluent"},
                {"language": "French", "level": "intermediate"}
            ],
            "education": [
                {"degree": "Master in Computer Science", "year": 2020}
            ],
            "preferred_locations": ["Paris", "Lyon", "Remote"],
            "preferred_contracts": ["CDI"],
            "salary_expectation": {
                "min": 50000,
                "max": 70000,
                "currency": "EUR"
            }
        }
    }

@app.post("/calculate-match")
async def calculate_match_score(match_data: dict):
    """Calculate job match score for candidate"""
    candidate = match_data.get("candidate", {})
    job = match_data.get("job", {})
    
    if not candidate or not job:
        return {"error": "Missing candidate or job data"}
    
    # Skills matching
    candidate_skills = set(skill.lower() for skill in candidate.get("skills", []))
    job_requirements = set(req.lower() for req in job.get("requirements", []))
    
    skills_intersection = candidate_skills.intersection(job_requirements)
    skills_score = (len(skills_intersection) / max(len(job_requirements), 1)) * 100
    
    # Experience matching
    candidate_exp = candidate.get("experience_years", 0)
    required_exp_match = re.search(r'(\d+)\+?\s*years?', ' '.join(job_requirements))
    required_exp = int(required_exp_match.group(1)) if required_exp_match else 2
    
    exp_score = min(100, (candidate_exp / max(required_exp, 1)) * 100)
    
    # Location matching
    candidate_locations = [loc.lower() for loc in candidate.get("preferred_locations", [])]
    job_location = job.get("location", "").lower()
    
    location_score = 100 if any(loc in job_location for loc in candidate_locations) else 50
    
    # Remote preference
    if job.get("remote", False) and "remote" in candidate_locations:
        location_score = 100
    
    # Salary matching
    salary_score = 100  # Default if no salary info
    if job.get("salaryMin") and candidate.get("salary_expectation", {}).get("min"):
        job_salary = job.get("salaryMax", job.get("salaryMin"))
        candidate_min = candidate["salary_expectation"]["min"]
        salary_score = 100 if job_salary >= candidate_min else 70
    
    # Calculate weighted overall score
    weights = {
        "skills": 0.4,
        "experience": 0.25,
        "location": 0.2,
        "salary": 0.15
    }
    
    overall_score = (
        skills_score * weights["skills"] +
        exp_score * weights["experience"] +
        location_score * weights["location"] +
        salary_score * weights["salary"]
    )
    
    return {
        "overall_score": round(overall_score),
        "breakdown": {
            "skills": round(skills_score),
            "experience": round(exp_score),
            "location": round(location_score),
            "salary": round(salary_score)
        },
        "matched_skills": list(skills_intersection),
        "missing_skills": list(job_requirements - candidate_skills),
        "recommendation": "strong_match" if overall_score >= 80 else "good_match" if overall_score >= 60 else "weak_match"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)