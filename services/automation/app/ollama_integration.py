"""
Ollama Integration with Existing Automation Service
Bridges Ollama-powered automation with FastAPI endpoints
"""

import os
import sys
import logging
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from ollama_automation import (
    OllamaAutomationOrchestrator,
    OllamaProfileEnhancer,
    UserProfile,
    UserCredentials,
    WTTJAutomation,
    SNCFAutomation
)

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8010")
AUTOMATION_DB_PATH = os.getenv("AUTOMATION_DB_PATH", "automation_tracking.db")


class OllamaAutomationService:
    """Service for managing Ollama-powered automation with tracking"""
    
    def __init__(self):
        self.orchestrator = OllamaAutomationOrchestrator()
        self.enhancer = OllamaProfileEnhancer()
        self.setup_database()
    
    def setup_database(self):
        """Setup SQLite database for automation tracking"""
        try:
            import sqlite3
            conn = sqlite3.connect(AUTOMATION_DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS automation_accounts (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT,
                    site_name TEXT,
                    email TEXT,
                    account_created DATETIME,
                    profile_setup DATETIME,
                    status TEXT,
                    error_message TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS automation_applications (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT,
                    site_name TEXT,
                    job_id TEXT,
                    job_title TEXT,
                    company TEXT,
                    job_url TEXT,
                    applied_at DATETIME,
                    status TEXT,
                    cover_letter TEXT,
                    ai_quality_score FLOAT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS automation_tracking (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT,
                    total_applications INTEGER,
                    successful_applications INTEGER,
                    success_rate FLOAT,
                    started_at DATETIME,
                    completed_at DATETIME,
                    automation_log TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ Automation tracking database initialized")
            
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
    
    async def create_user_profile(self, user_data: Dict) -> UserProfile:
        """Create user profile from data"""
        try:
            credentials = UserCredentials(
                email=user_data.get("email", ""),
                password=user_data.get("password", ""),
                first_name=user_data.get("first_name", ""),
                last_name=user_data.get("last_name", ""),
                phone=user_data.get("phone"),
                location=user_data.get("location")
            )
            
            profile = UserProfile(
                credentials=credentials,
                bio=user_data.get("bio", ""),
                headline=user_data.get("headline", "Professional"),
                skills=user_data.get("skills", []),
                experience_years=user_data.get("experience_years", 0),
                education=user_data.get("education", ""),
                linkedin_url=user_data.get("linkedin_url"),
                resume_text=user_data.get("resume_text")
            )
            
            logger.info(f"✅ Created profile for {credentials.first_name}")
            return profile
            
        except Exception as e:
            logger.error(f"❌ Profile creation failed: {e}")
            raise
    
    async def run_account_creation(self, user_id: str, user_data: Dict, sites: List[str]) -> Dict:
        """Create accounts on specified sites"""
        results = {
            "user_id": user_id,
            "sites": sites,
            "accounts_created": [],
            "accounts_failed": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Create user profile
            user = await self.create_user_profile(user_data)
            
            # Create accounts
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                
                if "wttj" in sites:
                    try:
                        logger.info("🔄 Creating WTTJ account...")
                        context = await browser.new_context()
                        page = await context.new_page()
                        
                        result = await self.orchestrator.wttj.create_account(page, user)
                        
                        if result.get("success"):
                            results["accounts_created"].append("wttj")
                            self._save_account_creation(user_id, "wttj", user_data["email"], "success")
                        else:
                            results["accounts_failed"].append({"site": "wttj", "error": result.get("error")})
                            self._save_account_creation(user_id, "wttj", user_data["email"], "failed", result.get("error"))
                        
                        await context.close()
                    except Exception as e:
                        logger.error(f"❌ WTTJ account creation failed: {e}")
                        results["accounts_failed"].append({"site": "wttj", "error": str(e)})
                
                if "sncf" in sites:
                    try:
                        logger.info("🔄 Creating SNCF account...")
                        context = await browser.new_context()
                        page = await context.new_page()
                        
                        result = await self.orchestrator.sncf.create_account(page, user)
                        
                        if result.get("success"):
                            results["accounts_created"].append("sncf")
                            self._save_account_creation(user_id, "sncf", user_data["email"], "success")
                        else:
                            results["accounts_failed"].append({"site": "sncf", "error": result.get("error")})
                            self._save_account_creation(user_id, "sncf", user_data["email"], "failed", result.get("error"))
                        
                        await context.close()
                    except Exception as e:
                        logger.error(f"❌ SNCF account creation failed: {e}")
                        results["accounts_failed"].append({"site": "sncf", "error": str(e)})
                
                await browser.close()
            
        except Exception as e:
            logger.error(f"❌ Account creation workflow failed: {e}")
            results["error"] = str(e)
        
        return results
    
    async def run_profile_setup(self, user_id: str, user_data: Dict, sites: List[str]) -> Dict:
        """Setup profiles on specified sites using AI"""
        results = {
            "user_id": user_id,
            "sites": sites,
            "profiles_setup": [],
            "profiles_failed": [],
            "ai_enhanced_content": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Create user profile
            user = await self.create_user_profile(user_data)
            
            # Generate AI-enhanced content
            bio = await self.enhancer.generate_profile_bio(user)
            user.bio = bio
            
            results["ai_enhanced_content"] = {
                "bio": bio,
                "headline": user.headline,
                "skills": user.skills
            }
            
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                
                if "wttj" in sites:
                    try:
                        logger.info("🔄 Setting up WTTJ profile...")
                        context = await browser.new_context()
                        page = await context.new_page()
                        
                        result = await self.orchestrator.wttj.setup_profile(page, user)
                        
                        if result.get("success"):
                            results["profiles_setup"].append("wttj")
                            self._save_profile_setup(user_id, "wttj", "success")
                        else:
                            results["profiles_failed"].append({"site": "wttj", "error": result.get("error")})
                            self._save_profile_setup(user_id, "wttj", "failed", result.get("error"))
                        
                        await context.close()
                    except Exception as e:
                        logger.error(f"❌ WTTJ profile setup failed: {e}")
                        results["profiles_failed"].append({"site": "wttj", "error": str(e)})
                
                if "sncf" in sites:
                    try:
                        logger.info("🔄 Setting up SNCF profile...")
                        context = await browser.new_context()
                        page = await context.new_page()
                        
                        result = await self.orchestrator.sncf.setup_profile(page, user)
                        
                        if result.get("success"):
                            results["profiles_setup"].append("sncf")
                            self._save_profile_setup(user_id, "sncf", "success")
                        else:
                            results["profiles_failed"].append({"site": "sncf", "error": result.get("error")})
                            self._save_profile_setup(user_id, "sncf", "failed", result.get("error"))
                        
                        await context.close()
                    except Exception as e:
                        logger.error(f"❌ SNCF profile setup failed: {e}")
                        results["profiles_failed"].append({"site": "sncf", "error": str(e)})
                
                await browser.close()
            
        except Exception as e:
            logger.error(f"❌ Profile setup workflow failed: {e}")
            results["error"] = str(e)
        
        return results
    
    async def run_job_applications(self, user_id: str, user_data: Dict, job_urls: Dict[str, List[str]]) -> Dict:
        """Apply to jobs using AI-generated content"""
        results = {
            "user_id": user_id,
            "job_urls": job_urls,
            "applications_submitted": 0,
            "applications_failed": 0,
            "applications": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Create user profile
            user = await self.create_user_profile(user_data)
            
            # Generate AI-enhanced content
            bio = await self.enhancer.generate_profile_bio(user)
            user.bio = bio
            
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                
                # Apply to WTTJ jobs
                if "wttj" in job_urls:
                    try:
                        logger.info("🔄 Applying to WTTJ jobs...")
                        context = await browser.new_context()
                        page = await context.new_page()
                        
                        for job_url in job_urls["wttj"][:5]:  # Limit to 5 jobs
                            try:
                                result = await self.orchestrator.wttj.apply_to_job(page, job_url, user)
                                
                                if result.get("success"):
                                    results["applications_submitted"] += 1
                                    results["applications"].append({
                                        "site": "wttj",
                                        "job_url": job_url,
                                        "job_title": result.get("job_title"),
                                        "status": "submitted"
                                    })
                                    self._save_application(user_id, "wttj", job_url, result.get("job_title"), "submitted")
                                else:
                                    results["applications_failed"] += 1
                                    results["applications"].append({
                                        "site": "wttj",
                                        "job_url": job_url,
                                        "error": result.get("error"),
                                        "status": "failed"
                                    })
                            except Exception as e:
                                logger.error(f"❌ Application failed: {e}")
                                results["applications_failed"] += 1
                        
                        await context.close()
                    except Exception as e:
                        logger.error(f"❌ WTTJ applications failed: {e}")
                
                # Apply to SNCF jobs
                if "sncf" in job_urls:
                    try:
                        logger.info("🔄 Applying to SNCF jobs...")
                        context = await browser.new_context()
                        page = await context.new_page()
                        
                        for job_url in job_urls["sncf"][:5]:  # Limit to 5 jobs
                            try:
                                result = await self.orchestrator.sncf.apply_to_job(page, job_url, user)
                                
                                if result.get("success"):
                                    results["applications_submitted"] += 1
                                    results["applications"].append({
                                        "site": "sncf",
                                        "job_url": job_url,
                                        "job_title": result.get("job_title"),
                                        "status": "submitted"
                                    })
                                    self._save_application(user_id, "sncf", job_url, result.get("job_title"), "submitted")
                                else:
                                    results["applications_failed"] += 1
                                    results["applications"].append({
                                        "site": "sncf",
                                        "job_url": job_url,
                                        "error": result.get("error"),
                                        "status": "failed"
                                    })
                            except Exception as e:
                                logger.error(f"❌ Application failed: {e}")
                                results["applications_failed"] += 1
                        
                        await context.close()
                    except Exception as e:
                        logger.error(f"❌ SNCF applications failed: {e}")
                
                await browser.close()
            
            # Save tracking info
            self._save_automation_tracking(
                user_id,
                results["applications_submitted"],
                results["applications_submitted"] + results["applications_failed"],
                results["applications_submitted"] / max(results["applications_submitted"] + results["applications_failed"], 1)
            )
            
        except Exception as e:
            logger.error(f"❌ Job applications workflow failed: {e}")
            results["error"] = str(e)
        
        return results
    
    def _save_account_creation(self, user_id: str, site: str, email: str, status: str, error: Optional[str] = None):
        """Save account creation to database"""
        try:
            import sqlite3
            conn = sqlite3.connect(AUTOMATION_DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO automation_accounts 
                (user_id, site_name, email, account_created, status, error_message)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
            ''', (user_id, site, email, status, error))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Failed to save account creation: {e}")
    
    def _save_profile_setup(self, user_id: str, site: str, status: str, error: Optional[str] = None):
        """Save profile setup to database"""
        try:
            import sqlite3
            conn = sqlite3.connect(AUTOMATION_DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE automation_accounts 
                SET profile_setup = CURRENT_TIMESTAMP, status = ?, error_message = ?
                WHERE user_id = ? AND site_name = ?
            ''', (status, error, user_id, site))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Failed to save profile setup: {e}")
    
    def _save_application(self, user_id: str, site: str, job_url: str, job_title: str, status: str):
        """Save job application to database"""
        try:
            import sqlite3
            conn = sqlite3.connect(AUTOMATION_DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO automation_applications 
                (user_id, site_name, job_id, job_title, company, job_url, applied_at, status)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            ''', (user_id, site, job_url, job_title, site, job_url, status))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Failed to save application: {e}")
    
    def _save_automation_tracking(self, user_id: str, successful: int, total: int, success_rate: float):
        """Save automation tracking to database"""
        try:
            import sqlite3
            conn = sqlite3.connect(AUTOMATION_DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO automation_tracking 
                (user_id, total_applications, successful_applications, success_rate, started_at, completed_at)
                VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
            ''', (user_id, total, successful, success_rate))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Saved automation tracking: {successful}/{total} successful")
        except Exception as e:
            logger.error(f"❌ Failed to save automation tracking: {e}")
    
    def get_automation_status(self, user_id: str) -> Dict:
        """Get automation status for user"""
        try:
            import sqlite3
            conn = sqlite3.connect(AUTOMATION_DB_PATH)
            cursor = conn.cursor()
            
            # Get accounts
            cursor.execute('SELECT site_name, status FROM automation_accounts WHERE user_id = ?', (user_id,))
            accounts = cursor.fetchall()
            
            # Get applications
            cursor.execute('SELECT site_name, job_title, status FROM automation_applications WHERE user_id = ?', (user_id,))
            applications = cursor.fetchall()
            
            # Get tracking
            cursor.execute('SELECT total_applications, successful_applications, success_rate FROM automation_tracking WHERE user_id = ? ORDER BY completed_at DESC LIMIT 1', (user_id,))
            tracking = cursor.fetchone()
            
            conn.close()
            
            return {
                "user_id": user_id,
                "accounts": [{"site": acc[0], "status": acc[1]} for acc in accounts],
                "total_applications": applications.__len__(),
                "applications": [{"site": app[0], "job_title": app[1], "status": app[2]} for app in applications],
                "success_rate": tracking[2] if tracking else 0
            }
        except Exception as e:
            logger.error(f"❌ Failed to get automation status: {e}")
            return {"error": str(e)}


# Create global service instance
automation_service = OllamaAutomationService()
