#!/usr/bin/env python3
"""
WTTJ Bot/Captcha Bypass Handler
Handles Cloudflare, reCAPTCHA, and other bot detection challenges
Uses Firefox with stealth techniques
"""
import asyncio
import os
import logging
import time
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
# playwright-stealth v2.0.3 only has sync 'stealth'
# We'll apply stealth after page creation
try:
    from playwright_stealth import stealth_async
    USE_ASYNC_STEALTH = True
except (ImportError, AttributeError):
    # playwright_stealth v2 doesn't have stealth_async
    # We'll skip stealth for now or use manual techniques
    USE_ASYNC_STEALTH = False
    stealth_async = None

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
                # Parse proxy URL to separate credentials (Playwright needs them split)
                from urllib.parse import urlparse
                parsed = urlparse(self.proxy)
                if parsed.username or parsed.password:
                    # Rebuild server without credentials
                    scheme = parsed.scheme or "http"
                    server = f"{scheme}://{parsed.hostname}"
                    if parsed.port:
                        server += f":{parsed.port}"
                    launch_args["proxy"] = {
                        "server": server,
                        "username": parsed.username or "",
                        "password": parsed.password or "",
                    }
                    logger.info(f"🔗 Using proxy: {server} (with auth)")
                else:
                    launch_args["proxy"] = {"server": self.proxy}
                    logger.info(f"🔗 Using proxy: {self.proxy}")
            
            # Launch Firefox browser
            self.browser = await playwright.firefox.launch(**launch_args)
            
            # Create context with anti-detection settings.
            # Locale/timezone default to UK (matches en-GB signup + UK residential
            # proxy) for reCAPTCHA v3 geo-consistency. Override via env if needed.
            browser_locale = os.getenv("BROWSER_LOCALE", "en-GB")
            browser_tz = os.getenv("BROWSER_TIMEZONE", "Europe/London")
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
                viewport={"width": 1920, "height": 1080},
                ignore_https_errors=True,
                locale=browser_locale,
                timezone_id=browser_tz,
            )
            
            # Create page first
            self.page = await self.context.new_page()
            
            # Apply stealth techniques if available
            if USE_ASYNC_STEALTH and stealth_async:
                try:
                    await stealth_async(self.page)
                    logger.info("✅ Stealth techniques applied")
                except Exception as e:
                    logger.warning(f"⚠️ Could not apply stealth: {e}")
            
            logger.info("✅ Firefox browser launched with anti-detection settings")
            return self.page
            
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise
    
    async def accept_cookies(self) -> bool:
        """Accept cookie consent banner (Axeptio-based on WTTJ)"""
        if not self.page:
            return False
        
        try:
            logger.info("Looking for cookie consent banner...")
            await asyncio.sleep(2)
            
            # WTTJ uses Axeptio. The primary accept button says "OK for me".
            # We MUST NOT click "Agree" as that matches the form submit button.
            cookie_selectors = [
                # Axeptio-specific selectors (most reliable)
                'button:has-text("OK for me")',
                'button:has-text("OK pour moi")',
                'button.axeptio_btn_acceptAll',
                '[data-testid="axeptio-accept-all"]',
                'button[title*="OK for me" i]',
                # Generic accept
                'button:has-text("Accept all")',
                'button:has-text("Accept cookies")',
                'button:has-text("I accept")',
                'button[id*="accept" i]:not([id*="terms" i])',
                # Common consent frameworks
                '#onetrust-accept-btn-handler',
                '.cookie-accept',
                # DO NOT include generic "Agree" since it matches "Agree and create profile"
            ]
            
            for selector in cookie_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2500, state="visible")
                    if element:
                        # Extra safety: make sure this isn't the form submit
                        text = (await element.text_content() or "").strip().lower()
                        if "create profile" in text or "sign up" in text:
                            logger.info(f"Skipping form-related button: {text!r}")
                            continue
                        await element.click()
                        logger.info(f"✅ Accepted cookies via: {selector} (text={text!r})")
                        await asyncio.sleep(1.5)
                        # Verify banner disappeared
                        try:
                            banner_check = await self.page.locator('text="C is for COOKIE"').count()
                            if banner_check == 0:
                                logger.info("✅ Cookie banner confirmed dismissed")
                                return True
                            else:
                                logger.info("Cookie banner still visible, trying next selector")
                                continue
                        except:
                            return True
                except:
                    continue
            
            # JS fallback specifically targeting Axeptio button text
            js_result = await self.page.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    // Prefer "OK for me" / "OK pour moi" exact match
                    const okBtn = buttons.find(btn => {
                        const t = (btn.textContent || '').trim().toLowerCase();
                        return t === 'ok for me' || t === 'ok pour moi' || t === 'accept all';
                    });
                    if (okBtn) { okBtn.click(); return {ok: true, text: okBtn.textContent.trim()}; }
                    return {ok: false};
                }
            """)
            
            if js_result.get('ok'):
                logger.info(f"✅ Accepted cookies via JavaScript: {js_result.get('text')}")
                await asyncio.sleep(1.5)
                return True
            
            logger.info("No cookie banner found (may already be accepted)")
            return True
            
        except Exception as e:
            logger.warning(f"Cookie acceptance error (continuing anyway): {e}")
            return True  # Don't fail if no cookie banner
    
    async def solve_captcha_if_present(self) -> bool:
        """Detect and attempt to solve captcha"""
        if not self.page:
            return False
        
        try:
            logger.info("Checking for captcha...")
            await asyncio.sleep(2)
            
            # Check for reCAPTCHA
            recaptcha_frame = await self.page.query_selector('iframe[src*="recaptcha"]')
            if recaptcha_frame:
                logger.info("⚠️ reCAPTCHA detected - attempting to solve...")
                
                # Method 1: Try clicking the checkbox
                try:
                    # Switch to reCAPTCHA iframe
                    frames = self.page.frames
                    recaptcha_checkbox_frame = None
                    
                    for frame in frames:
                        if 'recaptcha' in frame.url and 'anchor' in frame.url:
                            recaptcha_checkbox_frame = frame
                            break
                    
                    if recaptcha_checkbox_frame:
                        logger.info("Found reCAPTCHA checkbox frame")
                        checkbox = await recaptcha_checkbox_frame.wait_for_selector('.recaptcha-checkbox-border', timeout=5000)
                        if checkbox:
                            await checkbox.click()
                            logger.info("✅ Clicked reCAPTCHA checkbox")
                            await asyncio.sleep(3)
                            
                            # Check if solved
                            is_checked = await recaptcha_checkbox_frame.query_selector('.recaptcha-checkbox-checked')
                            if is_checked:
                                logger.info("✅ reCAPTCHA solved automatically!")
                                return True
                except Exception as e:
                    logger.warning(f"reCAPTCHA checkbox click failed: {e}")
                
                # Method 2: Wait for manual solve or timeout
                logger.warning("⚠️ reCAPTCHA may require manual solving - waiting 30 seconds...")
                await asyncio.sleep(30)
                
                # Check if still present
                still_present = await self.page.query_selector('iframe[src*="recaptcha"]')
                if not still_present:
                    logger.info("✅ reCAPTCHA solved (disappeared)")
                    return True
                else:
                    logger.warning("⚠️ reCAPTCHA still present - continuing anyway")
                    return False
            
            # Check for hCaptcha
            hcaptcha_frame = await self.page.query_selector('iframe[src*="hcaptcha"]')
            if hcaptcha_frame:
                logger.warning("⚠️ hCaptcha detected - waiting for manual solve (30s)...")
                await asyncio.sleep(30)
                return True
            
            # Check for Cloudflare turnstile
            turnstile = await self.page.query_selector('[name="cf-turnstile-response"]')
            if turnstile:
                logger.warning("⚠️ Cloudflare Turnstile detected - waiting...")
                await asyncio.sleep(10)
                return True
            
            logger.info("✅ No captcha detected")
            return True
            
        except Exception as e:
            logger.error(f"Captcha detection error: {e}")
            return True  # Continue anyway
    
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
            
            # Step 1: Accept cookies
            await self.accept_cookies()
            
            # Step 2: Solve captcha if present
            await self.solve_captcha_if_present()
            
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
            await asyncio.sleep(2)
            
            # Debug: capture all input fields info for diagnostics
            try:
                inputs_info = await self.page.evaluate("""() => {
                    const inputs = Array.from(document.querySelectorAll('input'));
                    return inputs.map(i => ({
                        type: i.type,
                        name: i.name,
                        id: i.id,
                        placeholder: i.placeholder,
                        ariaLabel: i.getAttribute('aria-label'),
                        dataTestId: i.getAttribute('data-testid'),
                        autocomplete: i.autocomplete
                    }));
                }""")
                logger.info(f"[DEBUG] Found {len(inputs_info)} input fields on page:")
                for idx, info in enumerate(inputs_info):
                    logger.info(f"  [{idx}] {info}")
            except Exception as e:
                logger.warning(f"Could not enumerate inputs: {e}")
            
            # First name field - comprehensive selector list
            first_name_selectors = [
                # Autocomplete attribute (most reliable)
                'input[autocomplete="given-name"]',
                # Data-testid patterns
                'input[data-testid*="first"i]',
                'input[data-testid*="firstname"i]',
                # Name attribute variations
                'input[name="firstName"]',
                'input[name="first_name"]',
                'input[name="firstname"]',
                'input[name="prenom"]',
                # ID variations
                'input#firstName',
                'input#first_name',
                'input#firstname',
                # Placeholder patterns (English + French)
                'input[placeholder="Hope"]',
                'input[placeholder*="First name" i]',
                'input[placeholder*="first-name" i]',
                'input[placeholder*="Prénom" i]',
                'input[placeholder*="Prenom" i]',
                # Aria label
                'input[aria-label*="First name" i]',
                'input[aria-label*="Prénom" i]',
                # Label-based (parent has label with "First name")
                'label:has-text("First name") input',
                'label:has-text("Prénom") input',
                # XPath fallback: input following a label containing First name
                'xpath=//label[contains(., "First name")]//input',
                'xpath=//label[contains(., "Prénom")]//input',
                'xpath=//input[@placeholder="Hope"]',
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
                except Exception as sel_ex:
                    continue
            
            # Fallback: pick the first text input that isn't email/password
            if not fname_filled:
                try:
                    logger.info("Trying fallback: first non-email/password text input")
                    fallback_result = await self.page.evaluate("""(name) => {
                        const inputs = Array.from(document.querySelectorAll('input'));
                        for (const i of inputs) {
                            const t = (i.type || '').toLowerCase();
                            if (t === 'text' || t === '' || t === 'search') {
                                if (i.name?.toLowerCase().includes('last')) continue;
                                if (i.placeholder?.toLowerCase().includes('last')) continue;
                                i.focus();
                                const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                                setter.call(i, name);
                                i.dispatchEvent(new Event('input', {bubbles: true}));
                                i.dispatchEvent(new Event('change', {bubbles: true}));
                                return {ok: true, selector: i.name || i.id || i.placeholder};
                            }
                        }
                        return {ok: false};
                    }""", first_name)
                    if fallback_result.get('ok'):
                        logger.info(f"✅ First name filled via JS fallback: {fallback_result.get('selector')}")
                        fname_filled = True
                    else:
                        logger.warning("Could not fill first name field (no text input found)")
                except Exception as e:
                    logger.warning(f"Fallback also failed: {e}")
            
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
        """Click 'Agree and create profile' yellow button with human-like behavior"""
        if not self.page:
            return False
        
        try:
            logger.info("Looking for 'Agree and create profile' button...")
            
            # Human-like pause before finding button (helps reCAPTCHA v3 score)
            await asyncio.sleep(2.5)
            
            # Simulate some mouse movement first (helps with reCAPTCHA v3)
            try:
                import random
                for _ in range(3):
                    x = random.randint(400, 1400)
                    y = random.randint(200, 700)
                    await self.page.mouse.move(x, y, steps=random.randint(5, 15))
                    await asyncio.sleep(random.uniform(0.15, 0.4))
            except Exception as mm_ex:
                logger.debug(f"Mouse movement simulation skipped: {mm_ex}")
            
            # Method 1: Try text-based selectors with hover + click (more human-like)
            text_selectors = [
                'button:has-text("Agree and create profile")',
                'text="Agree and create profile"',
                'button >> text="Agree and create profile"',
            ]
            
            for selector in text_selectors:
                try:
                    logger.info(f"Trying text selector: {selector}")
                    element = await self.page.wait_for_selector(selector, timeout=5000, state="visible")
                    if element:
                        # Scroll into view first
                        await element.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)
                        # Hover to trigger any human behavior tracking
                        await element.hover()
                        await asyncio.sleep(0.4)
                        # Then click
                        await element.click()
                        logger.info("✅ Clicked via text selector")
                        await asyncio.sleep(3)
                        return True
                except:
                    continue
            
            # Method 2: Try XPath
            xpath_selectors = [
                '//button[contains(text(), "Agree and create profile")]',
                '//button[contains(., "Agree and create")]',
                '//button[contains(@class, "btn") and contains(., "Agree")]',
            ]
            
            for xpath in xpath_selectors:
                try:
                    logger.info(f"Trying XPath: {xpath}")
                    element = await self.page.wait_for_selector(f'xpath={xpath}', timeout=5000, state="visible")
                    if element:
                        await element.click()
                        logger.info("✅ Clicked via XPath")
                        await asyncio.sleep(3)
                        return True
                except:
                    continue
            
            # Method 3: Use JavaScript to find and click button
            logger.info("Trying JavaScript approach...")
            js_click_result = await self.page.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const agreeButton = buttons.find(btn => 
                        btn.textContent.includes('Agree and create profile') || 
                        btn.textContent.includes('Agree') ||
                        btn.innerText.includes('Agree and create profile')
                    );
                    
                    if (agreeButton) {
                        agreeButton.click();
                        return true;
                    }
                    return false;
                }
            """)
            
            if js_click_result:
                logger.info("✅ Clicked via JavaScript")
                await asyncio.sleep(3)
                return True
            
            # Method 4: Find button by role and accessible name
            logger.info("Trying role selector...")
            try:
                await self.page.click('role=button[name="Agree and create profile"]', timeout=5000)
                logger.info("✅ Clicked via role selector")
                await asyncio.sleep(3)
                return True
            except:
                pass
            
            # Method 5: Get all buttons and log them for debugging
            logger.warning("Could not find button, listing all buttons on page:")
            buttons_text = await self.page.evaluate("""
                () => {
                    return Array.from(document.querySelectorAll('button'))
                        .map(btn => btn.textContent.trim())
                        .filter(text => text.length > 0);
                }
            """)
            logger.info(f"Buttons found: {buttons_text}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
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
    signup_url: str = "https://www.welcometothejungle.com/en-GB/authenticate/signup?redirect=%2Fen-GB",
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
