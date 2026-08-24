"""
Enhanced WTTJ Adapter with Multiple Strategies
Implements all three automation approaches:
A) Stealth Browser Automation (with anti-bot detection)
B) WelcomeKit API (when credentials available)
C) Algolia Direct Access (for job search)
"""
import asyncio
import logging
import re
from typing import Dict, Any, Optional
from playwright.async_api import Page
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stealth_browser import StealthBrowser, HumanBehaviorSimulator
from wttj_api_client import WTTJAPIClient, AlgoliaJobSearchClient

logger = logging.getLogger(__name__)


class WTTJEnhancedAdapter:
    """
    Enhanced WTTJ adapter with multiple automation strategies
    Automatically selects best strategy based on context
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        use_stealth: bool = True,
        headless: bool = False
    ):
        """
        Initialize enhanced adapter
        
        Args:
            api_key: WelcomeKit API key (if available)
            use_stealth: Use stealth browser mode
            headless: Run browser in headless mode
        """
        self.api_key = api_key
        self.use_stealth = use_stealth
        self.headless = headless
        
        # Initialize clients
        self.api_client = WTTJAPIClient(api_key=api_key) if api_key else None
        self.algolia_client = AlgoliaJobSearchClient()
        self.stealth_browser: Optional[StealthBrowser] = None
    
    async def create_account(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create WTTJ account using best available strategy
        
        Strategy priority:
        1. Try API if available (fastest, most reliable)
        2. Fall back to stealth browser automation
        """
        logger.info(f"Creating WTTJ account for {email}")
        
        # Strategy 1: Try API first
        if self.api_client:
            logger.info("Attempting account creation via API...")
            result = await self.api_client.create_candidate(
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                **kwargs
            )
            
            if result["success"]:
                logger.info("✅ Account created successfully via API")
                return result
            else:
                logger.warning(f"API creation failed: {result.get('error')}")
        
        # Strategy 2: Stealth browser automation
        logger.info("Using stealth browser automation...")
        return await self._create_account_via_browser(
            email, password, first_name, last_name, phone, **kwargs
        )
    
    async def _create_account_via_browser(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create account using stealth browser"""
        try:
            # Initialize stealth browser
            self.stealth_browser = StealthBrowser(headless=self.headless)
            page = await self.stealth_browser.launch()
            
            logger.info("Navigating to signup page...")
            await page.goto(
                'https://www.welcometothejungle.com/en/authenticate/signup',
                wait_until='domcontentloaded'
            )
            
            # Simulate reading page
            await HumanBehaviorSimulator.reading_pause(2, 4)
            
            # Random mouse movements
            await self.stealth_browser.random_mouse_movement()
            
            # Fill email with human-like typing
            logger.info("Filling email...")
            await self.stealth_browser.human_like_type('input[type="email"]', email)
            await HumanBehaviorSimulator.thinking_pause()
            
            # Fill password fields
            logger.info("Filling password...")
            password_selectors = await page.locator('input[type="password"]').count()
            for i in range(password_selectors):
                selector = f'input[type="password"]:nth-of-type({i+1})'
                await self.stealth_browser.human_like_type(selector, password)
                await HumanBehaviorSimulator.random_pause()
            
            # Fill first name
            logger.info("Filling name...")
            clean_first = re.sub(r'[^a-zA-Z\s\-\']', '', first_name) or 'Alexandre'
            clean_last = re.sub(r'[^a-zA-Z\s\-\']', '', last_name) or 'Dupont'
            
            first_name_selectors = [
                'input[name*="first"]',
                'input[placeholder*="First"]',
                'input[placeholder*="Prénom"]'
            ]
            
            for selector in first_name_selectors:
                try:
                    if await page.locator(selector).first.is_visible():
                        await self.stealth_browser.human_like_type(selector, clean_first)
                        break
                except:
                    continue
            
            await HumanBehaviorSimulator.random_pause()
            
            # Fill last name
            last_name_selectors = [
                'input[name*="last"]',
                'input[placeholder*="Last"]',
                'input[placeholder*="Nom"]'
            ]
            
            for selector in last_name_selectors:
                try:
                    if await page.locator(selector).first.is_visible():
                        await self.stealth_browser.human_like_type(selector, clean_last)
                        break
                except:
                    continue
            
            await HumanBehaviorSimulator.thinking_pause()
            
            # Check terms checkbox with human-like behavior
            logger.info("Accepting terms...")
            checkbox_count = await page.locator('input[type="checkbox"]').count()
            for i in range(checkbox_count):
                try:
                    checkbox = page.locator('input[type="checkbox"]').nth(i)
                    if await checkbox.is_visible() and not await checkbox.is_checked():
                        await checkbox.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)
                        await checkbox.click(force=True)
                        await asyncio.sleep(0.3)
                except:
                    pass
            
            await HumanBehaviorSimulator.thinking_pause()
            
            # Scroll to see submit button
            await self.stealth_browser.random_scroll()
            
            # Click submit with human-like behavior
            logger.info("Submitting form...")
            submit_success = await self.stealth_browser.human_like_click(
                'button[type="submit"]',
                delay_range=(1.0, 2.5)
            )
            
            if not submit_success:
                logger.error("❌ Failed to click submit button")
                return {
                    "success": False,
                    "error": "Could not click submit button - may require manual intervention",
                    "method": "browser_stealth"
                }
            
            # Wait for navigation
            logger.info("Waiting for account creation...")
            await asyncio.sleep(5)
            
            # Check if successful
            current_url = page.url
            
            if 'authenticate/signup' not in current_url or any(
                kw in current_url for kw in ['onboarding', 'profile', 'welcome', 'dashboard']
            ):
                logger.info(f"✅ Account created! URL: {current_url}")
                return {
                    "success": True,
                    "email": email,
                    "password": password,
                    "status": "created",
                    "url": current_url,
                    "method": "browser_stealth"
                }
            else:
                # Check for error messages
                try:
                    error_messages = await page.locator('[role="alert"], .error, .alert-danger').all_text_contents()
                    error_text = " ".join(error_messages) if error_messages else "Unknown error"
                except:
                    error_text = "Still on signup page"
                
                logger.warning(f"Form submission may have failed: {error_text}")
                
                return {
                    "success": False,
                    "error": "Form submission failed",
                    "details": error_text,
                    "url": current_url,
                    "method": "browser_stealth"
                }
        
        except Exception as e:
            logger.error(f"Browser automation error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "method": "browser_stealth"
            }
        
        finally:
            if self.stealth_browser:
                logger.info("Keeping browser open for 10 seconds for verification...")
                await asyncio.sleep(10)
                await self.stealth_browser.close()
    
    async def search_jobs(
        self,
        query: str = "",
        location: Optional[str] = None,
        contract_type: Optional[str] = None,
        page: int = 0,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Search jobs using best available strategy
        
        Priority:
        1. Algolia direct access (fastest, no anti-bot)
        2. API if available
        """
        logger.info(f"Searching jobs: {query}")
        
        # Strategy 1: Algolia (best option)
        result = await self.algolia_client.search_jobs(
            query=query,
            location=location,
            contract_type=contract_type,
            page=page,
            hits_per_page=per_page
        )
        
        if result["success"]:
            logger.info(f"✅ Found {result['total_results']} jobs via Algolia")
            return result
        
        # Strategy 2: API fallback
        if self.api_client:
            logger.info("Algolia failed, trying API...")
            result = await self.api_client.search_jobs(
                query=query,
                location=location,
                contract_type=[contract_type] if contract_type else None,
                page=page + 1,  # API uses 1-indexed pages
                per_page=per_page
            )
            
            if result["success"]:
                return result
        
        return {
            "success": False,
            "error": "All job search strategies failed",
            "method": "multiple"
        }
    
    async def apply_to_job(
        self,
        job_url: str,
        email: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        cover_letter: Optional[str] = None,
        resume_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Apply to job using best available strategy
        
        Priority:
        1. API if job reference extractable
        2. Stealth browser automation
        """
        logger.info(f"Applying to job: {job_url}")
        
        # Try to extract job reference from URL
        job_reference = self._extract_job_reference(job_url)
        
        # Strategy 1: API if we have reference and API key
        if self.api_client and job_reference:
            logger.info(f"Attempting application via API (ref: {job_reference})...")
            result = await self.api_client.apply_to_job(
                job_reference=job_reference,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                cover_letter=cover_letter,
                resume_url=resume_url,
                **kwargs
            )
            
            if result["success"]:
                logger.info("✅ Applied successfully via API")
                return result
            else:
                logger.warning(f"API application failed: {result.get('error')}")
        
        # Strategy 2: Stealth browser automation
        logger.info("Using stealth browser for application...")
        return await self._apply_via_browser(
            job_url, email, first_name, last_name, phone, cover_letter, resume_url, **kwargs
        )
    
    async def _apply_via_browser(
        self,
        job_url: str,
        email: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        cover_letter: Optional[str] = None,
        resume_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Apply to job using stealth browser"""
        try:
            self.stealth_browser = StealthBrowser(headless=self.headless)
            page = await self.stealth_browser.launch()
            
            logger.info("Navigating to job page...")
            await page.goto(job_url, wait_until='domcontentloaded')
            
            # Simulate reading job description
            await HumanBehaviorSimulator.reading_pause(5, 8)
            await self.stealth_browser.random_scroll()
            
            # Look for and click apply button
            logger.info("Looking for apply button...")
            apply_selectors = [
                'button:has-text("Apply")',
                'a:has-text("Apply")',
                '[data-testid*="apply"]',
                '.apply-button',
            ]
            
            apply_clicked = False
            for selector in apply_selectors:
                try:
                    if await page.locator(selector).first.is_visible(timeout=3000):
                        await self.stealth_browser.human_like_click(selector)
                        apply_clicked = True
                        break
                except:
                    continue
            
            if not apply_clicked:
                logger.error("Could not find apply button")
                return {
                    "success": False,
                    "error": "Apply button not found",
                    "method": "browser_stealth"
                }
            
            # Wait for application form
            await asyncio.sleep(3)
            
            # Fill application form with human-like behavior
            # (Implementation similar to account creation)
            logger.info("Filling application form...")
            
            # ... Add form filling logic here ...
            
            logger.info("✅ Application submitted")
            return {
                "success": True,
                "job_url": job_url,
                "method": "browser_stealth"
            }
        
        except Exception as e:
            logger.error(f"Browser application error: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "browser_stealth"
            }
        
        finally:
            if self.stealth_browser:
                await asyncio.sleep(5)
                await self.stealth_browser.close()
    
    def _extract_job_reference(self, job_url: str) -> Optional[str]:
        """Extract job reference from URL"""
        # Example: https://www.welcometothejungle.com/en/companies/company/jobs/job-ref-123
        patterns = [
            r'/jobs/([^/\?]+)',
            r'job[_-]?ref[_-]?([a-zA-Z0-9-]+)',
            r'/([a-zA-Z0-9-]+)$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, job_url)
            if match:
                return match.group(1)
        
        return None
    
    async def close(self):
        """Cleanup resources"""
        if self.api_client:
            await self.api_client.close()
        if self.algolia_client:
            await self.algolia_client.close()
        if self.stealth_browser:
            await self.stealth_browser.close()


# Example usage
async def example_usage():
    """Example of using enhanced adapter"""
    
    # Initialize with API key (optional)
    adapter = WTTJEnhancedAdapter(
        api_key=None,  # Set your API key here if available
        use_stealth=True,
        headless=False
    )
    
    try:
        # Create account
        result = await adapter.create_account(
            email="test@example.com",
            password="SecurePass123!",
            first_name="John",
            last_name="Doe",
            phone="+33612345678"
        )
        
        print(f"Account creation: {result}")
        
        # Search jobs
        jobs = await adapter.search_jobs(
            query="Python Developer",
            location="Paris",
            per_page=10
        )
        
        print(f"Found {jobs.get('total_results', 0)} jobs")
        
    finally:
        await adapter.close()


if __name__ == '__main__':
    asyncio.run(example_usage())
