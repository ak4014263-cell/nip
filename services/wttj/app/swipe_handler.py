"""
Swipe Event Handler - Triggers Automation When User Swipes Right on a Job
NO AI - Uses direct field mapping with saved credentials
"""
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SwipeAutomationHandler:
    """Handles swipe events and triggers the Firefox automation workflow"""
    
    def __init__(self):
        self.active_applications = {}  # Track ongoing applications
    
    async def handle_swipe_right(
        self,
        user_id: str,
        job_id: str,
        job_url: str,
        db_session
    ) -> Dict[str, Any]:
        """
        Handle user swiping right (liking) a job
        1. Retrieve user's saved WTTJ credentials
        2. Retrieve user's profile data
        3. Trigger Firefox automation to login and apply
        
        Args:
            user_id: User/candidate ID
            job_id: Job ID from database
            job_url: WTTJ job URL
            db_session: Database session
            
        Returns:
            Dict with success status and application details
        """
        try:
            logger.info(f"🎯 Swipe RIGHT detected: User {user_id} → Job {job_url}")
            
            # Import models
            from shared.models import Credential, UserProfile, UserPreferences, Application, Job
            
            # 1. Get saved credentials
            credential = db_session.query(Credential).filter(
                Credential.candidate_id == user_id,
                Credential.careerSite == "WTTJ"
            ).first()
            
            if not credential:
                return {
                    "success": False,
                    "error": "No WTTJ credentials found",
                    "message": "Please connect your WTTJ account first",
                    "action_required": "connect_wttj_account"
                }
            
            if not credential.isVerified:
                return {
                    "success": False,
                    "error": "WTTJ credentials not verified",
                    "message": "Please verify your WTTJ account credentials",
                    "action_required": "verify_wttj_account"
                }
            
            email = credential.email
            password = credential.password
            
            logger.info(f"✅ Found verified credentials for {email}")
            
            # 2. Get user profile data
            profile = db_session.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if not profile:
                # Create basic profile if doesn't exist
                profile = UserProfile(
                    user_id=user_id,
                    first_name="Candidate",
                    last_name="User",
                    phone="+33 6 12 34 56 78",
                    current_location="Paris, France",
                    current_title="Software Engineer",
                    profile_completion_percentage=50
                )
                db_session.add(profile)
                db_session.commit()
                db_session.refresh(profile)
            
            # 3. Get user preferences (optional)
            preferences = db_session.query(UserPreferences).filter(
                UserPreferences.user_id == user_id
            ).first()
            
            # 4. Build profile data dictionary for form filling
            profile_data = {
                "first_name": profile.first_name or "Candidate",
                "last_name": profile.last_name or "User",
                "phone": profile.phone or "+33 6 12 34 56 78",
                "current_location": profile.current_location or "Paris, France",
                "location": profile.current_location or "Paris, France",
                "current_title": profile.current_title or "Software Engineer",
                "title": profile.current_title or "Software Engineer",
                "linkedin_url": profile.linkedin_url or "",
                "github_url": profile.github_url or "",
                "portfolio_url": profile.portfolio_url or "",
                "availability": profile.availability or "Immediately",
                "bio": profile.bio or "",
                "summary": profile.summary or "",
                "cover_letter_template": profile.cover_letter_template if hasattr(profile, 'cover_letter_template') else None,
                "resume_path": profile.resume_path or "",
                "skills": profile.skills or [],
                "email": email
            }
            
            logger.info(f"📋 Profile data prepared: {profile_data.get('first_name')} {profile_data.get('last_name')}")
            
            # 5. Create application record (status: pending)
            application = Application(
                candidate_id=user_id,
                job_id=job_id,
                status="pending",
                applied_at=datetime.utcnow()
            )
            db_session.add(application)
            db_session.commit()
            db_session.refresh(application)
            
            application_id = application.id
            logger.info(f"📝 Created application record: {application_id}")
            
            # 6. Trigger Firefox automation (NO AI - Direct field mapping)
            try:
                from services.wttj.app.wttj_firefox_applier import WTTJFirefoxApplier
            except ImportError:
                from wttj_firefox_applier import WTTJFirefoxApplier
            
            applier = WTTJFirefoxApplier()
            
            # Run automation in visible browser (headless=False)
            logger.info(f"🚀 Starting Firefox automation for {email}...")
            
            automation_result = await applier.apply_to_job(
                email=email,
                password=password,
                job_url=job_url,
                profile_data=profile_data,
                headless=False  # Visible browser so user can see the magic!
            )
            
            # 7. Update application status based on result
            if automation_result.get("success"):
                application.status = "submitted"
                logger.info(f"✅ Application submitted successfully!")
            else:
                application.status = "failed"
                logger.error(f"❌ Application failed: {automation_result.get('message')}")
            
            db_session.commit()
            
            return {
                "success": automation_result.get("success", False),
                "message": automation_result.get("message", "Application processed"),
                "application_id": application_id,
                "job_url": job_url,
                "email": email,
                "fields_filled": automation_result.get("fields_filled", 0),
                "automation_method": "Firefox (No AI - Direct Field Mapping)",
                "status": application.status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error handling swipe automation: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process application",
                "job_url": job_url
            }
    
    async def handle_swipe_left(
        self,
        user_id: str,
        job_id: str,
        db_session
    ) -> Dict[str, Any]:
        """
        Handle user swiping left (passing) on a job
        Just records the pass, no automation needed
        
        Args:
            user_id: User/candidate ID
            job_id: Job ID from database
            db_session: Database session
            
        Returns:
            Dict with success status
        """
        try:
            from shared.models import Swipe
            
            # Record the pass
            swipe = Swipe(
                candidate_id=user_id,
                job_id=job_id,
                liked=False,
                timestamp=datetime.utcnow()
            )
            db_session.add(swipe)
            db_session.commit()
            
            logger.info(f"👈 Swipe LEFT recorded: User {user_id} passed on job {job_id}")
            
            return {
                "success": True,
                "action": "passed",
                "message": "Job passed successfully",
                "job_id": job_id
            }
            
        except Exception as e:
            logger.error(f"Error recording swipe left: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to record pass"
            }


# Global handler instance
swipe_handler = SwipeAutomationHandler()
