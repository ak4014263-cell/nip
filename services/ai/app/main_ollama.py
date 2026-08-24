"""
AI Service v2 - Multi-backend: Ollama (Free Local Mistral 7B) + OpenAI
Switch between free local LLM and cloud AI without code changes!
"""
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import json
import logging
import PyPDF2
import docx
from io import BytesIO

# Try Ollama first (local, free)
try:
    import ollama
    OLLAMA_AVAILABLE = True
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    logger_init = logging.getLogger("ollama_check")
    logger_init.info("Ollama library imported successfully")
except Exception as e:
    OLLAMA_AVAILABLE = False
    print(f"⚠️  Ollama not installed: {e}")

# Fallback to OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "sk-test"))
except:
    OPENAI_AVAILABLE = False
    openai_client = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Swiply AI Service v2",
    description="Multi-backend AI: Ollama (Free) + OpenAI",
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

# Models
class ProfileData(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[int] = 0
    skills: List[str] = []
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    education: Optional[str] = None
    current_role: Optional[str] = None
    career_goals: Optional[str] = None

class JobData(BaseModel):
    title: str
    company: str
    description: str
    requirements: List[str] = []
    location: Optional[str] = None

# AI Backend Class
class AIBackend:
    """Unified AI backend supporting Ollama and OpenAI"""
    
    def __init__(self):
        self.use_ollama = OLLAMA_AVAILABLE
        self.model = "mistral"
        
        if self.use_ollama:
            try:
                self.client = ollama.Client(host=OLLAMA_HOST)
                logger.info("✅ Using Ollama Mistral 7B (Free, Local, Private)")
                self.backend_name = "Ollama Mistral 7B"
            except Exception as e:
                logger.error(f"Ollama failed: {e}")
                self.use_ollama = False
                self.backend_name = "OpenAI GPT-5"
        else:
            self.client = openai_client
            self.backend_name = "OpenAI GPT-5"
            logger.info("✅ Using OpenAI GPT-5 (Latest model)")
    
    async def generate(self, prompt: str, max_tokens: int = 1500) -> str:
        """Generate text using available backend"""
        try:
            if self.use_ollama:
                response = self.client.generate(
                    model=self.model,
                    prompt=prompt,
                    stream=False
                )
                return response.get("response", "").strip()
            else:
                response = openai_client.chat.completions.create(
                    model="gpt-5",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_completion_tokens=max_tokens
                )
                return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return ""

# Initialize backend
ai_backend = AIBackend()

# Endpoints
@app.get("/")
async def root():
    return {
        "service": "ai-v2",
        "status": "running",
        "backend": ai_backend.backend_name,
        "ollama_available": OLLAMA_AVAILABLE,
        "openai_available": OPENAI_AVAILABLE,
        "cost": "$0/month" if OLLAMA_AVAILABLE else "$150+/month"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "backend": ai_backend.backend_name,
        "ollama": OLLAMA_AVAILABLE,
        "openai": OPENAI_AVAILABLE
    }

@app.get("/backend-info")
async def backend_info():
    return {
        "current_backend": ai_backend.backend_name,
        "model": ai_backend.model,
        "ollama_available": OLLAMA_AVAILABLE,
        "openai_available": OPENAI_AVAILABLE,
        "cost_per_1k_tokens": "$0" if OLLAMA_AVAILABLE else "$0.03",
        "speed": "50-200ms local" if OLLAMA_AVAILABLE else "100ms+ API",
        "privacy": "100% local" if OLLAMA_AVAILABLE else "Sent to OpenAI",
        "recommendation": "Use Ollama for best results" if OLLAMA_AVAILABLE else "Install Ollama to save costs"
    }

@app.post("/enhance-profile")
async def enhance_profile(profile: ProfileData):
    """Enhance profile using AI backend"""
    try:
        prompt = f"""
You are a professional career counselor. Create a comprehensive professional profile for:

Name: {profile.first_name} {profile.last_name}
Current Role: {profile.current_role or 'Professional'}
Location: {profile.location or 'Not specified'}
Experience: {profile.experience_years} years
Skills: {', '.join(profile.skills)}
Education: {profile.education or 'Not specified'}
Current Bio: {profile.bio or 'No bio provided'}
Career Goals: {profile.career_goals or 'Seeking new opportunities'}

Generate a JSON response with:
1. professional_headline: 1-line headline (60 chars max)
2. professional_summary: 3-4 sentences highlighting achievements
3. detailed_bio: 2-3 paragraphs for career site profiles
4. elevator_pitch: 30-second pitch
5. suggested_skills: 10 additional relevant skills
6. career_keywords: 15 ATS-optimized keywords
7. profile_strengths: 5 key strengths
8. recommended_job_titles: 5 target job titles

Return ONLY valid JSON, no markdown.
"""

        content = await ai_backend.generate(prompt, max_tokens=1500)
        
        if not content:
            # Fallback
            return {
                "success": True,
                "enhanced_profile": {
                    "professional_headline": f"Experienced {profile.skills[0] if profile.skills else 'Professional'} Developer",
                    "professional_summary": f"{profile.first_name} is an experienced professional with {profile.experience_years} years in {', '.join(profile.skills[:3])}.",
                    "detailed_bio": profile.bio or "Experienced professional seeking opportunities",
                    "elevator_pitch": f"Hi, I'm {profile.first_name}, a {profile.skills[0] if profile.skills else 'software'} professional.",
                    "suggested_skills": ["Problem Solving", "Team Collaboration", "Agile"],
                    "career_keywords": ["Software", "Development", "Innovation"],
                    "profile_strengths": ["Technical Expertise", "Problem Solving", "Team Work"],
                    "recommended_job_titles": ["Senior Developer", "Lead Developer", "Technical Lead"]
                },
                "backend": ai_backend.backend_name,
                "fallback": True
            }
        
        try:
            # Clean JSON response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content.strip())
        except:
            result = json.loads(content.strip())
        
        logger.info(f"Profile enhanced with {ai_backend.backend_name}")
        
        return {
            "success": True,
            "enhanced_profile": result,
            "backend": ai_backend.backend_name
        }
        
    except Exception as e:
        logger.error(f"Enhancement failed: {e}")
        return {
            "success": True,
            "enhanced_profile": {
                "professional_headline": f"Experienced Professional",
                "professional_summary": f"Skilled professional with {profile.experience_years} years experience",
                "detailed_bio": profile.bio,
                "elevator_pitch": f"Professional with expertise in {', '.join(profile.skills)}",
                "suggested_skills": ["Leadership", "Innovation", "Communication"],
                "career_keywords": ["Professional", "Development", "Growth"],
                "profile_strengths": ["Technical Skills", "Leadership", "Innovation"],
                "recommended_job_titles": ["Senior Role", "Manager", "Specialist"]
            },
            "fallback": True,
            "backend": ai_backend.backend_name
        }

@app.post("/generate-resume")
async def generate_resume(profile: ProfileData):
    """Generate professional resume"""
    try:
        prompt = f"""
Generate a professional ATS-optimized resume for:
{profile.first_name} {profile.last_name} | {profile.email} | {profile.phone}
Experience: {profile.experience_years} years
Skills: {', '.join(profile.skills)}

Return JSON with:
1. contact_info: Full contact details
2. professional_summary: Achievement-focused summary
3. technical_skills: Organized by category
4. work_experience: 3 detailed entries with metrics
5. education: Degree and institution
6. certifications: Relevant certs
7. projects: 2-3 key projects
8. achievements: Notable accomplishments

Return ONLY valid JSON.
"""

        content = await ai_backend.generate(prompt, max_tokens=2000)
        
        if content:
            try:
                if "```" in content:
                    content = content.split("```")[1].split("```")[0]
                result = json.loads(content.strip())
            except:
                result = json.loads(content.strip())
            
            return {
                "success": True,
                "resume": result,
                "backend": ai_backend.backend_name
            }
        else:
            return {
                "success": True,
                "resume": {
                    "contact_info": {"name": f"{profile.first_name} {profile.last_name}", "email": profile.email},
                    "professional_summary": f"Professional with {profile.experience_years} years experience",
                    "technical_skills": {"Core": profile.skills},
                    "work_experience": [],
                    "education": profile.education
                },
                "fallback": True,
                "backend": ai_backend.backend_name
            }
        
    except Exception as e:
        logger.error(f"Resume generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "backend": ai_backend.backend_name
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8010))
    logger.info(f"Starting AI Service on port {port}")
    logger.info(f"Backend: {ai_backend.backend_name}")
    uvicorn.run(app, host="0.0.0.0", port=port)
