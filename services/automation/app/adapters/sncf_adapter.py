"""SNCF Careers Adapter"""
from playwright.async_api import Page
import logging

logger = logging.getLogger(__name__)


class SNCFAdapter:
    """Adapter for SNCF Careers"""
    
    def __init__(self, base_url: str = "https://www.sncf.com/fr/carrieres"):
        self.base_url = base_url
        self.name = "SNCF"
    
    async def create_account(
        self,
        page: Page,
        email: str,
        password: str,
        candidate_data: dict
    ) -> dict:
        """Create an account on SNCF Careers"""
        try:
            logger.info(f"Creating SNCF account for {email}")
            
            await page.goto(f"{self.base_url}/register")
            await page.wait_for_load_state('networkidle')
            
            # Fill registration form
            await page.fill('#email', email)
            await page.fill('#password', password)
            await page.fill('#confirm-password', password)
            
            if candidate_data.get('first_name'):
                await page.fill('#firstName', candidate_data['first_name'])
            
            if candidate_data.get('last_name'):
                await page.fill('#lastName', candidate_data['last_name'])
            
            if candidate_data.get('phone'):
                await page.fill('#phone', candidate_data['phone'])
            
            # Accept terms
            terms_selector = 'input[type="checkbox"][id*="terms"], input[type="checkbox"][id*="cgu"]'
            if await page.locator(terms_selector).count() > 0:
                await page.check(terms_selector)
            
            await page.screenshot(path=f"screenshots/sncf_before_submit.png")
            
            # Submit
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            await page.screenshot(path=f"screenshots/sncf_after_submit.png")
            
            return {
                "success": True,
                "message": "SNCF account created successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to create SNCF account: {e}")
            await page.screenshot(path=f"screenshots/sncf_error.png")
            return {"success": False, "error": str(e)}
    
    async def login(self, page: Page, email: str, password: str) -> bool:
        """Login to SNCF Careers"""
        try:
            await page.goto(f"{self.base_url}/login")
            await page.fill('#email', email)
            await page.fill('#password', password)
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            return True
        except Exception as e:
            logger.error(f"SNCF login failed: {e}")
            return False
    
    async def apply_to_job(
        self,
        page: Page,
        job_url: str,
        application_data: dict
    ) -> dict:
        """Apply to a job on SNCF Careers"""
        try:
            logger.info(f"Applying to SNCF job: {job_url}")
            
            await page.goto(job_url)
            await page.click('button:has-text("Postuler"), button:has-text("Apply")')
            await page.wait_for_timeout(2000)
            
            # Upload resume
            if application_data.get('resume_path'):
                file_input = page.locator('input[type="file"]').first
                await file_input.set_input_files(application_data['resume_path'])
            
            # Cover letter
            if application_data.get('cover_letter'):
                cover_letter = page.locator('textarea[name*="lettre"], textarea[name*="cover"]')
                if await cover_letter.count() > 0:
                    await cover_letter.fill(application_data['cover_letter'])
            
            await page.screenshot(path=f"screenshots/sncf_application_filled.png")
            
            # Submit
            await page.click('button:has-text("Envoyer"), button:has-text("Submit")')
            await page.wait_for_load_state('networkidle')
            
            await page.screenshot(path=f"screenshots/sncf_application_submitted.png")
            
            return {"success": True, "message": "Application submitted"}
            
        except Exception as e:
            logger.error(f"SNCF application failed: {e}")
            await page.screenshot(path=f"screenshots/sncf_application_error.png")
            return {"success": False, "error": str(e)}
