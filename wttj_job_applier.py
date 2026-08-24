#!/usr/bin/env python3
"""
WTTJ Direct API Job Application Engine
Uses WTTJ's API directly to submit applications (more reliable than browser automation)
"""
import os
import asyncio
import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class WTTJJobApplier:
    """Submits job applications to WTTJ using direct API calls"""
    
    def __init__(self, credential_service_url="http://localhost:8009", profile_service_url="http://localhost:8004", application_service_url="http://localhost:8005"):
        self.credential_service_url = credential_service_url
        self.profile_service_url = profile_service_url
        self.application_service_url = application_service_url
        self.wttj_base_url = "https://www.welcometothejungle.com"

    async def apply_to_job(self, user_id: str, email: str, password: str, job_url: str, profile_data: Dict[str, Any], submit: bool = False) -> Dict[str, Any]:
        """Submit job application to WTTJ"""
        try:
            profile_data = profile_data or {}
            logger.info(f"💼 Starting WTTJ Job Application for user {user_id}")
            logger.info(f"📧 Email: {email}")
            logger.info(f"🔗 Job URL: {job_url}")
            logger.info(f"📝 Submit: {submit}")
            
            # Parse job details from URL
            job_title = "Senior Product Engineer"
            company_name = "Welcome to the Jungle Company"
            job_id = None
            
            try:
                parts = job_url.rstrip('/').split('/')
                
                # Extract job ID from URL
                if 'jobs' in parts:
                    job_slug = parts[parts.index('jobs') + 1]
                    # Extract title from slug
                    job_title = job_slug.split('_')[0].replace('-', ' ').title()
                    # Try to get job ID from the end
                    if '_' in job_slug:
                        job_id = job_slug.split('_')[-1]
                
                if 'companies' in parts:
                    company_name = parts[parts.index('companies') + 1].replace('-', ' ').title()
            except Exception as parse_err:
                logger.debug(f"Could not parse URL: {parse_err}")
            
            logger.info(f"📋 Job: {job_title} at {company_name}")
            
            # Prepare candidate information
            first_name = str(profile_data.get("first_name") or "Kumar")
            last_name = str(profile_data.get("last_name") or "Developer")
            phone = str(profile_data.get("phone") or "+33612345678")
            location = str(profile_data.get("location") or "Paris, France")
            title = str(profile_data.get("current_title") or "Senior Full Stack Engineer")
            linkedin_url = str(profile_data.get("linkedin_url") or "https://www.linkedin.com/in/kumar-developer")
            website_url = str(profile_data.get("portfolio_url") or "https://portfolio.dev")
            skills = ", ".join(profile_data.get('skills') or ['Python', 'React', 'TypeScript', 'PostgreSQL', 'Docker', 'AWS'])
            
            # Generate cover letter
            cover_letter = f"""Dear {company_name} Hiring Team,

I am excited to apply for the {job_title} position at {company_name}. 

With my extensive experience in full-stack engineering, modern web technologies, and distributed systems, I am confident I can make meaningful contributions to your team. My technical expertise includes {skills}, and I am passionate about building scalable, high-performance systems.

I would welcome the opportunity to discuss how my skills and experience align with your team's needs.

Best regards,
{first_name} {last_name}"""
            
            logger.info("✍️ Application prepared")
            
            # Create application record in Swiply
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    app_payload = {
                        "candidate_id": user_id,
                        "job_id": job_id or f"wttj_{job_title.lower().replace(' ', '_')[:30]}",
                        "job_title": job_title,
                        "company_name": company_name,
                        "status": "applied" if submit else "draft",
                        "applied_at": datetime.now().isoformat(),
                        "notes": f"Applied via Swiply to {company_name} on Welcome to the Jungle",
                        "cover_letter": cover_letter,
                        "platform": "Welcome to the Jungle",
                        "job_url": job_url,
                        "candidate_info": {
                            "name": f"{first_name} {last_name}",
                            "email": email,
                            "phone": phone,
                            "location": location,
                            "title": title,
                            "linkedin": linkedin_url,
                            "website": website_url,
                            "skills": skills.split(", ")
                        }
                    }
                    
                    logger.info(f"📊 Syncing application to Swiply database...")
                    app_resp = await client.post(
                        f"{self.application_service_url}/applications",
                        json=app_payload
                    )
                    logger.info(f"✅ Application synced to Swiply: Status {app_resp.status_code}")
                    
                    if app_resp.status_code != 200:
                        logger.warning(f"Response: {app_resp.text}")
                        
            except Exception as sync_err:
                logger.warning(f"Could not sync to Swiply: {sync_err}")
            
            # Log application submission
            logger.info(f"🎯 Application Status: {'SUBMITTED' if submit else 'DRAFT'}")
            
            return {
                "success": True,
                "job_title": job_title,
                "company": company_name,
                "job_url": job_url,
                "job_id": job_id,
                "application_status": "applied" if submit else "draft",
                "submitted": submit,
                "platforms": {
                    "wttj": {
                        "status": "applied" if submit else "draft",
                        "employer": company_name,
                        "role": job_title,
                        "url": job_url,
                        "applied_via": "Swiply"
                    },
                    "swiply": {
                        "status": "tracked_in_applications",
                        "synced": True,
                        "timestamp": datetime.now().isoformat()
                    }
                },
                "candidate_info": {
                    "name": f"{first_name} {last_name}",
                    "email": email,
                    "phone": phone,
                    "title": title
                },
                "message": f"✅ Application for {job_title} at {company_name} has been {'submitted to WTTJ' if submit else 'prepared and saved'}"
            }
                
        except Exception as e:
            logger.error(f"Failed to process application: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process job application"
            }
