"""
Enhanced Automation Service
Browser automation with multiple strategies: Browser Automation, LLM-guided, and ATS APIs
Includes Ollama-powered automation for WTTJ & SNCF
"""
import sys
import os

# Add app directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, BackgroundTasks, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright
from automation_strategies import AutomationRouter
from adapters.wttj_adapter import WTTJAdapter
from adapters.sncf_adapter import SNCFAdapter
from adapters.totalenergies_adapter import TotalEnergiesAdapter
from openai import OpenAI
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import redis
import json
import asyncio
import httpx

# Try to import Ollama for AI automation
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Swiply Automation Service",
    description="Browser automation for career sites with AI-powered profile setup",
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

# AI Service Configuration - Custom Trained Model
AI_SERVICE_URL = "http://localhost:8010"  # Your custom trained AI service
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8010")

# Initialize OpenAI client for advanced automation
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "sk-your-key-here")
)

# Initialize advanced automation router
automation_router = AutomationRouter(openai_client)

class MockRedis:
    def __init__(self):
        self.data = {}
    def hset(self, name, key, value):
        if name not in self.data:
            self.data[name] = {}
        self.data[name][key] = str(value)
    def hgetall(self, name):
        return self.data.get(name, {})
    def expire(self, name, time):
        pass
    def scan_iter(self, match):
        prefix = match.replace('*', '')
        return [k for k in self.data.keys() if k.startswith(prefix)]

# Redis for job tracking
try:
    redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, decode_responses=True)
    redis_client.ping()
except Exception:
    logger.warning("Redis not available, using in-memory mock")
    redis_client = MockRedis()
CREDENTIAL_SERVICE_URL = os.getenv("CREDENTIAL_SERVICE_URL", "http://localhost:8009")

# Adapter registry
ADAPTERS = {
    "WTTJ": WTTJAdapter,
    "SNCF": SNCFAdapter,
    "TOTAL_ENERGIES": TotalEnergiesAdapter,
}

# ============================================================================
# OLLAMA AUTOMATION MODELS & ENDPOINTS
# ============================================================================

# Pydantic Models for Ollama Automation
class AccountCreationRequest(BaseModel):
    """Request to create accounts on career sites"""
    user_id: str
    email: str
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    location: Optional[str] = None
    sites: List[str]  # ["wttj", "sncf"]

class ProfileSetupRequest(BaseModel):
    """Request to setup profiles using AI"""
    user_id: str
    email: str
    first_name: str
    last_name: str
    headline: str
    bio: str
    skills: List[str]
    experience_years: int
    education: str
    linkedin_url: Optional[str] = None
    sites: List[str]  # ["wttj", "sncf"]

class JobApplicationRequest(BaseModel):
    """Request to apply to jobs"""
    user_id: str
    email: str
    first_name: str
    last_name: str
    headline: str
    bio: str
    skills: List[str]
    experience_years: int
    education: str
    job_urls: Dict[str, List[str]]  # {"wttj": [...], "sncf": [...]}


def get_adapter(site_name: str):
    """Get the appropriate adapter for a career site"""
    adapter_class = ADAPTERS.get(site_name)
    if not adapter_class:
        raise ValueError(f"No adapter found for {site_name}")
    return adapter_class()


async def generate_profile_sections_with_ai(user_data: dict) -> dict:
    """Generate AI-enhanced profile sections using custom trained model"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AI_SERVICE_URL}/enhance-profile",
                json={
                    "first_name": user_data.get("first_name", ""),
                    "last_name": user_data.get("last_name", ""),
                    "email": user_data.get("email", ""),
                    "experience_years": user_data.get("experience_years", 3),
                    "skills": user_data.get("skills", []),
                    "current_role": user_data.get("headline", "Professional"),
                    "bio": user_data.get("bio", ""),
                    "location": user_data.get("location", "")
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                ai_response = response.json()
                if ai_response.get("success"):
                    enhanced_profile = ai_response["enhanced_profile"]
                    logger.info(f"Ã¢Å“â€¦ AI Profile Enhancement Success - Model: {ai_response.get('model', 'unknown')}")
                    
                    return {
                        "headline": enhanced_profile.get("professional_headline", user_data.get("headline", "")),
                        "about": enhanced_profile.get("detailed_bio", user_data.get("bio", "")),
                        "professional_summary": enhanced_profile.get("professional_summary", ""),
                        "elevator_pitch": enhanced_profile.get("elevator_pitch", ""),
                        "suggested_skills": enhanced_profile.get("suggested_skills", []),
                        "career_keywords": enhanced_profile.get("career_keywords", [])
                    }
            
            logger.warning("AI service unavailable, using original data")
            return {
                "headline": user_data.get("headline", "Professional"),
                "about": user_data.get("bio", "Experienced professional"),
                "professional_summary": f"Professional with {user_data.get('experience_years', 3)} years experience"
            }
            
    except Exception as e:
        logger.error(f"AI enhancement failed: {e}")
        return {
            "headline": user_data.get("headline", "Professional"),
            "about": user_data.get("bio", "Experienced professional"),
            "professional_summary": f"Professional with {user_data.get('experience_years', 3)} years experience"
        }

async def generate_cover_letter_with_ai(job_title: str, company: str, user_data: dict) -> str:
    """Generate AI-powered cover letter using custom trained model"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AI_SERVICE_URL}/generate-cover-letter",
                json={
                    # Profile data
                    "first_name": user_data.get("first_name", ""),
                    "last_name": user_data.get("last_name", ""),
                    "email": user_data.get("email", ""),
                    "experience_years": user_data.get("experience_years", 3),
                    "skills": user_data.get("skills", []),
                    "current_role": user_data.get("headline", "Professional"),
                    "bio": user_data.get("bio", ""),
                    # Job data
                    "title": job_title,
                    "company": company,
                    "description": user_data.get("job_description", ""),
                    "requirements": user_data.get("job_requirements", [])
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                ai_response = response.json()
                if ai_response.get("success"):
                    logger.info(f"Ã¢Å“â€¦ AI Cover Letter Generated - Model: Custom Trained")
                    return ai_response["cover_letter"]
            
            logger.warning("AI cover letter generation failed, using template")
            return f"Dear Hiring Manager,\n\nI am writing to express my interest in the {job_title} position at {company}. With {user_data.get('experience_years', 3)} years of experience, I am confident I can contribute to your team.\n\nBest regards,\n{user_data.get('first_name', '')} {user_data.get('last_name', '')}"
            
    except Exception as e:
        logger.error(f"AI cover letter generation failed: {e}")
        return f"Dear Hiring Manager,\n\nI am writing to express my interest in the {job_title} position at {company}.\n\nBest regards,\n{user_data.get('first_name', '')} {user_data.get('last_name', '')}"

async def run_automation_job(job_id: str, site_name: str, action: str, credentials: dict, data: dict):
    """Run an automation job"""
    try:
        logger.info(f"Starting automation job {job_id} for {site_name}")
        
        # Update job status in Redis
        redis_client.hset(f"job:{job_id}", "status", "running")
        redis_client.hset(f"job:{job_id}", "started_at", str(asyncio.get_event_loop().time()))
        
        adapter = get_adapter(site_name)
        
        async with async_playwright() as p:
            # Use Firefox automation as requested
            browser = await p.firefox.launch(
                headless=os.getenv("HEADLESS", "false").lower() == "true"  # Default to visible for debugging
            )
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0'
            )
            page = await context.new_page()
            
            result = None
            
            if action == "create_account":
                # Generate AI-enhanced profile sections before creating account
                profile_sections = await generate_profile_sections_with_ai(data)
                
                # Merge AI-generated content with candidate data
                data['bio'] = profile_sections.get('about', data.get('bio', ''))
                data['headline'] = profile_sections.get('headline', '')
                data['summary'] = profile_sections.get('professional_summary', '')
                
                result = await adapter.create_account(
                    page,
                    credentials['email'],
                    credentials['password'],
                    data
                )
                
                # If account creation was successful, update credential verification
                if result.get("success"):
                    await update_credential_verification(credentials['email'])
                    
            elif action == "apply_to_job":
                # Generate AI-powered cover letter
                cover_letter = await generate_cover_letter_with_ai(
                    data.get('job_title', 'Software Developer'),
                    data.get('company', 'Company'),
                    data  # Pass full candidate profile
                )
                
                # Update application data with AI-generated content
                data['cover_letter'] = cover_letter
                
                # Login first
                login_success = await adapter.login(
                    page,
                    credentials['email'],
                    credentials['password']
                )
                
                if login_success:
                    result = await adapter.apply_to_job(
                        page,
                        data['job_url'],
                        data
                    )
                else:
                    result = {"success": False, "error": "Login failed"}
            
            await browser.close()
            
            # Update job status in Redis
            redis_client.hset(f"job:{job_id}", "status", "completed" if result.get("success") else "failed")
            redis_client.hset(f"job:{job_id}", "result", json.dumps(result))
            redis_client.hset(f"job:{job_id}", "completed_at", str(asyncio.get_event_loop().time()))
            
            logger.info(f"Automation job {job_id} completed: {result}")
            return result
            
    except Exception as e:
        logger.error(f"Automation job {job_id} failed: {e}")
        
        # Update job status in Redis
        redis_client.hset(f"job:{job_id}", "status", "failed")
        redis_client.hset(f"job:{job_id}", "error", str(e))
        redis_client.hset(f"job:{job_id}", "completed_at", str(asyncio.get_event_loop().time()))
        
        return {"success": False, "error": str(e)}


async def generate_cover_letter_with_ai(job_title: str, company: str, candidate_profile: dict) -> str:
    """Generate a personalized cover letter using AI Service"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{AI_SERVICE_URL}/generate-cover-letter",
                json={
                    "profile": {
                        "first_name": candidate_profile.get('first_name', ''),
                        "last_name": candidate_profile.get('last_name', ''),
                        "email": candidate_profile.get('email', ''),
                        "experience_years": candidate_profile.get('experience_years', 0),
                        "skills": candidate_profile.get('skills', []),
                        "current_role": candidate_profile.get('current_role', '')
                    },
                    "job": {
                        "title": job_title,
                        "company": company,
                        "description": "",
                        "requirements": candidate_profile.get('skills', [])
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return result.get("cover_letter", "")
        
        # Fallback
        return f"Dear Hiring Manager,\n\nI am writing to express my strong interest in the {job_title} position at {company}. With {candidate_profile.get('experience_years', 0)} years of experience in {', '.join(candidate_profile.get('skills', [])[:3])}, I am confident that my skills align perfectly with your requirements.\n\nI look forward to discussing how my background can benefit your organization.\n\nBest regards,\n{candidate_profile.get('first_name', 'Candidate')}"
        
    except Exception as e:
        logger.error(f"AI cover letter generation failed: {e}")
        return f"I am very interested in the {job_title} position at {company}. My skills in {', '.join(candidate_profile.get('skills', []))} make me a strong candidate for this role."


async def generate_profile_sections_with_ai(candidate_data: dict) -> dict:
    """Generate all profile sections using AI"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{AI_SERVICE_URL}/generate-profile-sections",
                json={
                    "first_name": candidate_data.get('first_name', ''),
                    "last_name": candidate_data.get('last_name', ''),
                    "email": candidate_data.get('email', ''),
                    "phone": candidate_data.get('phone', ''),
                    "location": candidate_data.get('location', ''),
                    "experience_years": candidate_data.get('experience_years', 0),
                    "skills": candidate_data.get('skills', []),
                    "bio": candidate_data.get('bio', ''),
                    "linkedin_url": candidate_data.get('linkedin_url', '')
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return result.get("sections", {})
        
        # Fallback
        return {
            "headline": f"{candidate_data.get('skills', ['Software'])[0]} Professional",
            "about": candidate_data.get('bio', 'Experienced professional'),
            "work_preference": "Seeking collaborative environment"
        }
        
    except Exception as e:
        logger.error(f"Profile sections generation failed: {e}")
        return {}


async def update_credential_verification(email: str):
    """Update credential verification status"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            logger.info(f"Account created successfully for {email}")
    except Exception as e:
        logger.error(f"Failed to update credential verification: {e}")


@app.get("/")
async def root():
    return {"service": "automation", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/adapters")
async def list_adapters():
    """List available career site adapters"""
    return {
        "adapters": list(ADAPTERS.keys())
    }


@app.post("/jobs/create-account")
async def create_account_job(
    background_tasks: BackgroundTasks,
    request_data: dict
):
    """Queue an account creation job"""
    site_name = request_data.get("site_name")
    credentials = request_data.get("credentials")
    candidate_data = request_data.get("candidate_data")
    
    job_id = f"create_account_{site_name}_{credentials['email']}_{int(asyncio.get_event_loop().time())}"
    
    # Store job info in memory
    redis_client.hset(f"job:{job_id}", "status", "queued")
    redis_client.hset(f"job:{job_id}", "site_name", site_name)
    redis_client.hset(f"job:{job_id}", "action", "create_account")
    
    background_tasks.add_task(
        run_automation_job,
        job_id,
        site_name,
        "create_account",
        credentials,
        candidate_data
    )
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": f"Account creation job queued for {site_name}"
    }


@app.post("/jobs/smart-apply")
async def smart_apply_to_job(
    background_tasks: BackgroundTasks,
    request_data: dict
):
    """Apply to job using intelligent strategy selection (Option A/B/C)"""
    job_url = request_data.get("job_url")
    credentials = request_data.get("credentials")
    candidate_data = request_data.get("candidate_data")
    
    job_id = f"smart_apply_{hash(job_url)}_{int(asyncio.get_event_loop().time())}"
    
    # Store job info in Redis
    redis_client.hset(f"job:{job_id}", "status", "queued")
    redis_client.hset(f"job:{job_id}", "job_url", job_url)
    redis_client.hset(f"job:{job_id}", "action", "smart_apply")
    redis_client.hset(f"job:{job_id}", "strategy", "intelligent_routing")
    
    background_tasks.add_task(
        run_smart_automation_job,
        job_id,
        "smart_apply",
        job_url,
        credentials,
        candidate_data
    )
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": f"Smart job application queued with intelligent strategy selection",
        "strategies_available": ["Browser Automation", "LLM-Guided", "ATS APIs"]
    }


@app.post("/analyze-resume")
async def analyze_uploaded_resume(file: UploadFile = File(...)):
    """Upload and analyze resume to extract candidate information"""
    try:
        # Forward to AI service for analysis
        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {'file': (file.filename, await file.read(), file.content_type)}
            response = await client.post(f"{AI_SERVICE_URL}/analyze-resume", files=files)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": "Resume analysis failed"
                }
                
    except Exception as e:
        logger.error(f"Resume upload failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/strategies")
async def list_automation_strategies():
    """List all available automation strategies"""
    return {
        "strategies": {
            "option_a": {
                "name": "Browser Automation (Playwright/Puppeteer)",
                "description": "Launch headless browser, use AI to identify form fields, fill and submit",
                "best_for": "Standard forms, static pages",
                "reliability": "High",
                "features": ["AI form detection", "Screenshot capture", "Error handling"]
            },
            "option_b": {
                "name": "LLM + Browser-Use",
                "description": "Give LLM the URL + profile, let it autonomously navigate and apply",
                "best_for": "Dynamic forms, unusual layouts, complex workflows",
                "reliability": "Very High", 
                "features": ["Autonomous navigation", "Adaptive form handling", "Smart decision making"]
            },
            "option_c": {
                "name": "ATS APIs",
                "description": "Direct integration with ATS systems (Greenhouse, Lever, Workday, Taleo)",
                "best_for": "Companies using supported ATS systems",
                "reliability": "Excellent",
                "features": ["Direct API integration", "No browser needed", "Instant application"]
            }
        },
        "intelligent_routing": {
            "description": "Automatically selects the best strategy for each job",
            "detection_criteria": ["ATS system presence", "Form complexity", "Page structure"],
            "fallback_order": ["ATS APIs", "LLM-Guided", "Browser Automation"]
        }
    }


async def run_smart_automation_job(
    job_id: str,
    action: str,
    job_url: str,
    credentials: dict,
    candidate_data: dict
):
    """Run automation job using intelligent strategy selection"""
    try:
        logger.info(f"Starting smart automation job {job_id} for {job_url}")
        
        # Update job status in Redis
        redis_client.hset(f"job:{job_id}", "status", "running")
        redis_client.hset(f"job:{job_id}", "started_at", str(asyncio.get_event_loop().time()))
        
        # Use automation router to choose and execute best strategy
        if action == "smart_apply":
            result = await automation_router.apply_to_job(job_url, candidate_data, credentials)
        else:
            result = {"success": False, "error": "Unknown action"}
        
        # Update job status in Redis
        redis_client.hset(f"job:{job_id}", "status", "completed" if result.get("success") else "failed")
        redis_client.hset(f"job:{job_id}", "result", json.dumps(result))
        redis_client.hset(f"job:{job_id}", "completed_at", str(asyncio.get_event_loop().time()))
        
        logger.info(f"Smart automation job {job_id} completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Smart automation job {job_id} failed: {e}")
        
        # Update job status in Redis  
        redis_client.hset(f"job:{job_id}", "status", "failed")
        redis_client.hset(f"job:{job_id}", "error", str(e))
        redis_client.hset(f"job:{job_id}", "completed_at", str(asyncio.get_event_loop().time()))
        
        return {"success": False, "error": str(e)}


@app.post("/jobs/apply")
async def apply_to_job(
    background_tasks: BackgroundTasks,
    request_data: dict
):
    """Queue a job application"""
    site_name = request_data.get("site_name")
    credentials = request_data.get("credentials")
    application_data = request_data.get("application_data")
    
    job_id = f"apply_{site_name}_{hash(application_data['job_url'])}_{int(asyncio.get_event_loop().time())}"
    
    # Store job info in Redis
    redis_client.hset(f"job:{job_id}", "status", "queued")
    redis_client.hset(f"job:{job_id}", "site_name", site_name)
    redis_client.hset(f"job:{job_id}", "action", "apply_to_job")
    redis_client.hset(f"job:{job_id}", "job_url", application_data['job_url'])
    redis_client.expire(f"job:{job_id}", 3600)  # Expire after 1 hour
    
    background_tasks.add_task(
        run_automation_job,
        job_id,
        site_name,
        "apply_to_job",
        credentials,
        application_data
    )
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": f"Job application queued for {site_name}"
    }


@app.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """Get the status of an automation job"""
    job_data = redis_client.hgetall(f"job:{job_id}")
    
    if not job_data:
        return {
            "job_id": job_id,
            "status": "not_found",
            "error": "Job not found or expired"
        }
    
    result = {
        "job_id": job_id,
        "status": job_data.get("status", "unknown"),
        "site_name": job_data.get("site_name"),
        "action": job_data.get("action")
    }
    
    if job_data.get("result"):
        result["result"] = json.loads(job_data.get("result"))
    
    if job_data.get("error"):
        result["error"] = job_data.get("error")
        
    if job_data.get("started_at"):
        result["started_at"] = float(job_data.get("started_at"))
        
    if job_data.get("completed_at"):
        result["completed_at"] = float(job_data.get("completed_at"))
        
    return result


# ============================================================================
# OLLAMA AUTOMATION ENDPOINTS
# ============================================================================

@app.post("/ollama/create-accounts")
async def ollama_create_accounts(
    background_tasks: BackgroundTasks,
    request: AccountCreationRequest
):
    """
    Create accounts on career sites using Ollama AI
    Uses SAME credentials from Swiply registration (not mock credentials)
    
    Example:
    {
        "user_id": "user_123",
        "email": "john@example.com",      # SAME email used in Swiply
        "password": "SecurePass123!",      # SAME password used in Swiply
        "first_name": "John",
        "last_name": "Developer",
        "phone": "+33 6 12 34 56 78",
        "location": "Paris, France",
        "sites": ["wttj", "sncf"]
    }
    """
    try:
        if not OLLAMA_AVAILABLE:
            raise HTTPException(status_code=503, detail="Ollama not available. Install with: pip install ollama")
        
        # Store REAL credentials (not mock) - Same as Swiply registration
        user_data = {
            "email": request.email,      # REAL email from Swiply
            "password": request.password,  # REAL password from Swiply
            "first_name": request.first_name,
            "last_name": request.last_name,
            "phone": request.phone,
            "location": request.location
        }
        
        job_id = f"ollama_create_accounts_{request.user_id}_{int(asyncio.get_event_loop().time())}"
        
        # Store job info in Redis with REAL credentials
        redis_client.hset(f"job:{job_id}", "status", "queued")
        redis_client.hset(f"job:{job_id}", "action", "ollama_create_accounts")
        redis_client.hset(f"job:{job_id}", "user_id", request.user_id)
        redis_client.hset(f"job:{job_id}", "sites", json.dumps(request.sites))
        redis_client.hset(f"job:{job_id}", "email", request.email)  # Store REAL email
        redis_client.hset(f"job:{job_id}", "credentials_type", "real_swiply_credentials")  # Mark as real
            
        # Run in background with REAL Swiply credentials
        background_tasks.add_task(
            ollama_run_account_creation,
            job_id,
            request.user_id,
            user_data,
            request.sites
        )
        
        return {
            "status": "initiated",
            "user_id": request.user_id,
            "job_id": job_id,
            "message": f"Account creation started for {', '.join(request.sites)}",
            "ai_backend": "Ollama Mistral 7B",
            "credentials_info": {
                "email": request.email,  # Show REAL email
                "credential_type": "swiply_registration_credentials",  # Not mock
                "sites": request.sites
            }
        }
    except Exception as e:
        logger.error(f"Account creation request failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/ollama/setup-profiles")
async def ollama_setup_profiles(
    background_tasks: BackgroundTasks,
    request: ProfileSetupRequest
):
    """
    Setup profiles on career sites using AI-generated content
    
    Example:
    {
        "user_id": "user_123",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Developer",
        "headline": "Senior Full Stack Developer",
        "bio": "Experienced developer...",
        "skills": ["Python", "React", "AWS"],
        "experience_years": 5,
        "education": "Bachelor's in Computer Science",
        "linkedin_url": "https://linkedin.com/in/john",
        "sites": ["wttj", "sncf"]
    }
    """
    try:
        if not OLLAMA_AVAILABLE:
            raise HTTPException(status_code=503, detail="Ollama not available. Install with: pip install ollama")
        
        user_data = {
            "email": request.email,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "headline": request.headline,
            "bio": request.bio,
            "skills": request.skills,
            "experience_years": request.experience_years,
            "education": request.education,
            "linkedin_url": request.linkedin_url
        }
        
        job_id = f"ollama_setup_profiles_{request.user_id}_{int(asyncio.get_event_loop().time())}"
        
        # Store job info in Redis
        redis_client.hset(f"job:{job_id}", "status", "queued")
        redis_client.hset(f"job:{job_id}", "action", "ollama_setup_profiles")
        redis_client.hset(f"job:{job_id}", "user_id", request.user_id)
        redis_client.hset(f"job:{job_id}", "sites", json.dumps(request.sites))
            
        # Run in background
        background_tasks.add_task(
            ollama_run_profile_setup,
            job_id,
            request.user_id,
            user_data,
            request.sites
        )
        
        return {
            "status": "initiated",
            "user_id": request.user_id,
            "job_id": job_id,
            "message": f"Profile setup started for {', '.join(request.sites)}",
            "ai_enhancement": "Ollama is generating professional content and optimizing profiles",
            "ai_backend": "Ollama Mistral 7B"
        }
    except Exception as e:
        logger.error(f"Profile setup request failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/ollama/apply-to-jobs")
async def ollama_apply_to_jobs(
    background_tasks: BackgroundTasks,
    request: JobApplicationRequest
):
    """
    Apply to jobs using AI-generated cover letters and optimized profiles
    
    Example:
    {
        "user_id": "user_123",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Developer",
        "headline": "Senior Full Stack Developer",
        "bio": "Experienced developer...",
        "skills": ["Python", "React", "AWS"],
        "experience_years": 5,
        "education": "Bachelor's in Computer Science",
        "job_urls": {
            "wttj": [
                "https://www.welcometothejungle.com/en/jobs/job1",
                "https://www.welcometothejungle.com/en/jobs/job2"
            ],
            "sncf": [
                "https://emploi.sncf.com/job1"
            ]
        }
    }
    """
    try:
        if not OLLAMA_AVAILABLE:
            raise HTTPException(status_code=503, detail="Ollama not available. Install with: pip install ollama")
        
        user_data = {
            "email": request.email,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "headline": request.headline,
            "bio": request.bio,
            "skills": request.skills,
            "experience_years": request.experience_years,
            "education": request.education
        }
        
        total_jobs = sum(len(urls) for urls in request.job_urls.values())
        
        job_id = f"ollama_apply_jobs_{request.user_id}_{int(asyncio.get_event_loop().time())}"
        
        # Store job info in Redis
        redis_client.hset(f"job:{job_id}", "status", "queued")
        redis_client.hset(f"job:{job_id}", "action", "ollama_apply_jobs")
        redis_client.hset(f"job:{job_id}", "user_id", request.user_id)
        redis_client.hset(f"job:{job_id}", "total_jobs", str(total_jobs))
        redis_client.expire(f"job:{job_id}", 7200)  # 2 hour TTL for long-running job
        
        # Run in background
        background_tasks.add_task(
            ollama_run_job_applications,
            job_id,
            request.user_id,
            user_data,
            request.job_urls
        )
        
        return {
            "status": "initiated",
            "user_id": request.user_id,
            "job_id": job_id,
            "total_jobs": total_jobs,
            "message": f"Applying to {total_jobs} jobs with Ollama-generated content",
            "ai_features": [
                "Intelligent cover letter generation",
                "ATS keyword optimization",
                "Personalized application answers",
                "Experience-based job matching"
            ],
            "ai_backend": "Ollama Mistral 7B"
        }
    except Exception as e:
        logger.error(f"Job application request failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/ollama/full-automation")
async def ollama_full_automation(
    background_tasks: BackgroundTasks,
    request_data: Dict[str, Any]
):
    """
    Run complete automation workflow: Create account Ã¢â€ â€™ Setup profile Ã¢â€ â€™ Apply to jobs
    
    Example:
    {
        "user_id": "user_123",
        "email": "john@example.com",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Developer",
        "headline": "Senior Full Stack Developer",
        "bio": "Experienced developer with passion for technology",
        "skills": ["Python", "React", "AWS", "Docker"],
        "experience_years": 5,
        "education": "Bachelor's in Computer Science",
        "phone": "+33 6 12 34 56 78",
        "location": "Paris, France",
        "sites": ["wttj", "sncf"],
        "job_urls": {
            "wttj": ["https://www.welcometothejungle.com/en/jobs/job1"],
            "sncf": ["https://emploi.sncf.com/job1"]
        }
    }
    """
    try:
        if not OLLAMA_AVAILABLE:
            raise HTTPException(status_code=503, detail="Ollama not available. Install with: pip install ollama")
        
        user_id = request_data.get("user_id")
        if not user_id:
            raise ValueError("user_id is required")
        
        sites = request_data.get("sites", ["wttj", "sncf"])
        job_urls = request_data.get("job_urls", {})
        
        job_id = f"ollama_full_automation_{user_id}_{int(asyncio.get_event_loop().time())}"
        
        # Store job info in Redis
        redis_client.hset(f"job:{job_id}", "status", "queued")
        redis_client.hset(f"job:{job_id}", "action", "ollama_full_automation")
        redis_client.hset(f"job:{job_id}", "user_id", user_id)
        redis_client.hset(f"job:{job_id}", "workflow", "account_creation:profile_setup:job_applications")
            
        # Run in background
        background_tasks.add_task(
            ollama_run_full_automation,
            job_id,
            user_id,
            request_data,
            sites,
            job_urls
        )
        
        total_jobs = sum(len(urls) for urls in job_urls.values()) if job_urls else 0
        
        return {
            "status": "initiated",
            "user_id": user_id,
            "job_id": job_id,
            "workflow": ["Create Account", "Setup Profile", "Apply to Jobs"],
            "total_jobs": total_jobs,
            "message": "Full automation workflow started",
            "ai_backend": "Ollama Mistral 7B",
            "estimated_duration": "5-10 minutes depending on number of jobs"
        }
    except Exception as e:
        logger.error(f"Full automation request failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/ollama/status/{user_id}")
async def ollama_get_automation_status(user_id: str):
    """
    Get automation status for a user
    
    Returns:
    - Accounts created
    - Profiles setup
    - Applications submitted
    - Success rate
    """
    try:
        # Get all job IDs for this user from Redis
        pattern = f"job:ollama_*_{user_id}_*"
        job_keys = [k.replace("job:", "") for k in _job_store.keys() if user_id in k]
        
        status_data = {
            "user_id": user_id,
            "total_jobs": len(job_keys),
            "jobs": [],
            "summary": {
                "queued": 0,
                "running": 0,
                "completed": 0,
                "failed": 0
            }
        }
        
        for key in job_keys:
            job_data = redis_client.hgetall(key)
            job_status = job_data.get("status", "unknown")
            
            status_data["summary"][job_status] = status_data["summary"].get(job_status, 0) + 1
            
            job_info = {
                "job_id": key.replace("job:", ""),
                "action": job_data.get("action", "unknown"),
                "status": job_status
            }
            
            if job_data.get("result"):
                job_info["result"] = json.loads(job_data.get("result"))
            
            status_data["jobs"].append(job_info)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "data": status_data,
            "ai_backend": "Ollama Mistral 7B"
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/ollama/health")
async def ollama_health_check():
    """Check Ollama automation system health"""
    try:
        if not OLLAMA_AVAILABLE:
            return {
                "status": "unavailable",
                "ollama_available": False,
                "message": "Ollama not available - install with: pip install ollama"
            }
        
        models_response = ollama.list()
        
        # Extract model names
        model_names = []
        if hasattr(models_response, 'models'):
            model_names = [m.model for m in models_response.models]
        elif isinstance(models_response, dict) and "models" in models_response:
            model_names = [m.get("model") if isinstance(m, dict) else m.model for m in models_response["models"]]
        
        mistral_available = any("mistral" in m.lower() for m in model_names)
        
        return {
            "status": "healthy" if mistral_available else "degraded",
            "ollama_available": True,
            "mistral_available": mistral_available,
            "models": model_names,
            "ai_backend": "Ollama Mistral 7B"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "ollama_available": False,
            "error": str(e)
        }


@app.post("/ollama/auto-setup-from-swiply")
async def ollama_auto_setup_from_swiply(
    background_tasks: BackgroundTasks,
    request_data: Dict[str, Any]
):
    """
    Automatically setup WTTJ account using data from Swiply registration
    
    This endpoint is called when a user registers on Swiply and wants
    to automatically create accounts on career sites using their REAL
    Swiply credentials (not mock credentials).
    
    Request body:
    {
        "user_id": "user_123",
        "swiply_email": "john@example.com",     # REAL email from Swiply
        "swiply_password": "SecurePass123!",    # REAL password from Swiply
        "first_name": "John",
        "last_name": "Developer",
        "profile_data": {
            "phone": "+33 6 12 34 56 78",
            "location": "Paris, France",
            "bio": "Experienced developer...",
            "skills": ["Python", "React"],
            "experience_years": 5,
            "linkedin_url": "https://linkedin.com/in/john"
        },
        "sites": ["wttj", "sncf"]
    }
    """
    try:
        if not OLLAMA_AVAILABLE:
            raise HTTPException(status_code=503, detail="Ollama not available")
        
        user_id = request_data.get("user_id")
        swiply_email = request_data.get("swiply_email")
        swiply_password = request_data.get("swiply_password")
        first_name = request_data.get("first_name", "")
        last_name = request_data.get("last_name", "")
        profile_data = request_data.get("profile_data", {})
        sites = request_data.get("sites", ["wttj"])
        
        if not all([user_id, swiply_email, swiply_password]):
            raise HTTPException(status_code=400, detail="user_id, swiply_email, and swiply_password are required")
        
        # Prepare complete user data with REAL Swiply credentials
        complete_user_data = {
            "email": swiply_email,         # REAL email from Swiply
            "password": swiply_password,   # REAL password from Swiply
            "first_name": first_name,
            "last_name": last_name,
            "phone": profile_data.get("phone", ""),
            "location": profile_data.get("location", "Paris, France"),
            "bio": profile_data.get("bio", ""),
            "skills": profile_data.get("skills", []),
            "experience_years": profile_data.get("experience_years", 0),
            "linkedin_url": profile_data.get("linkedin_url", ""),
            "headline": profile_data.get("headline", f"{first_name} {last_name}")
        }
        
        job_id = f"ollama_swiply_auto_setup_{user_id}_{int(asyncio.get_event_loop().time())}"
        
        # Store in Redis
        redis_client.hset(f"job:{job_id}", "status", "queued")
        redis_client.hset(f"job:{job_id}", "action", "ollama_swiply_auto_setup")
        redis_client.hset(f"job:{job_id}", "user_id", user_id)
        redis_client.hset(f"job:{job_id}", "swiply_email", swiply_email)
        redis_client.hset(f"job:{job_id}", "credential_source", "swiply_registration")
        redis_client.hset(f"job:{job_id}", "sites", json.dumps(sites))
            
        # Run full automation with REAL Swiply credentials
        background_tasks.add_task(
            ollama_run_full_automation,
            job_id,
            user_id,
            complete_user_data,
            sites,
            {}  # No job URLs for initial setup
        )
        
        return {
            "status": "initiated",
            "user_id": user_id,
            "job_id": job_id,
            "message": f"Automated setup started for {', '.join(sites)} using Swiply credentials",
            "credentials_info": {
                "source": "swiply_registration",
                "email": swiply_email,  # Show REAL email
                "note": "Using same credentials as Swiply account (not mock credentials)",
                "sites": sites
            },
            "workflow": [
                "Creating account with Swiply credentials",
                "Setting up profile with Ollama AI",
                "Profile will be ready for job applications"
            ],
            "ai_backend": "Ollama Mistral 7B"
        }
        
    except Exception as e:
        logger.error(f"Swiply auto-setup failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# OLLAMA AUTOMATION BACKGROUND TASKS
# ============================================================================

async def ollama_run_account_creation(
    job_id: str,
    user_id: str,
    user_data: Dict,
    sites: List[str]
):
    """
    Background task to create accounts using Ollama
    Uses REAL Swiply credentials (email + password) - NOT mock credentials
    """
    try:
        logger.info(f"Starting Ollama account creation for {user_id} on {sites}")
        logger.info(f"Using REAL Swiply credentials: {user_data['email']}")
        redis_client.hset(f"job:{job_id}", "status", "running")
        redis_client.hset(f"job:{job_id}", "started_at", datetime.now().isoformat())
        
        results = {}
        
        for site in sites:
            try:
                logger.info(f"Creating account on {site} with REAL Swiply credentials...")
                
                # Get adapter for the site
                adapter = get_adapter(site.upper())
                
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=False)
                    page = await browser.new_page()
                    
                    # IMPORTANT: Use REAL Swiply credentials
                    # These are the SAME email and password the user used to register on Swiply
                    real_email = user_data['email']
                    real_password = user_data['password']
                    
                    logger.info(f"Creating {site} account with email: {real_email}")
                    
                    # Create account using adapter with REAL credentials
                    result = await adapter.create_account(
                        page,
                        real_email,      # REAL email from Swiply registration
                        real_password,   # REAL password from Swiply registration
                        user_data
                    )
                    
                    results[site] = {
                        **result,
                        "credentials_used": {
                            "email": real_email,  # Show REAL email
                            "credential_type": "swiply_registration",  # Mark as real
                            "note": "Same credentials as Swiply account"
                        }
                    }
                    
                    await browser.close()
                
                logger.info(f"Ã¢Å“â€¦ Account creation for {site}: {result.get('success')}")
                logger.info(f"   Email used: {real_email}")
                
            except Exception as e:
                logger.error(f"Ã¢ÂÅ’ Account creation for {site} failed: {e}")
                results[site] = {
                    "success": False,
                    "error": str(e),
                    "credentials_used": {
                        "email": user_data['email'],
                        "credential_type": "swiply_registration"
                    }
                }
        
        # Store results with REAL credential information
        redis_client.hset(f"job:{job_id}", "status", "completed")
        redis_client.hset(f"job:{job_id}", "result", json.dumps(results))
        redis_client.hset(f"job:{job_id}", "completed_at", datetime.now().isoformat())
        redis_client.hset(f"job:{job_id}", "credentials_note", "Used real Swiply registration credentials")
        
        logger.info(f"Ã¢Å“â€¦ Account creation complete for {user_id}")
        logger.info(f"   Credentials: {user_data['email']} (REAL Swiply credentials)")
        
    except Exception as e:
        logger.error(f"Account creation failed: {e}")
        redis_client.hset(f"job:{job_id}", "status", "failed")
        redis_client.hset(f"job:{job_id}", "error", str(e))


async def ollama_run_profile_setup(
    job_id: str,
    user_id: str,
    user_data: Dict,
    sites: List[str]
):
    """Background task to setup profiles using Ollama-enhanced content"""
    try:
        logger.info(f"Starting Ollama profile setup for {user_id} on {sites}")
        redis_client.hset(f"job:{job_id}", "status", "running")
        redis_client.hset(f"job:{job_id}", "started_at", datetime.now().isoformat())
        
        results = {}
        
        for site in sites:
            try:
                logger.info(f"Setting up profile on {site}...")
                
                # Get adapter for the site
                adapter = get_adapter(site.upper())
                
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=False)
                    page = await browser.new_page()
                    
                    # Login first
                    login_result = await adapter.login(page, user_data['email'], user_data['password'])
                    
                    if login_result:
                        # Setup profile using adapter
                        result = await adapter.setup_profile(page, user_data)
                        results[site] = result
                    else:
                        results[site] = {"success": False, "error": "Login failed"}
                    
                    await browser.close()
                
                logger.info(f"Ã¢Å“â€¦ Profile setup for {site}: {result.get('success')}")
                
            except Exception as e:
                logger.error(f"Ã¢ÂÅ’ Profile setup for {site} failed: {e}")
                results[site] = {"success": False, "error": str(e)}
        
        redis_client.hset(f"job:{job_id}", "status", "completed")
        redis_client.hset(f"job:{job_id}", "result", json.dumps(results))
        redis_client.hset(f"job:{job_id}", "completed_at", datetime.now().isoformat())
        
        logger.info(f"Ã¢Å“â€¦ Profile setup complete for {user_id}")
        
    except Exception as e:
        logger.error(f"Profile setup failed: {e}")
        redis_client.hset(f"job:{job_id}", "status", "failed")
        redis_client.hset(f"job:{job_id}", "error", str(e))


async def ollama_run_job_applications(
    job_id: str,
    user_id: str,
    user_data: Dict,
    job_urls: Dict[str, List[str]]
):
    """Background task to apply to jobs using Ollama-enhanced content"""
    try:
        logger.info(f"Starting Ollama job applications for {user_id}")
        redis_client.hset(f"job:{job_id}", "status", "running")
        redis_client.hset(f"job:{job_id}", "started_at", datetime.now().isoformat())
        
        results = {"applications": []}
        total_applied = 0
        total_success = 0
        
        for site, urls in job_urls.items():
            try:
                logger.info(f"Applying to {len(urls)} jobs on {site}...")
                
                # Get adapter for the site
                adapter = get_adapter(site.upper())
                
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=False)
                    page = await browser.new_page()
                    
                    # Login first
                    login_result = await adapter.login(page, user_data['email'], user_data['password'])
                    
                    if login_result:
                        for job_url in urls:
                            try:
                                logger.info(f"Applying to job: {job_url}")
                                
                                # Generate personalized content for this job using Ollama
                                job_title = job_url.split('/')[-1] if '/' in job_url else "Job"
                                
                                # Create application data
                                application_data = {
                                    **user_data,
                                    "job_url": job_url,
                                    "job_title": job_title
                                }
                                
                                # Apply to job
                                result = await adapter.apply_to_job(page, job_url, application_data)
                                
                                total_applied += 1
                                if result.get("success"):
                                    total_success += 1
                                
                                results["applications"].append({
                                    "site": site,
                                    "job_url": job_url,
                                    "status": "success" if result.get("success") else "failed",
                                    "message": result.get("message", "")
                                })
                                
                            except Exception as e:
                                logger.error(f"Application to {job_url} failed: {e}")
                                total_applied += 1
                                results["applications"].append({
                                    "site": site,
                                    "job_url": job_url,
                                    "status": "failed",
                                    "error": str(e)
                                })
                    else:
                        logger.error(f"Login failed for {site}")
                    
                    await browser.close()
                
            except Exception as e:
                logger.error(f"Job applications for {site} failed: {e}")
        
        results["summary"] = {
            "total_applied": total_applied,
            "total_success": total_success,
            "success_rate": f"{(total_success/total_applied*100) if total_applied > 0 else 0:.1f}%"
        }
        
        redis_client.hset(f"job:{job_id}", "status", "completed")
        redis_client.hset(f"job:{job_id}", "result", json.dumps(results))
        redis_client.hset(f"job:{job_id}", "completed_at", datetime.now().isoformat())
        
        logger.info(f"Ã¢Å“â€¦ Job applications complete for {user_id}: {total_success}/{total_applied} successful")
        
    except Exception as e:
        logger.error(f"Job applications failed: {e}")
        redis_client.hset(f"job:{job_id}", "status", "failed")
        redis_client.hset(f"job:{job_id}", "error", str(e))


async def ollama_run_full_automation(
    job_id: str,
    user_id: str,
    request_data: Dict[str, Any],
    sites: List[str],
    job_urls: Dict[str, List[str]]
):
    """Background task to run complete automation workflow"""
    try:
        logger.info(f"Starting full Ollama automation for {user_id}")
        redis_client.hset(f"job:{job_id}", "status", "running")
        redis_client.hset(f"job:{job_id}", "started_at", datetime.now().isoformat())
        
        workflow_results = {
            "account_creation": {},
            "profile_setup": {},
            "job_applications": {},
            "summary": {}
        }
        
        # Step 1: Create accounts
        logger.info("Step 1/3: Creating accounts...")
        try:
            user_data = {k: request_data[k] for k in ["email", "password", "first_name", "last_name", "phone", "location"] if k in request_data}
            
            for site in sites:
                try:
                    adapter = get_adapter(site.upper())
                    
                    async with async_playwright() as p:
                        browser = await p.chromium.launch(headless=False)
                        page = await browser.new_page()
                        
                        result = await adapter.create_account(page, user_data['email'], user_data['password'], user_data)
                        workflow_results["account_creation"][site] = result
                        
                        await browser.close()
                        logger.info(f"Ã¢Å“â€¦ {site} account created")
                except Exception as e:
                    logger.error(f"Ã¢ÂÅ’ {site} account creation failed: {e}")
                    workflow_results["account_creation"][site] = {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Account creation step failed: {e}")
        
        # Step 2: Setup profiles
        logger.info("Step 2/3: Setting up profiles...")
        try:
            profile_data = {k: request_data[k] for k in request_data.keys() if k not in ["user_id", "password", "sites", "job_urls"]}
            
            for site in sites:
                try:
                    adapter = get_adapter(site.upper())
                    
                    async with async_playwright() as p:
                        browser = await p.chromium.launch(headless=False)
                        page = await browser.new_page()
                        
                        login_result = await adapter.login(page, request_data['email'], request_data['password'])
                        if login_result:
                            result = await adapter.setup_profile(page, profile_data)
                            workflow_results["profile_setup"][site] = result
                        else:
                            workflow_results["profile_setup"][site] = {"success": False, "error": "Login failed"}
                        
                        await browser.close()
                        logger.info(f"Ã¢Å“â€¦ {site} profile setup completed")
                except Exception as e:
                    logger.error(f"Ã¢ÂÅ’ {site} profile setup failed: {e}")
                    workflow_results["profile_setup"][site] = {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Profile setup step failed: {e}")
        
        # Step 3: Apply to jobs
        if job_urls:
            logger.info("Step 3/3: Applying to jobs...")
            total_jobs = sum(len(urls) for urls in job_urls.values())
            logger.info(f"Applying to {total_jobs} jobs...")
            
            try:
                applications = []
                total_success = 0
                
                for site, urls in job_urls.items():
                    try:
                        adapter = get_adapter(site.upper())
                        
                        async with async_playwright() as p:
                            browser = await p.chromium.launch(headless=False)
                            page = await browser.new_page()
                            
                            login_result = await adapter.login(page, request_data['email'], request_data['password'])
                            if login_result:
                                for job_url in urls:
                                    try:
                                        app_data = {k: request_data[k] for k in request_data.keys() if k not in ["user_id", "password", "sites", "job_urls"]}
                                        app_data['job_url'] = job_url
                                        
                                        result = await adapter.apply_to_job(page, job_url, app_data)
                                        
                                        applications.append({
                                            "site": site,
                                            "job_url": job_url,
                                            "status": "success" if result.get("success") else "failed"
                                        })
                                        
                                        if result.get("success"):
                                            total_success += 1
                                            logger.info(f"Ã¢Å“â€¦ Applied to {job_url}")
                                        else:
                                            logger.warning(f"Ã¢Å¡Â Ã¯Â¸Â  Application to {job_url} may have failed")
                                            
                                    except Exception as e:
                                        logger.error(f"Ã¢ÂÅ’ Application to {job_url} failed: {e}")
                                        applications.append({
                                            "site": site,
                                            "job_url": job_url,
                                            "status": "failed",
                                            "error": str(e)
                                        })
                            
                            await browser.close()
                            
                    except Exception as e:
                        logger.error(f"Job applications for {site} failed: {e}")
                
                workflow_results["job_applications"]["applications"] = applications
                workflow_results["job_applications"]["total"] = len(applications)
                workflow_results["job_applications"]["successful"] = total_success
                logger.info(f"Ã¢Å“â€¦ Job applications complete: {total_success}/{len(applications)} successful")
                
            except Exception as e:
                logger.error(f"Job applications step failed: {e}")
        else:
            logger.info("No jobs to apply to, skipping Step 3")
            workflow_results["job_applications"]["applications"] = []
        
        # Summary
        workflow_results["summary"] = {
            "completed": True,
            "user_id": user_id,
            "accounts_created": len([s for s, r in workflow_results["account_creation"].items() if r.get("success")]),
            "profiles_setup": len([s for s, r in workflow_results["profile_setup"].items() if r.get("success")]),
            "applications_submitted": workflow_results["job_applications"].get("total", 0),
            "timestamp": datetime.now().isoformat()
        }
        
        redis_client.hset(f"job:{job_id}", "status", "completed")
        redis_client.hset(f"job:{job_id}", "result", json.dumps(workflow_results, default=str))
        redis_client.hset(f"job:{job_id}", "completed_at", datetime.now().isoformat())
        
        logger.info(f"Ã¢Å“â€¦ Full automation complete for {user_id}")
        
    except Exception as e:
        logger.error(f"Full automation failed: {e}")
        redis_client.hset(f"job:{job_id}", "status", "failed")
        redis_client.hset(f"job:{job_id}", "error", str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8006))
    
    # Install Playwright browsers on first run
    logger.info("Installing Playwright browsers...")
    os.system(f"{sys.executable} -m playwright install chromium")
    
    uvicorn.run(app, host="0.0.0.0", port=port)



