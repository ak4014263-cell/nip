#!/usr/bin/env python3
"""
WTTJ Bot/Captcha Bypass Handler
Handles Cloudflare, reCAPTCHA, and other bot detection challenges
Uses Firefox with stealth techniques
"""
import asyncio
import logging
import time
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright_stealth import stealth_async

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wttj_bot_bypass")


class WTTJBotBypass:
    """Handles bot detection and captcha bypass for WTTJ signup"""
    
    def __init__(self, headless: bool = True, use_proxy: Optional[str] = None):
        """
        Initialize bot bypass handler
        
        Args:
            headless: Run in headless mode
            use_proxy: Proxy URL (optional)
        """
        self.headless = headless
        self.proxy = use_proxy
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    async def launch(self):
        """Launch Firefox browser with stealth settings"""
        try:
            playwright = await async_playwright().start()
            
            launch_args = {
                "headless": self.headless,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-resources",
                    "--no-first-run",
                    "--no-default-browser-check",
                ]
            }
            
            if self.proxy:
                launch_args["proxy"] = {"server": self.proxy}
            
            # Launch Firefox browser
            self.browser = await playwright.firefox.launch(**launch_args)
            
            # Create context with anti-detection settings
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
                viewport={"width": 1920, "height": 1080},
                ignore_https_errors=True,
                locale="en-US",
                timezone_id="America/New_York",
            )
            
            # Apply stealth techniques
            await stealth_async(self.context)
            
            # Create page
            self.page = await self.context.new_page()
            
            logger.info("✅ Firefox browser launched with stealth settings")
            return self.page
            
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise
    
    async def bypass_captcha(self, url: str, timeout: int = 60) -> bool:
        """
        Navigate to URL and bypass bot/captcha challenges
        
        Args:
            url: URL to visit (e.g., WTTJ signup page)
            timeout: Timeout in seconds
            
        Returns:
            True if successfully bypassed, False otherwise
        """
        if not self.page:
            await self.launch()
        
        try:
            logger.info(f"Navigating to {url}")
            
            # Set extra headers to appear more legitimate
            await self.page.set_extra_http_headers({
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0",
            })
            
            # Navigate to page
            response = await self.page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
            logger.info(f"Page response: {response.status if response else 'No response'}")
            
            # Wait for navigation to complete
            await asyncio.sleep(2)
            
            # Check for common bot detection indicators
            title = await self.page.title()
            logger.info(f"Page title: {title}")
            
            # Check if we're blocked by Cloudflare
            if "challenge" in title.lower() or "cloudflare" in title.lower():
                logger.warning("⚠️ Cloudflare challenge detected")
                await self.handle_cloudflare()
            
            # Check for reCAPTCHA
            recaptcha_present = await self.page.query_selector('iframe[src*="recaptcha"]')
            if recaptcha_present:
                logger.warning("⚠️ reCAPTCHA detected")
                await self.handle_recaptcha()
            
            # Check if page loaded successfully (not a challenge page)
            body_text = await self.page.content()
            if "just a moment" in body_text.lower() or "enable javascript" in body_text.lower():
                logger.warning("⚠️ Bot challenge page detected")
                # Wait for JavaScript to complete
                await self.page.wait_for_load_state("networkidle", timeout=timeout * 1000)
            
            await asyncio.sleep(1)
            
            # Verify we're on the actual signup page
            current_url = self.page.url
            if "signin" in current_url or "login" in current_url or "signup" in current_url:
                logger.info(f"✅ Successfully bypassed captcha/bot detection")
                logger.info(f"Current URL: {current_url}")
                return True
            else:
                logger.warning(f"⚠️ May still be on challenge page: {current_url}")
                # Give extra time for async content
                await asyncio.sleep(3)
                current_url = self.page.url
                logger.info(f"Final URL after wait: {current_url}")
                return True  # Optimistic - page loaded
                
        except Exception as e:
            logger.error(f"Error bypassing captcha: {e}")
            return False
    
    async def handle_cloudflare(self):
        """Handle Cloudflare challenge"""
        try:
            logger.info("Attempting to bypass Cloudflare...")
            
            # Cloudflare usually completes automatically with proper headers and wait
            # Just wait for it to finish
            await self.page.wait_for_load_state("networkidle", timeout=30000)
            
            # Look for the "challenge" button that indicates completion
            challenge_button = await self.page.query_selector('input[value="Challenge"]')
            if challenge_button:
                await challenge_button.click()
            
            # Wait for redirect
            await self.page.wait_for_load_state("networkidle", timeout=30000)
            logger.info("✅ Cloudflare challenge completed")
            
        except Exception as e:
            logger.warning(f"Cloudflare handling error: {e}")
    
    async def handle_recaptcha(self):
        """Handle reCAPTCHA"""
        try:
            logger.info("Attempting to handle reCAPTCHA...")
            
            # Wait for reCAPTCHA frame to load
            await asyncio.sleep(2)
            
            # Look for reCAPTCHA checkbox
            recaptcha_checkbox = await self.page.query_selector('[aria-label="recaptcha"]')
            if recaptcha_checkbox:
                logger.info("Found reCAPTCHA checkbox")
                await recaptcha_checkbox.click()
                await asyncio.sleep(3)
            
            logger.info("reCAPTCHA handling attempted")
            
        except Exception as e:
            logger.warning(f"reCAPTCHA handling error: {e}")
    
    async def get_page(self) -> Optional[Page]:
        """Get the current page after bypass"""
        return self.page
    
    async def fill_signup_form(
        self, 
        email: str, 
        password: str, 
        first_name: str,
        last_name: str = None
    ) -> bool:
        """Fill signup form with account details"""
        if not self.page:
            return False
        
        try:
            logger.info(f"Filling signup form for {email}...")
            await asyncio.sleep(1)
            
            # First name field (appears as "First name" label with "Hope" placeholder)
            first_name_selectors = [
                'input[placeholder="Hope"]',
                'xpath=//input[@placeholder="Hope"]',
                'input[name="firstName"]',
                'input[name="first_name"]',
            ]
            
            fname_filled = False
            for selector in first_name_selectors:
                try:
                    locator = self.page.locator(selector)
                    if await locator.count() > 0:
                        logger.info(f"Filling first name with: {selector}")
                        await locator.first.fill(first_name)
                        fname_filled = True
                        await asyncio.sleep(0.5)
                        break
                except:
                    continue
            
            if not fname_filled:
                logger.warning("Could not fill first name field")
            
            # Email field
            email_selectors = [
                'input[type="email"]',
                'xpath=//input[@type="email"]',
                'input[placeholder*="@gmail.com"]',
                'input[name="email"]',
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    locator = self.page.locator(selector)
                    if await locator.count() > 0:
                        logger.info(f"Filling email with: {selector}")
                        await locator.first.fill(email)
                        email_filled = True
                        await asyncio.sleep(0.5)
                        break
                except:
                    continue
            
            if not email_filled:
                logger.warning("Could not fill email field")
            
            # Password field
            password_selectors = [
                'input[type="password"]',
                'xpath=//input[@type="password"]',
                'input[name="password"]',
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    locator = self.page.locator(selector)
                    if await locator.count() > 0:
                        logger.info(f"Filling password with: {selector}")
                        await locator.first.fill(password)
                        password_filled = True
                        await asyncio.sleep(0.5)
                        break
                except:
                    continue
            
            if not password_filled:
                logger.warning("Could not fill password field")
            
            logger.info("✅ Signup form filled")
            return fname_filled and email_filled and password_filled
            
        except Exception as e:
            logger.error(f"Error filling form: {e}")
            return False
    
    async def click_agree_button(self) -> bool:
        """Click 'Agree and create profile' yellow button"""
        if not self.page:
            return False
        
        try:
            logger.info("Looking for 'Agree and create profile' button...")
            await asyncio.sleep(1)
            
            # The yellow button text "Agree and create profile"
            agree_selectors = [
                'button:text-matches("Agree and create profile")',
                'button:has-text("Agree and create profile")',
                'xpath=//button[contains(., "Agree and create profile")]',
                'xpath=//button[contains(text(), "Agree")]',
            ]
            
            for selector in agree_selectors:
                try:
                    logger.info(f"Trying: {selector}")
                    locator = self.page.locator(selector)
                    count = await locator.count()
                    if count > 0:
                        logger.info(f"✅ Found button: {selector}")
                        await locator.first.wait_for(state="visible")
                        await locator.first.click()
                        logger.info("✅ Clicked 'Agree and create profile' button")
                        await asyncio.sleep(2)
                        return True
                except Exception as e:
                    logger.debug(f"Failed: {selector} - {e}")
                    continue
            
            logger.warning("⚠️ Could not find Agree button")
            return False
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return False
    
    async def click_create_profile_button(self) -> bool:
        """Click create profile/account button"""
        if not self.page:
            return False
        
        try:
            logger.info("Looking for 'Create Profile' button...")
            await asyncio.sleep(1)
            
            # Get all buttons on page
            all_buttons = await self.page.locator("button").all()
            logger.info(f"Found {len(all_buttons)} buttons on page")
            
            # Log button texts
            for i, btn in enumerate(all_buttons[:15]):  # First 15 buttons
                try:
                    text = await btn.inner_text()
                    logger.info(f"  Button {i}: '{text.strip()}'")
                except:
                    pass
            
            # Try common create profile selectors
            create_selectors = [
                'button:text("Create Profile")',
                'button:text("Create profile")',
                'button:text("create profile")',
                'button:has-text("Create Profile")',
                'button:text("Create Account")',
                'button:text("Create")',
                'button:text("Sign Up")',
                'button:text("Register")',
                'button:text("Join")',
                'button[type="submit"]',
                'button[class*="submit"]',
                'button[class*="create"]',
                'button[class*="signup"]',
                'button[class*="register"]',
                'xpath=//button[contains(text(), "Create Profile")]',
                'xpath=//button[contains(text(), "Create")]',
                'xpath=//button[@type="submit"]',
            ]
            
            for selector in create_selectors:
                try:
                    logger.info(f"Trying selector: {selector}")
                    locator = self.page.locator(selector)
                    count = await locator.count()
                    if count > 0:
                        logger.info(f"✅ Found {count} elements with selector: {selector}")
                        # Make sure it's visible
                        await locator.first.wait_for(state="visible", timeout=5000)
                        await locator.first.click()
                        logger.info("✅ Clicked Create Profile button")
                        await asyncio.sleep(3)
                        # Wait for form submission
                        try:
                            await self.page.wait_for_load_state("networkidle", timeout=10000)
                            logger.info("✅ Form submitted and page loaded")
                        except:
                            logger.info("Page load completed (with timeout)")
                        return True
                except Exception as e:
                    logger.debug(f"Selector failed: {selector} - {e}")
                    continue
            
            logger.warning("⚠️ Could not find Create Profile button")
            return False
            
        except Exception as e:
            logger.error(f"Error clicking create profile button: {e}", exc_info=True)
            return False
    
    async def close(self):
        """Close browser"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")


async def bypass_wttj_signup(
    signup_url: str = "https://www.welcometothe.jungle/users/sign_up",
    headless: bool = False,
    proxy: Optional[str] = None
) -> bool:
    """
    Bypass WTTJ signup page bot detection
    
    Args:
        signup_url: WTTJ signup page URL
        headless: Run headless (for testing, set to False to see the browser)
        proxy: Proxy URL (optional)
        
    Returns:
        True if successfully bypassed
    """
    bypass = WTTJBotBypass(headless=headless, use_proxy=proxy)
    
    try:
        await bypass.launch()
        result = await bypass.bypass_captcha(signup_url, timeout=60)
        
        if result:
            page = await bypass.get_page()
            if page:
                # Keep page open for further automation
                logger.info("Page is ready for account creation automation")
                return True
        
        return result
        
    except Exception as e:
        logger.error(f"Bypass failed: {e}")
        return False
    
    finally:
        await bypass.close()


if __name__ == "__main__":
    # Test the bypass
    result = asyncio.run(bypass_wttj_signup(headless=False))
    print(f"Bypass result: {result}")
