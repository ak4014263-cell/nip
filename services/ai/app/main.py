"""
AI Service - Multi-backend support: Ollama (Mistral 7B) + OpenAI Integration
"""
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import json
import logging
import PyPDF2
import docx
from io import BytesIO

# Disable Ollama and force OpenAI
OLLAMA_AVAILABLE = False

# Fallback to OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "sk-your-key-here"))
    client = openai_client
except:
    OPENAI_AVAILABLE = False
    openai_client = None
    client = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Swiply AI Service",
    description="Multi-backend AI: Ollama (Free Local) + OpenAI",
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

# AI Backend Management
class AIBackend:
    """Unified AI backend supporting Ollama and OpenAI"""
    
    def __init__(self):
        self.use_ollama = OLLAMA_AVAILABLE
        # Use custom trained model if available
        self.model = "gpt-4o-mini" if not self.use_ollama else "mistral-custom"
        self.backend = "Ollama (Mistral 7B Custom Trained)" if self.use_ollama else "OpenAI (GPT-4o-mini)"
        
        if self.use_ollama:
            try:
                self.client = ollama.Client(host=OLLAMA_HOST)
                logger.info("✅ Using Ollama Mistral 7B Custom Trained Model (Free Local LLM)")
            except Exception as e:
                logger.warning(f"Ollama connection failed, falling back to OpenAI: {e}")
                self.use_ollama = False
                self.backend = "OpenAI (GPT-5)"
        else:
            self.client = openai_client
            logger.info("✅ Using OpenAI GPT-5 (Latest model)")
    
    async def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate text using available backend with fast fallback"""
        try:
            if self.use_ollama:
                import asyncio
                # Run with 3 second timeout in case local Ollama is offline
                def _call_ollama():
                    return self.client.generate(
                        model=self.model,
                        prompt=prompt,
                        stream=False,
                        options={
                            "temperature": 1,
                            "top_p": 0.9,
                        }
                    )
                response = await asyncio.wait_for(asyncio.to_thread(_call_ollama), timeout=30.0)
                return response.get("response", "").strip()
            elif openai_client and openai_client.api_key and not openai_client.api_key.startswith("sk-your-key"):
                import asyncio
                def _call_openai():
                    return openai_client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens
                    )
                response = await asyncio.wait_for(asyncio.to_thread(_call_openai), timeout=30.0)
                return response.choices[0].message.content.strip()
            else:
                return ""
        except Exception as e:
            logger.warning(f"AI backend generation note (using intelligent fallback): {e}")
            return ""

# Initialize AI backend
ai_backend = AIBackend()

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

class FormFillRequest(BaseModel):
    fields: List[Dict[str, Any]]
    profile_data: Dict[str, Any]

@app.get("/")
async def root():
    return {
        "service": "ai",
        "status": "running",
        "backend": ai_backend.backend,
        "model": ai_backend.model,
        "ollama_available": OLLAMA_AVAILABLE,
        "openai_available": OPENAI_AVAILABLE,
        "features": ["profile-enhancement", "resume-generation", "cover-letters", "ats-optimization", "resume-analysis"]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "backend": ai_backend.backend,
        "model": ai_backend.model,
        "ollama_ready": OLLAMA_AVAILABLE,
        "openai_ready": OPENAI_AVAILABLE and openai_client.api_key != "sk-your-key-here"
    }

@app.post("/fill-form")
async def fill_form(req: FormFillRequest):
    """Use AI to dynamically determine values for form fields"""
    try:
        # Construct the prompt
        prompt = f"""
You are an expert AI browser agent applying to a job. Your task is to determine the correct values for a set of form fields based on the candidate's profile.

Candidate Profile:
{json.dumps(req.profile_data, indent=2)}

Form Fields on the Page:
{json.dumps(req.fields, indent=2)}

Instructions:
1. For each field in the 'Form Fields', determine the best value from the 'Candidate Profile'.
2. If it's a 'checkbox' for terms of service, GDPR, or consent, output the boolean value true.
3. If it's a radio button for work authorization, usually answer true or "Yes".
4. If it's a textarea asking for motivation or cover letter, write a short personalized text based on their profile.
5. NEVER leave a field empty. If you don't know the answer, invent a highly plausible professional placeholder, use 'N/A' for text, '0' for numbers, or 'Yes'/true for toggles. NO FIELD SHALL BE LEFT EMPTY.

CRITICAL: Return ONLY a valid JSON object where the keys are the exact 'ai_id' of each field, and the values are what should be typed/selected/checked. Do not wrap in markdown tags. Example format:
{{
  "ai_field_0": "John",
  "ai_field_1": "Paris, France",
  "ai_field_2": true,
  "ai_field_3": "I am highly interested in this role because..."
}}
"""
        content = await ai_backend.generate(prompt, max_tokens=1500)
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        return json.loads(content)
    except Exception as e:
        logger.error(f"Error in /fill-form: {e}")
        return {}

@app.post("/enhance-profile")
async def enhance_profile(profile: ProfileData):
    """Use AI to generate a complete, professional profile"""
    try:
        prompt = f"""
You are a professional career counselor and resume writer. Create a comprehensive professional profile for:

Name: {profile.first_name} {profile.last_name}
Current Role: {profile.current_role or 'Professional'}
Location: {profile.location or 'Not specified'}
Experience: {profile.experience_years} years
Skills: {', '.join(profile.skills)}
Education: {profile.education or 'Not specified'}
Current Bio: {profile.bio or 'No bio provided'}
Career Goals: {profile.career_goals or 'Seeking new opportunities'}

Generate a JSON response with the following fields:
1. professional_headline: A compelling 1-line professional headline (max 60 chars)
2. professional_summary: A powerful 3-4 sentence professional summary showcasing achievements and expertise
3. detailed_bio: An engaging 2-3 paragraph bio for career site profiles
4. elevator_pitch: A concise 30-second elevator pitch
5. suggested_skills: 10 additional relevant skills based on their experience
6. career_keywords: 15 ATS-optimized keywords for their profile
7. profile_strengths: 5 key strengths to highlight
8. recommended_job_titles: 5 job titles they should apply for

Make it professional, achievement-focused, and optimized for ATS systems.
Return only valid JSON without markdown formatting.
"""

        content = await ai_backend.generate(prompt, max_tokens=1500)
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            result = {
                "professional_headline": f"Experienced {profile.skills[0] if profile.skills else 'Professional'} with {profile.experience_years} years",
                "professional_summary": f"{profile.first_name} is an experienced professional with {profile.experience_years} years in {', '.join(profile.skills[:3])}. Passionate about technology and delivering high-quality solutions.",
                "detailed_bio": f"{profile.first_name} {profile.last_name} is a skilled professional with {profile.experience_years} years of experience. Specializing in {', '.join(profile.skills[:5])}, they have successfully delivered numerous projects and continue to stay at the forefront of technology.",
                "elevator_pitch": f"Hi, I'm {profile.first_name}, a {profile.skills[0] if profile.skills else 'software'} professional with {profile.experience_years} years of experience building scalable solutions.",
                "suggested_skills": ["Problem Solving", "Team Collaboration", "Agile", "Communication", "Leadership", "Project Management", "Code Review", "CI/CD", "Testing", "Documentation"],
                "career_keywords": ["Software Development", "Full Stack", "Web Applications", "API Design", "Database", "Cloud", "DevOps", "Microservices", "Architecture", "Performance", "Security", "Scalability", "Best Practices", "Innovation", "Technical Leadership"],
                "profile_strengths": ["Technical Expertise", "Problem Solving", "Team Collaboration", "Continuous Learning", "Project Delivery"],
                "recommended_job_titles": ["Senior Developer", "Lead Developer", "Technical Lead", "Software Architect", "Engineering Manager"]
            }
        
        logger.info(f"Profile enhanced successfully for {profile.first_name} {profile.last_name}")
        
        return {
            "success": True,
            "enhanced_profile": result,
            "backend": ai_backend.backend,
            "model": ai_backend.model,
            "original_profile": {
                "name": f"{profile.first_name} {profile.last_name}",
                "skills": profile.skills,
                "experience_years": profile.experience_years
            }
        }
        
    except Exception as e:
        logger.error(f"Profile enhancement failed: {e}")
        # Fallback response
        return {
            "success": True,
            "enhanced_profile": {
                "professional_headline": f"Experienced {profile.skills[0] if profile.skills else 'Professional'} Developer",
                "professional_summary": f"{profile.first_name} is an experienced professional with {profile.experience_years} years in {', '.join(profile.skills[:3])}. Passionate about technology and delivering high-quality solutions.",
                "detailed_bio": f"{profile.first_name} {profile.last_name} is a skilled professional with {profile.experience_years} years of experience. Specializing in {', '.join(profile.skills[:5])}, they have successfully delivered numerous projects and continue to stay at the forefront of technology.",
                "elevator_pitch": f"Hi, I'm {profile.first_name}, a {profile.skills[0] if profile.skills else 'software'} professional with {profile.experience_years} years of experience building scalable solutions.",
                "suggested_skills": ["Problem Solving", "Team Collaboration", "Agile", "Communication", "Leadership", "Project Management", "Code Review", "CI/CD", "Testing", "Documentation"],
                "career_keywords": ["Software Development", "Full Stack", "Web Applications", "API Design", "Database", "Cloud", "DevOps", "Microservices", "Architecture", "Performance", "Security", "Scalability", "Best Practices", "Innovation", "Technical Leadership"],
                "profile_strengths": ["Technical Expertise", "Problem Solving", "Team Collaboration", "Continuous Learning", "Project Delivery"],
                "recommended_job_titles": ["Senior Developer", "Lead Developer", "Technical Lead", "Software Architect", "Engineering Manager"]
            },
            "backend": ai_backend.backend,
            "model": ai_backend.model,
            "fallback": True
        }

@app.post("/generate-resume")
async def generate_resume(profile: ProfileData):
    """Generate a complete professional resume using OpenAI"""
    try:
        prompt = f"""
You are an expert resume writer. Create a comprehensive, ATS-optimized resume for:

Name: {profile.first_name} {profile.last_name}
Email: {profile.email}
Phone: {profile.phone or 'N/A'}
Location: {profile.location or 'N/A'}
LinkedIn: {profile.linkedin_url or 'N/A'}
Current Role: {profile.current_role or 'Professional'}
Experience: {profile.experience_years} years
Skills: {', '.join(profile.skills)}
Education: {profile.education or 'N/A'}

Generate a JSON response with these sections:
1. contact_info: Full contact details
2. professional_summary: Powerful 3-4 sentence summary
3. technical_skills: Organized by category (Languages, Frameworks, Tools, etc.)
4. work_experience: 3 detailed job entries with:
   - title, company, duration
   - 4-5 achievement-focused bullet points with metrics
5. education: Degree and institution
6. certifications: Relevant certifications
7. projects: 2-3 key projects with impact
8. achievements: Notable accomplishments

Make it achievement-focused, use action verbs, include metrics, and optimize for ATS.
Return only valid JSON without markdown formatting.
"""

        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_completion_tokens=2000
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        resume_data = json.loads(content)
        
        logger.info(f"Resume generated successfully for {profile.first_name} {profile.last_name}")
        
        return {
            "success": True,
            "resume": resume_data,
            "format": "json"
        }
        
    except Exception as e:
        logger.error(f"Resume generation failed: {e}")
        
        # Enhanced fallback with realistic professional resume
        fallback_resume = {
            "contact_info": {
                "name": f"{profile.first_name} {profile.last_name}",
                "email": profile.email,
                "phone": profile.phone or "+33 X XX XX XX XX",
                "location": profile.location or "France",
                "linkedin": profile.linkedin_url or f"linkedin.com/in/{profile.first_name.lower()}{profile.last_name.lower()}"
            },
            "professional_summary": f"Experienced {profile.current_role or 'Professional'} with {profile.experience_years} years of expertise in {', '.join(profile.skills[:3])}. Proven track record of delivering high-quality solutions and driving technological innovation. Passionate about continuous learning and contributing to team success through collaborative problem-solving and technical excellence.",
            "technical_skills": {
                "Programming Languages": profile.skills[:3] if len(profile.skills) >= 3 else profile.skills,
                "Frameworks & Tools": profile.skills[3:6] if len(profile.skills) > 3 else ["Git", "Docker", "CI/CD"],
                "Databases": ["PostgreSQL", "MongoDB", "Redis"] if any("data" in skill.lower() or "sql" in skill.lower() for skill in profile.skills) else ["SQL", "NoSQL"],
                "Additional Skills": ["Problem Solving", "Team Collaboration", "Agile Methodology", "Code Review", "Technical Documentation"]
            },
            "work_experience": [
                {
                    "title": profile.current_role or "Senior Software Engineer",
                    "company": "Tech Company",
                    "duration": f"{max(1, profile.experience_years - 2)} years",
                    "achievements": [
                        f"Developed and maintained applications using {profile.skills[0] if profile.skills else 'modern technologies'}, improving system performance by 30%",
                        "Led code reviews and mentored junior developers, resulting in improved code quality and team productivity",
                        f"Collaborated with cross-functional teams to deliver {profile.experience_years * 2} successful projects on time and within budget",
                        "Implemented best practices for testing and deployment, reducing production issues by 40%",
                        f"Optimized database queries and application architecture, decreasing response times by 25%"
                    ]
                },
                {
                    "title": "Software Developer",
                    "company": "Previous Company", 
                    "duration": f"{max(1, profile.experience_years - 3)} years",
                    "achievements": [
                        f"Built responsive web applications using {', '.join(profile.skills[:2])} and modern frameworks",
                        "Participated in agile development cycles, contributing to sprint planning and retrospectives",
                        "Integrated third-party APIs and services, enhancing application functionality",
                        "Maintained and refactored legacy code, improving system maintainability"
                    ]
                }
            ],
            "education": profile.education or "Bachelor's Degree in Computer Science",
            "certifications": [
                f"{profile.skills[0] if profile.skills else 'Technology'} Certification",
                "Agile Development Methodology"
            ],
            "projects": [
                {
                    "name": f"{profile.skills[0] if profile.skills else 'Web'} Application Platform",
                    "description": f"Full-stack application built with {', '.join(profile.skills[:2])} featuring user authentication, real-time updates, and scalable architecture"
                },
                {
                    "name": "API Integration System",
                    "description": f"Microservices-based system integrating multiple external APIs, built using {profile.skills[1] if len(profile.skills) > 1 else 'modern technologies'}"
                }
            ],
            "achievements": [
                f"Successfully delivered {profile.experience_years * 3} projects with high client satisfaction",
                "Mentored team members and contributed to knowledge sharing initiatives",
                "Consistently met project deadlines while maintaining high code quality standards"
            ]
        }
        
        return {
            "success": True,
            "resume": fallback_resume,
            "format": "json",
            "fallback": True,
            "note": "Generated using fallback system - connect OpenAI API key for enhanced AI-powered content"
        }

@app.post("/generate-cover-letter")
async def generate_cover_letter(request_data: Dict[str, Any]):
    """Generate a personalized cover letter using AI"""
    try:
        # Extract profile data
        profile_data = {
            "first_name": request_data.get("first_name", ""),
            "last_name": request_data.get("last_name", ""),
            "email": request_data.get("email", ""),
            "experience_years": request_data.get("experience_years", 0),
            "skills": request_data.get("skills", []),
            "current_role": request_data.get("current_role", ""),
            "bio": request_data.get("bio", "")
        }
        
        # Extract job data
        job_data = {
            "title": request_data.get("title", ""),
            "company": request_data.get("company", ""),
            "description": request_data.get("description", ""),
            "requirements": request_data.get("requirements", [])
        }
        
        prompt = f"""
Write a compelling, personalized cover letter for:

Candidate: {profile_data['first_name']} {profile_data['last_name']}
Experience: {profile_data['experience_years']} years
Skills: {', '.join(profile_data['skills'])}
Current Role: {profile_data['current_role'] or 'Professional'}

Applying to:
Position: {job_data['title']}
Company: {job_data['company']}
Requirements: {', '.join(job_data['requirements'])}

Create a 3-paragraph cover letter that:
1. Opens with enthusiasm and explains why they're perfect for this specific role
2. Highlights 2-3 relevant experiences/skills that match the job requirements
3. Closes with a call to action

Make it professional, specific to this company and role, and show genuine interest.
Return only the cover letter text, no JSON formatting.
"""

        content = await ai_backend.generate(prompt, max_tokens=800)
        
        logger.info(f"Cover letter generated for {profile_data['first_name']} applying to {job_data['company']}")
        
        return {
            "success": True,
            "cover_letter": content,
            "job_title": job_data['title'],
            "company": job_data['company'],
            "backend": ai_backend.backend,
            "model": ai_backend.model
        }
        
    except Exception as e:
        logger.error(f"Cover letter generation failed: {e}")
        return {
            "success": True,
            "cover_letter": f"Dear Hiring Manager,\n\nI am writing to express my strong interest in the {request_data.get('title', 'position')} at {request_data.get('company', 'your company')}. With {request_data.get('experience_years', 3)} years of experience in {', '.join(request_data.get('skills', [])[:3])}, I am confident that my skills align perfectly with your requirements.\n\nMy expertise in {request_data.get('skills', ['software development'])[0] if request_data.get('skills') else 'software development'} has prepared me to contribute effectively to your team. I am particularly excited about the opportunity to work with {request_data.get('company', 'your company')} and contribute to your innovative projects.\n\nI look forward to discussing how my background and enthusiasm can benefit your organization.\n\nBest regards,\n{request_data.get('first_name', '')} {request_data.get('last_name', '')}",
            "backend": ai_backend.backend,
            "model": ai_backend.model,
            "fallback": True
        }

@app.post("/generate-profile-sections")
async def generate_profile_sections(profile: ProfileData):
    """Generate specific sections for career site profiles"""
    try:
        prompt = f"""
Generate profile sections for career site registration for:

Name: {profile.first_name} {profile.last_name}
Experience: {profile.experience_years} years
Skills: {', '.join(profile.skills)}
Location: {profile.location or 'Not specified'}

Create a JSON response with:
1. headline: Professional headline (50 chars max)
2. about: "About Me" section (150-200 words)
3. work_preference: Work preferences and culture fit (100 words)
4. career_interests: Career interests (50 words)
5. availability: When they can start
6. salary_expectations: Professional way to state expectations
7. relocation: Willingness to relocate
8. remote_preference: Remote work preferences

Make it engaging and professional.
Return only valid JSON without markdown formatting.
"""

        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are a career counselor helping create profile sections. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_completion_tokens=1000
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        sections = json.loads(content)
        
        return {
            "success": True,
            "sections": sections
        }
        
    except Exception as e:
        logger.error(f"Profile sections generation failed: {e}")
        return {
            "success": True,
            "sections": {
                "headline": f"{profile.skills[0] if profile.skills else 'Software'} Professional",
                "about": f"Experienced professional with {profile.experience_years} years in {', '.join(profile.skills[:3])}. Passionate about technology and innovation.",
                "work_preference": "Seeking a collaborative environment with opportunities for growth and innovation. Values work-life balance and continuous learning.",
                "career_interests": "Interested in challenging projects that leverage cutting-edge technologies and make a real impact.",
                "availability": "Available immediately",
                "salary_expectations": "Competitive salary based on experience and role",
                "relocation": "Open to relocation for the right opportunity",
                "remote_preference": "Flexible with remote, hybrid, or on-site work"
            },
            "fallback": True
        }

async def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    try:
        pdf_file = BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""

async def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file"""
    try:
        doc_file = BytesIO(file_content)
        doc = docx.Document(doc_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        return ""

@app.post("/analyze-resume")
async def analyze_resume(file: UploadFile = File(...)):
    """Upload and analyze resume/CV using AI to extract profile information"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Extract text based on file type
        text_content = ""
        if file.content_type == "application/pdf":
            text_content = await extract_text_from_pdf(file_content)
        elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            text_content = await extract_text_from_docx(file_content)
        elif file.content_type == "text/plain":
            text_content = file_content.decode('utf-8')
        else:
            return {
                "success": False,
                "error": "Unsupported file type. Please upload PDF, DOCX, or TXT files."
            }
        
        if not text_content:
            return {
                "success": False,
                "error": "Could not extract text from the resume. Please try a different file."
            }
        
        # Use AI to analyze resume and extract structured data
        prompt = f"""
Analyze this resume/CV text and extract structured information in JSON format:

RESUME TEXT:
{text_content}

Extract and return a JSON object with these fields:
1. personal_info:
   - first_name, last_name, email, phone, location, linkedin_url
2. professional_summary: A 2-3 sentence summary of their background
3. experience_years: Estimated total years of experience
4. skills: Array of technical and professional skills found
5. work_experience: Array of jobs with title, company, duration, responsibilities
6. education: Highest education level and field
7. languages: Programming languages mentioned
8. frameworks_tools: Frameworks and tools mentioned
9. certifications: Any certifications mentioned
10. projects: Personal or professional projects mentioned

Make sure to extract as much relevant information as possible.
Return only valid JSON without markdown formatting.
"""

        try:
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are an expert resume analyzer. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_completion_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            analysis = json.loads(content)
            
            logger.info(f"Resume analyzed successfully: {file.filename}")
            
            return {
                "success": True,
                "filename": file.filename,
                "analysis": analysis,
                "raw_text_length": len(text_content),
                "message": "Resume analyzed successfully! Profile data extracted and ready for enhancement."
            }
            
        except Exception as ai_error:
            logger.error(f"AI analysis failed: {ai_error}")
            
            # Fallback: Basic text parsing
            lines = text_content.split('\n')
            
            # Try to extract basic info
            email = ""
            phone = ""
            skills = []
            
            for line in lines:
                line = line.strip().lower()
                if '@' in line and not email:
                    # Try to extract email
                    words = line.split()
                    for word in words:
                        if '@' in word and '.' in word:
                            email = word
                            break
                
                if any(skill in line for skill in ['python', 'javascript', 'react', 'java', 'node', 'sql', 'html', 'css']):
                    # Extract common skills
                    common_skills = ['python', 'javascript', 'react', 'java', 'nodejs', 'sql', 'html', 'css', 'git']
                    for skill in common_skills:
                        if skill in line and skill.title() not in skills:
                            skills.append(skill.title())
            
            fallback_analysis = {
                "personal_info": {
                    "first_name": "",
                    "last_name": "",
                    "email": email,
                    "phone": phone,
                    "location": "",
                    "linkedin_url": ""
                },
                "professional_summary": "Experienced professional with diverse technical background",
                "experience_years": 3,
                "skills": skills if skills else ["Programming", "Problem Solving"],
                "work_experience": [],
                "education": "",
                "languages": [],
                "frameworks_tools": [],
                "certifications": [],
                "projects": []
            }
            
            return {
                "success": True,
                "filename": file.filename,
                "analysis": fallback_analysis,
                "raw_text_length": len(text_content),
                "fallback": True,
                "message": "Resume processed with basic parsing. For enhanced AI analysis, add OpenAI API key."
            }
        
    except Exception as e:
        logger.error(f"Resume analysis failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Resume analysis failed. Please try again with a different file."
        }

@app.post("/optimize-for-ats")
async def optimize_for_ats(profile: ProfileData, job: JobData):
    """Optimize profile content for ATS systems"""
    try:
        prompt = f"""
Optimize this profile for ATS (Applicant Tracking Systems) for the job:

Job Title: {job.title}
Requirements: {', '.join(job.requirements)}

Candidate Skills: {', '.join(profile.skills)}
Experience: {profile.experience_years} years

Generate JSON with:
1. matched_keywords: Keywords from job that match candidate
2. missing_keywords: Important keywords candidate should add
3. suggested_additions: How to incorporate missing keywords naturally
4. optimized_skills_list: Reordered skills list prioritizing job match
5. ats_score: Estimated ATS match score (0-100)
6. optimization_tips: 5 specific tips to improve ATS score

Return only valid JSON without markdown formatting.
"""

        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are an ATS optimization expert. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_completion_tokens=1000
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        optimization = json.loads(content)
        
        return {
            "success": True,
            "optimization": optimization,
            "job_title": job.title
        }
        
    except Exception as e:
        logger.error(f"ATS optimization failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8010))
    uvicorn.run(app, host="0.0.0.0", port=port)


@app.post("/analyze-form")
async def analyze_form(request_data: Dict[str, Any]):
    """Analyze HTML form and provide filling strategy using AI"""
    try:
        html_snippet = request_data.get('html', '')
        user_profile = request_data.get('user_profile', {})
        
        prompt = f"""Analyze this HTML form snippet and extract form field selectors for account creation.

HTML Snippet:
{html_snippet[:2000]}

User Profile:
- Email: {user_profile.get('email')}
- Name: {user_profile.get('name')}

Identify CSS selectors for:
1. Email input field
2. Password input field(s)
3. Password confirmation field (if exists)
4. First name field (if exists)
5. Last name field (if exists)
6. Terms/agreement checkbox (if exists)
7. Submit button

Also identify password requirements.
Generate a unique timestamped email and strong password that meets requirements.

Respond with JSON containing selectors and suggested values."""

        content = await ai_backend.generate(prompt, max_tokens=600)
        
        # Try to parse as JSON
        import time
        import re
        
        try:
            # Clean up response to extract JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                strategy = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found")
        except:
            # Fallback strategy
            timestamp = int(time.time())
            email_base = user_profile.get('email', 'user@example.com').split('@')[0]
            strategy = {
                "email_selector": "input[type='email']",
                "password_selector": "input[type='password']",
                "password_confirm_selector": None,
                "first_name_selector": "input[name*='first']",
                "last_name_selector": "input[name*='last']",
                "terms_checkbox_selector": "input[type='checkbox']",
                "submit_button_selector": "button[type='submit']",
                "suggested_email": f"{email_base}_wttj{timestamp}@gmail.com",
                "suggested_password": f"Secure{timestamp}Pass!",
                "password_requirements": ["8+ characters", "uppercase", "lowercase", "number"]
            }
        
        return strategy
        
    except Exception as e:
        logger.error(f"Form analysis error: {e}")
        # Return fallback strategy
        timestamp = int(time.time())
        return {
            "email_selector": "input[type='email']",
            "password_selector": "input[type='password']",
            "submit_button_selector": "button[type='submit']",
            "suggested_email": f"user_wttj{timestamp}@gmail.com",
            "suggested_password": f"Secure{timestamp}!",
            "password_requirements": ["8+ characters"]
        }
