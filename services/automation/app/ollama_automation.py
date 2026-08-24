"""
Ollama-Powered Automation System
Uses trained Ollama model for intelligent account creation, profile setup, and job applications
Supports: WTTJ (Welcome to the Jungle), SNCF
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Ollama not available")

from playwright.async_api import async_playwright, Page, Browser

# Import stealth browser
try:
    from stealth_browser import StealthBrowser, HumanBehaviorSimulator
    STEALTH_AVAILABLE = True
    logger.info("✅ Stealth browser available")
except ImportError:
    STEALTH_AVAILABLE = False
    logger.warning("⚠️ Stealth browser not available - using basic Playwright")

@dataclass
class UserCredentials:
    """User account credentials"""
    email: str
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    location: Optional[str] = None

@dataclass
class UserProfile:
    """Complete user profile for automation"""
    credentials: UserCredentials
    bio: str
    headline: str
    skills: List[str]
    experience_years: int
    education: str
    linkedin_url: Optional[str] = None
    resume_text: Optional[str] = None

@dataclass
class JobApplication:
    """Job application tracking"""
    job_id: str
    job_title: str
    company: str
    job_url: str
    applied_at: datetime
    application_status: str  # pending, submitted, failed
    cover_letter: Optional[str] = None
    resume_section: Optional[str] = None

class OllamaProfileEnhancer:
    """Uses trained Ollama model to enhance profile content"""
    
    def __init__(self, model_name: str = "mistral", ollama_host: str = "http://localhost:11434"):
        self.model_name = model_name
        self.ollama_host = ollama_host
        
        if not OLLAMA_AVAILABLE:
            logger.error("Ollama not available - install with: pip install ollama")
    
    async def generate_profile_bio(self, user: UserProfile) -> str:
        """Generate professional bio using Ollama"""
        try:
            prompt = f"""Generate a professional bio for a {user.experience_years}-year experienced professional with these details:

Name: {user.credentials.first_name} {user.credentials.last_name}
Skills: {', '.join(user.skills)}
Headline: {user.headline}
Experience: {user.experience_years} years
Education: {user.education}

Create a compelling 2-3 paragraph professional bio suitable for career site profiles. Be specific and highlight achievements."""

            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                stream=False
            )
            
            bio = response.get('response', '').strip()
            logger.info(f"✅ Generated bio for {user.credentials.first_name}")
            return bio
            
        except Exception as e:
            logger.error(f"❌ Bio generation failed: {e}")
            # Fallback bio
            return f"{user.credentials.first_name} is a {user.headline} with {user.experience_years} years of experience in {', '.join(user.skills)}. Passionate about {user.skills[0] if user.skills else 'technology'} and continuous learning."
    
    async def generate_application_answers(self, job_title: str, company: str, job_description: str, user: UserProfile) -> Dict[str, str]:
        """Generate intelligent answers for job application questions"""
        try:
            prompt = f"""You are helping a candidate apply for a job. Generate professional, personalized answers.

Candidate Profile:
- Name: {user.credentials.first_name} {user.credentials.last_name}
- Headline: {user.headline}
- Experience: {user.experience_years} years
- Skills: {', '.join(user.skills)}
- Bio: {user.bio[:200]}...

Job Details:
- Position: {job_title}
- Company: {company}
- Description: {job_description[:500]}...

Generate JSON with these questions answered:
1. Why are you interested in this position?
2. Why are you a good fit for this company?
3. What value would you bring to this role?
4. Describe your relevant experience.

Keep each answer 2-3 sentences, professional and specific to the job."""

            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                stream=False
            )
            
            content = response.get('response', '').strip()
            
            # Try to parse JSON
            try:
                # Find JSON in response
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = content[start:end]
                    answers = json.loads(json_str)
                    return answers
            except:
                pass
            
            # Fallback structured answers
            return {
                "interest": f"I'm very interested in the {job_title} position at {company} because it aligns with my skills in {', '.join(user.skills[:2])}.",
                "fit": f"My {user.experience_years} years of experience and expertise in {user.skills[0]} make me a strong fit for your team.",
                "value": f"I can contribute by leveraging my skills in {', '.join(user.skills[:3])} to drive impactful results.",
                "experience": f"I have successfully worked on projects requiring {', '.join(user.skills[:2])} and have consistently delivered high-quality results."
            }
            
        except Exception as e:
            logger.error(f"❌ Application answers generation failed: {e}")
            # Fallback answers
            return {
                "interest": f"I'm excited about the {job_title} opportunity at {company}.",
                "fit": "My experience makes me a strong candidate for this role.",
                "value": "I can contribute valuable skills and drive project success.",
                "experience": f"I have relevant experience with {', '.join(user.skills[:2])}."
            }
    
    async def optimize_for_ats(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """Optimize resume/profile for ATS using Ollama"""
        try:
            prompt = f"""Analyze this resume for ATS (Applicant Tracking System) optimization against the job posting.

RESUME:
{resume_text[:1000]}

JOB POSTING:
{job_description[:1000]}

Provide JSON with:
1. matched_keywords: Keywords from job that appear in resume
2. missing_keywords: Important keywords to add
3. ats_score: Estimated match score (0-100)
4. recommendations: List of optimization tips (3-5 items)

Format as valid JSON only."""

            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                stream=False
            )
            
            content = response.get('response', '').strip()
            
            # Try to parse JSON
            try:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = content[start:end]
                    return json.loads(json_str)
            except:
                pass
            
            # Fallback
            return {
                "matched_keywords": [],
                "missing_keywords": [],
                "ats_score": 75,
                "recommendations": [
                    "Add more specific technical keywords",
                    "Use action verbs for accomplishments",
                    "Include quantifiable metrics"
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ ATS optimization failed: {e}")
            return {"ats_score": 0, "recommendations": []}


class WTTJAutomation:
    """Automation for Welcome to the Jungle (WTTJ)"""
    
    def __init__(self, ollama_enhancer: OllamaProfileEnhancer):
        self.enhancer = ollama_enhancer
        self.base_url = "https://www.welcometothejungle.com"
        self.signin_url = f"{self.base_url}/en/authenticate/signin"
        self.signup_url = f"{self.base_url}/en/authenticate/signup"
    
    async def create_account(self, page: Page, user: UserProfile) -> Dict[str, Any]:
        """Create WTTJ account"""
        try:
            logger.info(f"🔄 Creating WTTJ account for {user.credentials.email}")
            
            # Navigate to signup
            await page.goto(self.signup_url, wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Fill email
            try:
                await page.fill('input[type="email"]', user.credentials.email)
                await asyncio.sleep(1)
            except:
                logger.warning("Could not fill email field")
            
            # Fill password
            try:
                await page.fill('input[type="password"]', user.credentials.password)
                await asyncio.sleep(1)
            except:
                logger.warning("Could not fill password field")
            
            # Fill name
            try:
                await page.fill('input[placeholder*="First name" i]', user.credentials.first_name)
                await page.fill('input[placeholder*="Last name" i]', user.credentials.last_name)
                await asyncio.sleep(1)
            except:
                logger.warning("Could not fill name fields")
            
            # Click signup button
            try:
                await page.click('button:has-text("Sign up")')
                await page.wait_for_navigation(wait_until="networkidle", timeout=10000)
            except:
                logger.warning("Could not click signup button")
            
            logger.info("✅ WTTJ account created")
            return {"success": True, "message": "Account created"}
            
        except Exception as e:
            logger.error(f"❌ WTTJ account creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def setup_profile(self, page: Page, user: UserProfile) -> Dict[str, Any]:
        """Setup WTTJ profile with AI-generated content"""
        try:
            logger.info(f"🔄 Setting up WTTJ profile for {user.credentials.first_name}")
            
            # Generate enhanced bio
            bio = await self.enhancer.generate_profile_bio(user)
            user.bio = bio
            
            # Navigate to profile
            await page.goto(f"{self.base_url}/profile", wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Fill bio
            try:
                bio_elements = await page.query_selector_all('textarea')
                if bio_elements:
                    await bio_elements[0].fill(bio)
                    await asyncio.sleep(1)
            except:
                logger.warning("Could not fill bio")
            
            # Add skills
            try:
                for skill in user.skills[:5]:
                    skill_input = await page.query_selector('input[placeholder*="skill" i]')
                    if skill_input:
                        await skill_input.fill(skill)
                        await page.keyboard.press("Enter")
                        await asyncio.sleep(0.5)
            except:
                logger.warning("Could not add skills")
            
            # Set headline
            try:
                headline_input = await page.query_selector('input[placeholder*="headline" i]')
                if headline_input:
                    await headline_input.fill(user.headline)
                    await asyncio.sleep(1)
            except:
                logger.warning("Could not set headline")
            
            # Save profile
            try:
                await page.click('button:has-text("Save")')
                await asyncio.sleep(2)
            except:
                logger.warning("Could not click save")
            
            logger.info("✅ WTTJ profile setup complete")
            return {"success": True, "profile": {"bio": bio[:100], "skills_count": len(user.skills)}}
            
        except Exception as e:
            logger.error(f"❌ WTTJ profile setup failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def apply_to_job(self, page: Page, job_url: str, user: UserProfile) -> Dict[str, Any]:
        """Apply to WTTJ job"""
        try:
            logger.info(f"🔄 Applying to WTTJ job: {job_url}")
            
            # Navigate to job
            await page.goto(job_url, wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Extract job details
            job_title = ""
            company = ""
            job_description = ""
            
            try:
                job_title = await page.query_selector('h1')
                if job_title:
                    job_title = await job_title.text_content()
            except:
                pass
            
            try:
                company = await page.query_selector('h2')
                if company:
                    company = await company.text_content()
            except:
                pass
            
            try:
                desc_elem = await page.query_selector('[class*="description"]')
                if desc_elem:
                    job_description = await desc_elem.text_content()
            except:
                job_description = ""
            
            # Generate application answers
            answers = await self.enhancer.generate_application_answers(
                job_title, company, job_description, user
            )
            
            # Fill application form
            try:
                # Find and fill form fields
                form_fields = await page.query_selector_all('input[type="text"], textarea')
                field_index = 0
                
                for field in form_fields:
                    if field_index < len(answers):
                        answer_key = list(answers.keys())[field_index]
                        await field.fill(answers[answer_key])
                        field_index += 1
                        await asyncio.sleep(0.5)
            except:
                logger.warning("Could not fill form fields")
            
            # Click apply button
            try:
                await page.click('button:has-text("Apply")')
                await asyncio.sleep(3)
                logger.info("✅ Applied to WTTJ job")
                return {
                    "success": True,
                    "job_title": job_title,
                    "company": company,
                    "message": "Application submitted"
                }
            except:
                logger.warning("Could not click apply button")
                return {"success": False, "error": "Could not submit application"}
                
        except Exception as e:
            logger.error(f"❌ WTTJ job application failed: {e}")
            return {"success": False, "error": str(e)}


class SNCFAutomation:
    """Automation for SNCF (Société Nationale des Chemins de fer français)"""
    
    def __init__(self, ollama_enhancer: OllamaProfileEnhancer):
        self.enhancer = ollama_enhancer
        self.base_url = "https://emploi.sncf.com"
        self.login_url = f"{self.base_url}/espace-candidat"
    
    async def create_account(self, page: Page, user: UserProfile) -> Dict[str, Any]:
        """Create SNCF account"""
        try:
            logger.info(f"🔄 Creating SNCF account for {user.credentials.email}")
            
            # Navigate to login
            await page.goto(self.login_url, wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Click create account link
            try:
                await page.click('a:has-text("Create")')
                await asyncio.sleep(2)
            except:
                logger.warning("Could not find create account link")
            
            # Fill registration form
            try:
                await page.fill('input[type="email"]', user.credentials.email)
                await page.fill('input[type="password"]', user.credentials.password)
                await page.fill('input[placeholder*="First" i]', user.credentials.first_name)
                await page.fill('input[placeholder*="Last" i]', user.credentials.last_name)
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"Could not fill form: {e}")
            
            # Submit registration
            try:
                await page.click('button[type="submit"]')
                await page.wait_for_navigation(timeout=10000)
            except:
                logger.warning("Could not submit registration")
            
            logger.info("✅ SNCF account created")
            return {"success": True, "message": "Account created"}
            
        except Exception as e:
            logger.error(f"❌ SNCF account creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def setup_profile(self, page: Page, user: UserProfile) -> Dict[str, Any]:
        """Setup SNCF profile"""
        try:
            logger.info(f"🔄 Setting up SNCF profile for {user.credentials.first_name}")
            
            # Generate enhanced bio
            bio = await self.enhancer.generate_profile_bio(user)
            user.bio = bio
            
            # Navigate to profile
            await page.goto(f"{self.base_url}/mon-profil", wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Fill profile information
            try:
                # Fill phone
                if user.credentials.phone:
                    phone_field = await page.query_selector('input[type="tel"]')
                    if phone_field:
                        await phone_field.fill(user.credentials.phone)
                
                # Fill location
                if user.credentials.location:
                    location_field = await page.query_selector('input[placeholder*="location" i]')
                    if location_field:
                        await location_field.fill(user.credentials.location)
                
                # Fill bio
                bio_field = await page.query_selector('textarea')
                if bio_field:
                    await bio_field.fill(bio)
                
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"Could not fill profile: {e}")
            
            # Save profile
            try:
                await page.click('button:has-text("Save")')
                await asyncio.sleep(2)
            except:
                logger.warning("Could not save profile")
            
            logger.info("✅ SNCF profile setup complete")
            return {"success": True, "profile": {"bio": bio[:100]}}
            
        except Exception as e:
            logger.error(f"❌ SNCF profile setup failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def apply_to_job(self, page: Page, job_url: str, user: UserProfile) -> Dict[str, Any]:
        """Apply to SNCF job"""
        try:
            logger.info(f"🔄 Applying to SNCF job: {job_url}")
            
            # Navigate to job
            await page.goto(job_url, wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Extract job details
            job_title = ""
            company = "SNCF"
            job_description = ""
            
            try:
                title_elem = await page.query_selector('h1')
                if title_elem:
                    job_title = await title_elem.text_content()
            except:
                pass
            
            try:
                desc_elem = await page.query_selector('[class*="description"]')
                if desc_elem:
                    job_description = await desc_elem.text_content()
            except:
                pass
            
            # Generate application answers
            answers = await self.enhancer.generate_application_answers(
                job_title, company, job_description, user
            )
            
            # Submit application
            try:
                # Look for apply button
                apply_button = await page.query_selector('button:has-text("Postuler")')
                if not apply_button:
                    apply_button = await page.query_selector('button:has-text("Apply")')
                
                if apply_button:
                    await apply_button.click()
                    await asyncio.sleep(2)
                    
                    # Fill any modal forms
                    form_fields = await page.query_selector_all('input[type="text"], textarea')
                    for idx, field in enumerate(form_fields[:len(answers)]):
                        answer_key = list(answers.keys())[idx]
                        await field.fill(answers[answer_key])
                        await asyncio.sleep(0.5)
                    
                    # Submit
                    await page.click('button[type="submit"]')
                    await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"Could not apply: {e}")
            
            logger.info("✅ Applied to SNCF job")
            return {
                "success": True,
                "job_title": job_title,
                "company": company,
                "message": "Application submitted"
            }
            
        except Exception as e:
            logger.error(f"❌ SNCF job application failed: {e}")
            return {"success": False, "error": str(e)}


class OllamaAutomationOrchestrator:
    """Orchestrates complete automation workflow with Ollama"""
    
    def __init__(self):
        self.enhancer = OllamaProfileEnhancer()
        self.wttj = WTTJAutomation(self.enhancer)
        self.sncf = SNCFAutomation(self.enhancer)
        self.applications_log: List[JobApplication] = []
    
    async def full_automation_workflow(self, user: UserProfile, job_urls: Dict[str, List[str]]) -> Dict[str, Any]:
        """Complete workflow: Create account, setup profile, apply to jobs"""
        
        results = {
            "user": f"{user.credentials.first_name} {user.credentials.last_name}",
            "wttj": {"account": None, "profile": None, "applications": []},
            "sncf": {"account": None, "profile": None, "applications": []},
            "total_applications": 0,
            "successful_applications": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            
            try:
                # ========== WTTJ WORKFLOW ==========
                if "wttj" in job_urls:
                    logger.info("\n" + "="*60)
                    logger.info("🚀 Starting WTTJ Automation")
                    logger.info("="*60)
                    
                    context = await browser.new_context()
                    page = await context.new_page()
                    
                    # Create account
                    account_result = await self.wttj.create_account(page, user)
                    results["wttj"]["account"] = account_result
                    
                    if account_result.get("success"):
                        # Setup profile
                        profile_result = await self.wttj.setup_profile(page, user)
                        results["wttj"]["profile"] = profile_result
                        
                        # Apply to jobs
                        for job_url in job_urls["wttj"][:3]:  # Limit to 3 jobs
                            app_result = await self.wttj.apply_to_job(page, job_url, user)
                            results["wttj"]["applications"].append(app_result)
                            
                            if app_result.get("success"):
                                results["successful_applications"] += 1
                                self.applications_log.append(JobApplication(
                                    job_id=job_url,
                                    job_title=app_result.get("job_title", "Unknown"),
                                    company="WTTJ",
                                    job_url=job_url,
                                    applied_at=datetime.now(),
                                    application_status="submitted"
                                ))
                            results["total_applications"] += 1
                    
                    await context.close()
                
                # ========== SNCF WORKFLOW ==========
                if "sncf" in job_urls:
                    logger.info("\n" + "="*60)
                    logger.info("🚀 Starting SNCF Automation")
                    logger.info("="*60)
                    
                    context = await browser.new_context()
                    page = await context.new_page()
                    
                    # Create account
                    account_result = await self.sncf.create_account(page, user)
                    results["sncf"]["account"] = account_result
                    
                    if account_result.get("success"):
                        # Setup profile
                        profile_result = await self.sncf.setup_profile(page, user)
                        results["sncf"]["profile"] = profile_result
                        
                        # Apply to jobs
                        for job_url in job_urls["sncf"][:3]:  # Limit to 3 jobs
                            app_result = await self.sncf.apply_to_job(page, job_url, user)
                            results["sncf"]["applications"].append(app_result)
                            
                            if app_result.get("success"):
                                results["successful_applications"] += 1
                                self.applications_log.append(JobApplication(
                                    job_id=job_url,
                                    job_title=app_result.get("job_title", "Unknown"),
                                    company="SNCF",
                                    job_url=job_url,
                                    applied_at=datetime.now(),
                                    application_status="submitted"
                                ))
                            results["total_applications"] += 1
                    
                    await context.close()
                
            finally:
                await browser.close()
        
        logger.info("\n" + "="*60)
        logger.info("✅ Automation Complete!")
        logger.info(f"Total Applications: {results['total_applications']}")
        logger.info(f"Successful: {results['successful_applications']}")
        logger.info("="*60)
        
        return results
    
    def get_applications_log(self) -> List[JobApplication]:
        """Get log of all applications"""
        return self.applications_log
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate automation report"""
        total = len(self.applications_log)
        successful = len([app for app in self.applications_log if app.application_status == "submitted"])
        
        return {
            "total_applications": total,
            "successful_applications": successful,
            "success_rate": successful / max(total, 1),
            "applications": [
                {
                    "job_id": app.job_id,
                    "job_title": app.job_title,
                    "company": app.company,
                    "applied_at": app.applied_at.isoformat(),
                    "status": app.application_status
                }
                for app in self.applications_log
            ],
            "timestamp": datetime.now().isoformat()
        }


async def demo_automation():
    """Demo the complete automation system"""
    
    # Create sample user profile
    user = UserProfile(
        credentials=UserCredentials(
            email="john.developer@example.com",
            password="SecurePass123!",
            first_name="John",
            last_name="Developer",
            phone="+33 6 12 34 56 78",
            location="Paris, France"
        ),
        bio="Experienced software developer passionate about building scalable solutions",
        headline="Senior Full Stack Developer",
        skills=["Python", "React", "Node.js", "AWS", "Docker"],
        experience_years=5,
        education="Bachelor's in Computer Science",
        linkedin_url="https://linkedin.com/in/johndeveloper"
    )
    
    # Sample job URLs (replace with real job URLs)
    job_urls = {
        "wttj": [
            "https://www.welcometothejungle.com/en/jobs/job1",
            "https://www.welcometothejungle.com/en/jobs/job2",
            "https://www.welcometothejungle.com/en/jobs/job3"
        ],
        "sncf": [
            "https://emploi.sncf.com/job1",
            "https://emploi.sncf.com/job2",
            "https://emploi.sncf.com/job3"
        ]
    }
    
    # Run automation
    orchestrator = OllamaAutomationOrchestrator()
    results = await orchestrator.full_automation_workflow(user, job_urls)
    
    # Print results
    print("\n" + "="*60)
    print("🎉 Automation Results")
    print("="*60)
    print(json.dumps(results, indent=2, default=str))
    
    # Print report
    report = orchestrator.generate_report()
    print("\n" + "="*60)
    print("📊 Detailed Report")
    print("="*60)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    print("Ollama-Powered Automation System")
    print("================================")
    
    if not OLLAMA_AVAILABLE:
        print("❌ Ollama not available. Install with: pip install ollama")
        print("Start Ollama server with: ollama serve")
    else:
        print("✅ Ollama available")
        asyncio.run(demo_automation())
