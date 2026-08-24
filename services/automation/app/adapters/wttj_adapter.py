
"""Welcome to the Jungle (WTTJ) Adapter"""
from playwright.async_api import Page
import logging
import asyncio
import os

logger = logging.getLogger(__name__)


class WTTJAdapter:
    """Adapter for Welcome to the Jungle career site"""
    
    def __init__(self, base_url: str = "https://www.welcometothejungle.com"):
        self.base_url = base_url
        self.name = "WTTJ"
    
    async def create_account(
        self,
        page: Page,
        email: str,
        password: str,
        candidate_data: dict
    ) -> dict:
        """Create an account on WTTJ with full profile setup"""
        try:
            logger.info(f"Creating WTTJ account for {email} with enhanced profile data")
            
            # Navigate to homepage first
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')
            
            # Handle cookie consent
            try:
                cookie_button = page.locator('button:has-text("Accept"), button:has-text("Accepter"), [id*="cookie"], [class*="cookie"]')
                if await cookie_button.count() > 0:
                    await cookie_button.first.click()
                    await asyncio.sleep(1)
            except Exception:
                pass
            
            # Look for sign up link/button
            signup_selectors = [
                'a[href*="signup"]',
                'a:has-text("Sign up")', 
                'a:has-text("S\'inscrire")',
                'button:has-text("Sign up")',
                'button:has-text("S\'inscrire")',
                '[data-testid="signup"]',
                '.signup-button'
            ]
            
            signup_found = False
            for selector in signup_selectors:
                if await page.locator(selector).count() > 0:
                    await page.click(selector)
                    signup_found = True
                    break
            
            if not signup_found:
                # Try navigating directly to signup URL
                await page.goto(f"{self.base_url}/fr/signup")
            
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            # Take screenshot for debugging
            os.makedirs("screenshots", exist_ok=True)
            await page.screenshot(path=f"screenshots/wttj_signup_page.png")
            
            # Fill basic registration form
            await self._fill_basic_registration(page, email, password, candidate_data)
            
            # Submit registration
            success = await self._submit_registration(page)
            
            result = {
                "success": success,
                "email": email,
                "profile_completed": False,
                "email_verification_required": False,
                "message": ""
            }
            
            if success:
                await asyncio.sleep(3)
                
                # Check for email verification message
                email_verification_needed = await self._check_email_verification_required(page)
                result["email_verification_required"] = email_verification_needed
                
                if email_verification_needed:
                    result["message"] = f"Account created successfully! ⚠️ Please check your email ({email}) to verify your account before proceeding."
                    result["profile_completed"] = False
                    logger.info(f"Email verification required for {email}")
                else:
                    # Try to complete profile if we're logged in and verified
                    profile_result = await self._complete_profile_setup(page, candidate_data)
                    result["profile_completed"] = profile_result.get("success", False)
                    
                    if result["profile_completed"]:
                        result["message"] = "Account created and profile setup completed successfully!"
                    else:
                        result["message"] = "Account created! Profile setup may require manual completion."
                
                return result
            else:
                result["message"] = "Registration submission failed. Please try again."
                return result
            
        except Exception as e:
            logger.error(f"Failed to create WTTJ account: {e}")
            await page.screenshot(path=f"screenshots/wttj_error.png")
            return {
                "success": False,
                "email": email,
                "error": str(e),
                "message": f"Account creation failed: {str(e)}"
            }
    
    async def _check_email_verification_required(self, page: Page) -> bool:
        """Check if email verification is required"""
        try:
            # Look for email verification messages
            verification_indicators = [
                'text="verify your email"',
                'text="vérifiez votre email"',
                'text="check your email"',
                'text="email verification"',
                'text="confirm your email"',
                'text="confirmez votre email"',
                'text="activate your account"',
                '[data-testid*="verification"]',
                '[class*="verification"]',
                'text="sent you an email"',
                'text="nous vous avons envoyé"'
            ]
            
            for indicator in verification_indicators:
                try:
                    if await page.locator(indicator).count() > 0:
                        logger.info(f"Email verification indicator found: {indicator}")
                        return True
                except Exception:
                    pass
            
            # Check current URL for verification page
            current_url = page.url
            if any(keyword in current_url.lower() for keyword in ['verify', 'verification', 'confirm', 'activate']):
                logger.info(f"Email verification page detected: {current_url}")
                return True
            
            # Check page content
            page_content = await page.content()
            verification_keywords = [
                'verify your email',
                'vérifiez votre email', 
                'check your email',
                'email verification',
                'confirm your email',
                'activate your account'
            ]
            
            for keyword in verification_keywords:
                if keyword.lower() in page_content.lower():
                    logger.info(f"Email verification keyword found in page: {keyword}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check email verification: {e}")
            return False

    async def _fill_basic_registration(self, page: Page, email: str, password: str, candidate_data: dict):
        """Fill basic registration form fields"""
        # Email field
        email_selectors = [
            'input[name="email"]',
            'input[type="email"]',
            'input[placeholder*="mail"]',
            'input[id*="email"]',
            '#email'
        ]
        
        for selector in email_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await page.fill(selector, email)
                    logger.info(f"Email filled using selector: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Failed with selector {selector}: {e}")
        
        # Password field
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            'input[placeholder*="password"]',
            'input[placeholder*="mot de passe"]',
            '#password'
        ]
        
        for selector in password_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await page.fill(selector, password)
                    logger.info(f"Password filled using selector: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Failed with selector {selector}: {e}")
        
        # First name
        if candidate_data.get('first_name'):
            name_selectors = [
                'input[name="firstName"]',
                'input[name="first_name"]',
                'input[name="user[first_name]"]',
                'input[name*="first"]',
                'input[placeholder*="prénom" i]',
                'input[placeholder*="first" i]',
                'input[placeholder*="First"]',
                'input[placeholder*="Anita"]',
                '#firstName',
                '#first_name',
                '#user_first_name',
                'input[aria-label*="First"]'
            ]
            
            for selector in name_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.fill(selector, candidate_data['first_name'])
                        logger.info(f"First name filled using selector: {selector}")
                        break
                except Exception:
                    pass
        
        # Last name
        if candidate_data.get('last_name'):
            lastname_selectors = [
                'input[name="lastName"]',
                'input[name="last_name"]',
                'input[name="user[last_name]"]',
                'input[name*="last"]',
                'input[placeholder*="nom" i]',
                'input[placeholder*="last" i]',
                'input[placeholder*="Last"]',
                '#lastName',
                '#last_name',
                '#user_last_name',
                'input[aria-label*="Last"]'
            ]
            
            for selector in lastname_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.fill(selector, candidate_data['last_name'])
                        logger.info(f"Last name filled using selector: {selector}")
                        break
                except Exception:
                    pass
        
        # Accept terms if checkbox exists
        terms_selectors = [
            'input[type="checkbox"][name*="terms"]',
            'input[type="checkbox"][name*="conditions"]',
            'input[type="checkbox"][name*="cgu"]',
            'input[type="checkbox"]:near(text("terms"))',
            'input[type="checkbox"]:near(text("conditions"))'
        ]
        
        for selector in terms_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await page.check(selector)
                    break
            except Exception:
                pass
    
    async def _submit_registration(self, page: Page) -> bool:
        """Submit the registration form"""
        try:
            # Screenshot before submit
            await page.screenshot(path=f"screenshots/wttj_before_submit.png")
            
            # Submit the form
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Sign up")',
                'button:has-text("S\'inscrire")',
                'button:has-text("Create")',
                'button:has-text("Créer")',
                '[data-testid="submit"]'
            ]
            
            for selector in submit_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.click(selector)
                        logger.info(f"Submit clicked using selector: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Failed to click submit with selector {selector}: {e}")
            
            # Wait for response
            try:
                await page.wait_for_load_state('load', timeout=10000)
            except Exception:
                pass # ignore if timeout, page might still have loaded
            await asyncio.sleep(3)
            
            # Screenshot after submit
            await page.screenshot(path=f"screenshots/wttj_after_submit.png")
            
            return True
            
        except Exception as e:
            logger.error(f"Registration submission failed: {e}")
            return False
    
    async def _complete_profile_setup(self, page: Page, candidate_data: dict) -> dict:
        """Complete profile setup with enhanced data"""
        try:
            logger.info("Attempting to complete profile setup")
            
            # Look for profile completion prompts
            profile_selectors = [
                'a:has-text("Complete")',
                'a:has-text("Profile")',
                'button:has-text("Profile")',
                '[href*="profile"]',
                '.profile-button'
            ]
            
            profile_found = False
            for selector in profile_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.click(selector)
                        profile_found = True
                        logger.info(f"Profile section accessed using: {selector}")
                        break
                except Exception:
                    pass
            
            if not profile_found:
                # Try navigating directly to profile
                current_url = page.url
                if "welcometothejungle" in current_url:
                    await page.goto(f"{self.base_url}/fr/me/profile")
            
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            # Fill profile fields if available
            fields_filled = await self._fill_profile_fields(page, candidate_data)
            
            await page.screenshot(path=f"screenshots/wttj_profile_completed.png")
            
            return {
                "success": True,
                "fields_filled": fields_filled
            }
            
        except Exception as e:
            logger.error(f"Profile setup failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _fill_profile_fields(self, page: Page, candidate_data: dict) -> int:
        """Fill available profile fields with AI-enhanced content"""
        fields_filled = 0
        
        try:
            logger.info("Filling profile fields with AI-enhanced content")
            
            # Bio/About section with AI-enhanced content
            bio_content = candidate_data.get('bio') or candidate_data.get('summary', '')
            if bio_content:
                bio_selectors = [
                    'textarea[name*="bio"]',
                    'textarea[name*="about"]',
                    'textarea[placeholder*="about"]',
                    'textarea[placeholder*="bio"]',
                    'textarea[name*="description"]',
                    'textarea[name*="summary"]',
                    '#bio',
                    '#about',
                    '#description'
                ]
                
                for selector in bio_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            await page.fill(selector, bio_content)
                            logger.info("Bio/About section filled with AI-enhanced content")
                            fields_filled += 1
                            break
                    except Exception:
                        pass
            
            # Professional headline
            headline = candidate_data.get('headline', '')
            if headline:
                headline_selectors = [
                    'input[name*="headline"]',
                    'input[name*="title"]',
                    'input[placeholder*="headline"]',
                    'input[placeholder*="titre"]',
                    '#headline',
                    '#title'
                ]
                
                for selector in headline_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            await page.fill(selector, headline)
                            logger.info("Professional headline filled")
                            break
                    except Exception:
                        pass
            
            # Location
            if candidate_data.get('location'):
                location_selectors = [
                    'input[name*="location"]',
                    'input[placeholder*="location"]',
                    'input[placeholder*="ville"]',
                    'input[name*="city"]',
                    '#location',
                    '#city'
                ]
                
                for selector in location_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            await page.fill(selector, candidate_data['location'])
                            logger.info("Location filled")
                            break
                    except Exception:
                        pass
            
            # Phone
            if candidate_data.get('phone'):
                phone_selectors = [
                    'input[name*="phone"]',
                    'input[type="tel"]',
                    'input[placeholder*="phone"]',
                    'input[placeholder*="téléphone"]',
                    '#phone'
                ]
                
                for selector in phone_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            await page.fill(selector, candidate_data['phone'])
                            logger.info("Phone filled")
                            break
                    except Exception:
                        pass
            
            # LinkedIn URL
            if candidate_data.get('linkedin_url'):
                linkedin_selectors = [
                    'input[name*="linkedin"]',
                    'input[placeholder*="linkedin"]',
                    'input[name*="profile"]',
                    'input[placeholder*="profil"]',
                    '#linkedin'
                ]
                
                for selector in linkedin_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            await page.fill(selector, candidate_data['linkedin_url'])
                            logger.info("LinkedIn URL filled")
                            break
                    except Exception:
                        pass
            
            # Experience years
            if candidate_data.get('experience_years'):
                exp_selectors = [
                    'input[name*="experience"]',
                    'input[placeholder*="experience"]',
                    'input[name*="years"]',
                    'select[name*="experience"]',
                    '#experience'
                ]
                
                for selector in exp_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            if 'select' in selector:
                                # Handle dropdown selection
                                await page.select_option(selector, str(candidate_data['experience_years']))
                            else:
                                await page.fill(selector, str(candidate_data['experience_years']))
                            logger.info("Experience years filled")
                            break
                    except Exception:
                        pass
            
            # Skills - Enhanced with AI suggestions
            skills_to_add = candidate_data.get('skills', [])
            if isinstance(skills_to_add, str):
                skills_to_add = skills_to_add.split(',')
            
            if skills_to_add:
                skills_input_selectors = [
                    'input[name*="skill"]',
                    'input[placeholder*="skill"]',
                    'input[placeholder*="compétence"]',
                    'input[name*="competence"]',
                    '#skills'
                ]
                
                for selector in skills_input_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            # Add skills one by one
                            skills_added = 0
                            for skill in skills_to_add:
                                if skills_added >= 10:  # Limit to prevent spam
                                    break
                                try:
                                    await page.fill(selector, skill.strip())
                                    await page.press(selector, 'Enter')
                                    await asyncio.sleep(1)  # Wait between additions
                                    skills_added += 1
                                    logger.info(f"Added skill: {skill.strip()}")
                                except Exception:
                                    # If Enter doesn't work, try Tab or just continue
                                    try:
                                        await page.press(selector, 'Tab')
                                        await asyncio.sleep(0.5)
                                    except Exception:
                                        pass
                            break
                    except Exception as e:
                        logger.debug(f"Skills selector {selector} failed: {e}")
            
            # Work preferences (AI-generated)
            work_pref = candidate_data.get('work_preference', '')
            if work_pref:
                pref_selectors = [
                    'textarea[name*="preference"]',
                    'textarea[name*="interest"]',
                    'textarea[placeholder*="préférence"]',
                    'textarea[name*="motivation"]'
                ]
                
                for selector in pref_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            await page.fill(selector, work_pref)
                            logger.info("Work preferences filled")
                            break
                    except Exception:
                        pass
            
            # Career interests
            career_interests = candidate_data.get('career_interests', '')
            if career_interests:
                interests_selectors = [
                    'textarea[name*="interest"]',
                    'textarea[name*="career"]',
                    'textarea[placeholder*="intérêt"]',
                    'input[name*="objective"]'
                ]
                
                for selector in interests_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            await page.fill(selector, career_interests)
                            logger.info("Career interests filled")
                            break
                    except Exception:
                        pass
            
            # Salary expectations (if field exists)
            salary_exp = candidate_data.get('salary_expectations', '')
            if salary_exp:
                salary_selectors = [
                    'input[name*="salary"]',
                    'input[name*="salaire"]',
                    'input[placeholder*="salary"]',
                    'select[name*="salary"]'
                ]
                
                for selector in salary_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            await page.fill(selector, salary_exp)
                            logger.info("Salary expectations filled")
                            break
                    except Exception:
                        pass
            
            # Availability
            availability = candidate_data.get('availability', 'Available immediately')
            if availability:
                avail_selectors = [
                    'input[name*="availability"]',
                    'input[name*="disponibilité"]',
                    'select[name*="availability"]',
                    'input[placeholder*="when"]'
                ]
                
                for selector in avail_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            if 'select' in selector:
                                await page.select_option(selector, availability)
                            else:
                                await page.fill(selector, availability)
                            logger.info("Availability filled")
                            break
                    except Exception:
                        pass
            
            # Save profile if save button exists
            save_selectors = [
                'button:has-text("Save")',
                'button:has-text("Sauvegarder")',
                'button:has-text("Enregistrer")',
                'button[type="submit"]',
                'input[type="submit"]',
                '.save-button',
                '[data-testid="save"]'
            ]
            
            for selector in save_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.click(selector)
                        await asyncio.sleep(3)  # Wait for save to complete
                        logger.info("Profile saved successfully")
                        break
                except Exception as e:
                    logger.debug(f"Save selector {selector} failed: {e}")
            
            logger.info(f"Profile setup complete. Fields filled: {fields_filled}")
            return fields_filled
                    
        except Exception as e:
            logger.error(f"Profile field filling failed: {e}")
            return fields_filled
    
    async def login(self, page: Page, email: str, password: str) -> bool:
        """Login to WTTJ"""
        try:
            logger.info(f"Logging into WTTJ with {email}")
            
            # Try multiple login URL formats
            login_urls = [
                f"{self.base_url}/en/signin",
                f"{self.base_url}/fr/signin", 
                f"{self.base_url}/en/login",
                f"{self.base_url}/fr/login",
                f"{self.base_url}/signin",
                f"{self.base_url}/login"
            ]
            
            login_page_found = False
            for login_url in login_urls:
                try:
                    logger.info(f"Trying login URL: {login_url}")
                    response = await page.goto(login_url, wait_until='networkidle', timeout=10000)
                    
                    # Check if we got a 404
                    if response and response.status == 404:
                        logger.warning(f"404 error for {login_url}, trying next...")
                        continue
                    
                    # Check if login form exists
                    await asyncio.sleep(2)
                    email_input = page.locator('input[type="email"], input[name*="email"], input[placeholder*="email" i]')
                    if await email_input.count() > 0:
                        logger.info(f"Login form found at: {login_url}")
                        login_page_found = True
                        break
                    else:
                        logger.warning(f"No login form at {login_url}, trying next...")
                        
                except Exception as e:
                    logger.debug(f"Failed to load {login_url}: {e}")
                    continue
            
            if not login_page_found:
                # Try going to homepage first, then clicking sign in
                logger.info("Direct login URLs failed, trying homepage first...")
                await page.goto(self.base_url)
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
                
                # Look for sign in button
                signin_selectors = [
                    'a:has-text("Sign in")',
                    'a:has-text("Log in")',
                    'a:has-text("Se connecter")',
                    'button:has-text("Sign in")',
                    'button:has-text("Log in")',
                    '[href*="signin"]',
                    '[href*="login"]'
                ]
                
                for selector in signin_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            await page.click(selector)
                            await page.wait_for_load_state('networkidle')
                            await asyncio.sleep(2)
                            logger.info(f"Clicked sign in button: {selector}")
                            login_page_found = True
                            break
                    except Exception:
                        pass
            
            if not login_page_found:
                logger.error("Could not find login page")
                await page.screenshot(path="screenshots/wttj_login_404.png")
                return False
            
            # Take screenshot of login page
            await page.screenshot(path="screenshots/wttj_login_page.png")
            
            # Handle cookie consent
            try:
                cookie_button = page.locator('button:has-text("Accept"), button:has-text("Accepter"), button:has-text("OK")')
                if await cookie_button.count() > 0:
                    await cookie_button.first.click()
                    await asyncio.sleep(1)
            except Exception:
                pass
            
            # Fill email with multiple attempts
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[name*="email"]',
                'input[placeholder*="email" i]',
                'input[autocomplete="email"]',
                '#email',
                '[data-testid*="email"]'
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.fill(selector, email)
                        logger.info(f"Email filled using: {selector}")
                        email_filled = True
                        break
                except Exception as e:
                    logger.debug(f"Failed to fill email with {selector}: {e}")
            
            if not email_filled:
                logger.error("Could not fill email field")
                await page.screenshot(path="screenshots/wttj_login_no_email_field.png")
                return False
            
            await asyncio.sleep(1)
            
            # Fill password with multiple attempts
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[name*="password"]',
                'input[placeholder*="password" i]',
                'input[placeholder*="mot de passe" i]',
                'input[autocomplete="current-password"]',
                '#password',
                '[data-testid*="password"]'
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.fill(selector, password)
                        logger.info(f"Password filled using: {selector}")
                        password_filled = True
                        break
                except Exception as e:
                    logger.debug(f"Failed to fill password with {selector}: {e}")
            
            if not password_filled:
                logger.error("Could not fill password field")
                await page.screenshot(path="screenshots/wttj_login_no_password_field.png")
                return False
            
            await asyncio.sleep(1)
            await page.screenshot(path="screenshots/wttj_login_filled.png")
            
            # Click submit
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Sign in")',
                'button:has-text("Log in")',
                'button:has-text("Se connecter")',
                'button:has-text("Connexion")',
                '[data-testid*="submit"]',
                '[data-testid*="login"]',
                'button:has-text("Continue")',
                'button:has-text("Continuer")'
            ]
            
            submit_clicked = False
            for selector in submit_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.click(selector)
                        logger.info(f"Submit button clicked: {selector}")
                        submit_clicked = True
                        break
                except Exception as e:
                    logger.debug(f"Failed to click submit with {selector}: {e}")
            
            if not submit_clicked:
                logger.error("Could not click submit button")
                await page.screenshot(path="screenshots/wttj_login_no_submit.png")
                return False
            
            # Wait for navigation
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
            except Exception:
                pass
            
            await asyncio.sleep(3)
            await page.screenshot(path="screenshots/wttj_after_login.png")
            
            # Check if login was successful
            current_url = page.url
            
            # Multiple success indicators
            success_indicators = [
                "dashboard" in current_url.lower(),
                "profile" in current_url.lower(),
                "me" in current_url.lower(),
                "jobs" in current_url.lower() and "signin" not in current_url.lower(),
                "account" in current_url.lower()
            ]
            
            # Also check if we're NOT on login/signin page
            not_on_login = not any([
                "login" in current_url.lower(),
                "signin" in current_url.lower(),
                "sign-in" in current_url.lower()
            ])
            
            success = any(success_indicators) or not_on_login
            
            # Additional check: look for logged-in elements
            if not success:
                # Look for user menu or profile elements
                logged_in_selectors = [
                    '[data-testid*="user"]',
                    '[data-testid*="profile"]',
                    'button:has-text("Profile")',
                    'a:has-text("Profile")',
                    '[href*="profile"]',
                    '[href*="/me/"]'
                ]
                
                for selector in logged_in_selectors:
                    if await page.locator(selector).count() > 0:
                        success = True
                        logger.info(f"Found logged-in indicator: {selector}")
                        break
            
            if success:
                logger.info(f"WTTJ login successful - URL: {current_url}")
            else:
                logger.error(f"WTTJ login failed - Still on: {current_url}")
                
                # Check for error messages
                error_selectors = [
                    '[class*="error"]',
                    '[data-testid*="error"]',
                    'div:has-text("incorrect")',
                    'div:has-text("invalid")',
                    'div:has-text("wrong")'
                ]
                
                for selector in error_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            error_text = await page.locator(selector).first.text_content()
                            logger.error(f"Login error message: {error_text}")
                    except Exception:
                        pass
            
            return success
            
        except Exception as e:
            logger.error(f"WTTJ login failed with exception: {e}")
            import traceback
            traceback.print_exc()
            try:
                await page.screenshot(path="screenshots/wttj_login_exception.png")
            except Exception:
                pass
            return False
    
    async def upload_resume(self, page: Page, resume_path: str) -> dict:
        """Upload resume/CV to WTTJ profile"""
        try:
            logger.info(f"Uploading resume: {resume_path}")
            
            # Navigate to profile/resume section
            profile_urls = [
                f"{self.base_url}/fr/me/profile",
                f"{self.base_url}/fr/me/cv",
                f"{self.base_url}/fr/me/resume"
            ]
            
            for url in profile_urls:
                try:
                    await page.goto(url)
                    await page.wait_for_load_state('networkidle')
                    await asyncio.sleep(2)
                    break
                except Exception:
                    continue
            
            # Look for file upload input
            file_selectors = [
                'input[type="file"][accept*="pdf"]',
                'input[type="file"][name*="resume"]',
                'input[type="file"][name*="cv"]',
                'input[type="file"]',
                '[data-testid*="upload"]'
            ]
            
            uploaded = False
            for selector in file_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.set_input_files(selector, resume_path)
                        logger.info(f"Resume uploaded using selector: {selector}")
                        uploaded = True
                        await asyncio.sleep(3)  # Wait for upload
                        break
                except Exception as e:
                    logger.debug(f"Upload selector {selector} failed: {e}")
            
            if not uploaded:
                # Try clicking upload button first
                upload_buttons = [
                    'button:has-text("Upload")',
                    'button:has-text("Télécharger")',
                    'button:has-text("Add CV")',
                    'button:has-text("Ajouter CV")',
                    '[data-testid*="upload"]'
                ]
                
                for button in upload_buttons:
                    try:
                        if await page.locator(button).count() > 0:
                            await page.click(button)
                            await asyncio.sleep(1)
                            
                            # Try file input again
                            if await page.locator('input[type="file"]').count() > 0:
                                await page.set_input_files('input[type="file"]', resume_path)
                                uploaded = True
                                logger.info("Resume uploaded after clicking upload button")
                                break
                    except Exception as e:
                        logger.debug(f"Upload button {button} failed: {e}")
            
            await page.screenshot(path="screenshots/wttj_resume_uploaded.png")
            
            if uploaded:
                return {
                    "success": True,
                    "message": "Resume uploaded successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Could not find resume upload field"
                }
                
        except Exception as e:
            logger.error(f"Resume upload failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def connect_linkedin(self, page: Page, linkedin_url: str) -> dict:
        """Connect LinkedIn profile to WTTJ account"""
        try:
            logger.info(f"Connecting LinkedIn: {linkedin_url}")
            
            # Navigate to profile settings
            await page.goto(f"{self.base_url}/fr/me/profile")
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            # Look for LinkedIn connection options
            linkedin_selectors = [
                'a[href*="linkedin"]',
                'button:has-text("LinkedIn")',
                'button:has-text("Connect LinkedIn")',
                '[data-testid*="linkedin"]',
                'input[name*="linkedin"]'
            ]
            
            connected = False
            for selector in linkedin_selectors:
                try:
                    locator = page.locator(selector)
                    if await locator.count() > 0:
                        element_type = await locator.first.evaluate("el => el.tagName")
                        
                        if element_type.lower() == 'input':
                            # Input field - fill with URL
                            await page.fill(selector, linkedin_url)
                            logger.info("LinkedIn URL filled in input field")
                            connected = True
                        else:
                            # Button/Link - click it
                            await page.click(selector)
                            await asyncio.sleep(2)
                            
                            # May open OAuth or input field
                            if await page.locator('input[name*="linkedin"]').count() > 0:
                                await page.fill('input[name*="linkedin"]', linkedin_url)
                            
                            logger.info("LinkedIn connection initiated")
                            connected = True
                        break
                except Exception as e:
                    logger.debug(f"LinkedIn selector {selector} failed: {e}")
            
            await page.screenshot(path="screenshots/wttj_linkedin_connected.png")
            
            if connected:
                return {
                    "success": True,
                    "message": "LinkedIn profile connected"
                }
            else:
                return {
                    "success": False,
                    "error": "Could not find LinkedIn connection option"
                }
                
        except Exception as e:
            logger.error(f"LinkedIn connection failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def set_job_preferences(self, page: Page, preferences: dict) -> dict:
        """Set job preferences (remote work, contract type, salary, etc.)"""
        try:
            logger.info("Setting job preferences")
            
            # Navigate to preferences/settings
            pref_urls = [
                f"{self.base_url}/fr/me/preferences",
                f"{self.base_url}/fr/me/settings",
                f"{self.base_url}/fr/me/job-preferences"
            ]
            
            for url in pref_urls:
                try:
                    await page.goto(url)
                    await page.wait_for_load_state('networkidle')
                    await asyncio.sleep(2)
                    break
                except Exception:
                    continue
            
            # Remote work preference
            if preferences.get('remote_work'):
                remote_selectors = [
                    'input[name*="remote"]',
                    'select[name*="remote"]',
                    'button:has-text("Remote")',
                    '[data-testid*="remote"]'
                ]
                
                for selector in remote_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            element_type = await page.locator(selector).first.evaluate("el => el.tagName")
                            
                            if element_type.lower() == 'select':
                                await page.select_option(selector, preferences['remote_work'])
                            elif element_type.lower() == 'input':
                                input_type = await page.locator(selector).first.get_attribute('type')
                                if input_type == 'checkbox':
                                    if preferences['remote_work'] in ['yes', 'true', True]:
                                        await page.check(selector)
                                else:
                                    await page.fill(selector, str(preferences['remote_work']))
                            else:
                                await page.click(selector)
                            
                            logger.info(f"Remote work preference set: {preferences['remote_work']}")
                            break
                    except Exception as e:
                        logger.debug(f"Remote selector {selector} failed: {e}")
            
            # Contract type (CDI, CDD, Freelance, etc.)
            if preferences.get('contract_type'):
                contract_selectors = [
                    'select[name*="contract"]',
                    'input[name*="contract"]',
                    'select[name*="type"]',
                    '[data-testid*="contract"]'
                ]
                
                for selector in contract_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            element_type = await page.locator(selector).first.evaluate("el => el.tagName")
                            
                            if element_type.lower() == 'select':
                                # Try to select by value or label
                                contract_types = preferences['contract_type']
                                if isinstance(contract_types, str):
                                    contract_types = [contract_types]
                                
                                for contract in contract_types:
                                    try:
                                        await page.select_option(selector, contract)
                                        logger.info(f"Contract type selected: {contract}")
                                    except Exception:
                                        pass
                            break
                    except Exception as e:
                        logger.debug(f"Contract selector {selector} failed: {e}")
            
            # Salary expectations
            if preferences.get('salary_min') or preferences.get('salary_max'):
                salary_min = preferences.get('salary_min', '')
                salary_max = preferences.get('salary_max', '')
                
                # Minimum salary
                if salary_min:
                    min_selectors = [
                        'input[name*="salary"][name*="min"]',
                        'input[placeholder*="minimum"]',
                        'input[id*="salary-min"]'
                    ]
                    
                    for selector in min_selectors:
                        try:
                            if await page.locator(selector).count() > 0:
                                await page.fill(selector, str(salary_min))
                                logger.info(f"Min salary set: {salary_min}")
                                break
                        except Exception:
                            pass
                
                # Maximum salary
                if salary_max:
                    max_selectors = [
                        'input[name*="salary"][name*="max"]',
                        'input[placeholder*="maximum"]',
                        'input[id*="salary-max"]'
                    ]
                    
                    for selector in max_selectors:
                        try:
                            if await page.locator(selector).count() > 0:
                                await page.fill(selector, str(salary_max))
                                logger.info(f"Max salary set: {salary_max}")
                                break
                        except Exception:
                            pass
            
            # Job location preferences
            if preferences.get('preferred_locations'):
                locations = preferences['preferred_locations']
                if isinstance(locations, str):
                    locations = [locations]
                
                location_selectors = [
                    'input[name*="location"]',
                    'input[placeholder*="location"]',
                    'input[placeholder*="ville"]'
                ]
                
                for selector in location_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            for location in locations:
                                await page.fill(selector, location)
                                await page.press(selector, 'Enter')
                                await asyncio.sleep(1)
                            logger.info(f"Preferred locations set: {locations}")
                            break
                    except Exception:
                        pass
            
            # Job categories/sectors
            if preferences.get('job_categories'):
                categories = preferences['job_categories']
                if isinstance(categories, str):
                    categories = [categories]
                
                category_selectors = [
                    'input[name*="category"]',
                    'input[name*="sector"]',
                    'select[name*="category"]'
                ]
                
                for selector in category_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            element_type = await page.locator(selector).first.evaluate("el => el.tagName")
                            
                            if element_type.lower() == 'select':
                                for category in categories:
                                    try:
                                        await page.select_option(selector, category)
                                    except Exception:
                                        pass
                            else:
                                for category in categories:
                                    await page.fill(selector, category)
                                    await page.press(selector, 'Enter')
                                    await asyncio.sleep(1)
                            
                            logger.info(f"Job categories set: {categories}")
                            break
                    except Exception:
                        pass
            
            # Company size preference
            if preferences.get('company_size'):
                size_selectors = [
                    'select[name*="size"]',
                    'select[name*="company"]',
                    'input[name*="company-size"]'
                ]
                
                for selector in size_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            await page.select_option(selector, preferences['company_size'])
                            logger.info(f"Company size set: {preferences['company_size']}")
                            break
                    except Exception:
                        pass
            
            # Save preferences
            save_selectors = [
                'button[type="submit"]',
                'button:has-text("Save")',
                'button:has-text("Sauvegarder")',
                'input[type="submit"]'
            ]
            
            for selector in save_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.click(selector)
                        await asyncio.sleep(3)
                        logger.info("Preferences saved")
                        break
                except Exception:
                    pass
            
            await page.screenshot(path="screenshots/wttj_preferences_set.png")
            
            return {
                "success": True,
                "message": "Job preferences set successfully",
                "preferences_set": preferences
            }
            
        except Exception as e:
            logger.error(f"Setting preferences failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_matching_jobs(self, page: Page, filters: dict = None) -> dict:
        """Get jobs matching user profile and preferences"""
        try:
            logger.info("Fetching matching jobs")
            
            # Navigate to jobs page
            await page.goto(f"{self.base_url}/fr/jobs")
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)
            
            # Apply filters if provided
            if filters:
                # Search by keyword
                if filters.get('keywords'):
                    search_selectors = [
                        'input[name*="search"]',
                        'input[placeholder*="search"]',
                        'input[type="search"]',
                        '[data-testid*="search"]'
                    ]
                    
                    for selector in search_selectors:
                        try:
                            if await page.locator(selector).count() > 0:
                                await page.fill(selector, filters['keywords'])
                                await page.press(selector, 'Enter')
                                await asyncio.sleep(2)
                                logger.info(f"Search by keyword: {filters['keywords']}")
                                break
                        except Exception:
                            pass
                
                # Filter by location
                if filters.get('location'):
                    location_selectors = [
                        'input[name*="location"]',
                        'input[placeholder*="location"]',
                        'input[placeholder*="où"]'
                    ]
                    
                    for selector in location_selectors:
                        try:
                            if await page.locator(selector).count() > 0:
                                await page.fill(selector, filters['location'])
                                await page.press(selector, 'Enter')
                                await asyncio.sleep(2)
                                logger.info(f"Filter by location: {filters['location']}")
                                break
                        except Exception:
                            pass
                
                # Filter by contract type
                if filters.get('contract_type'):
                    # Look for filter buttons or dropdowns
                    contract_filter = f"button:has-text('{filters['contract_type']}')"
                    try:
                        if await page.locator(contract_filter).count() > 0:
                            await page.click(contract_filter)
                            await asyncio.sleep(2)
                    except Exception:
                        pass
                
                # Filter by remote
                if filters.get('remote'):
                    remote_filters = [
                        'button:has-text("Remote")',
                        'button:has-text("Télétravail")',
                        'input[name*="remote"]'
                    ]
                    
                    for selector in remote_filters:
                        try:
                            if await page.locator(selector).count() > 0:
                                await page.click(selector)
                                await asyncio.sleep(2)
                                logger.info("Remote filter applied")
                                break
                        except Exception:
                            pass
            
            await page.screenshot(path="screenshots/wttj_jobs_filtered.png")
            
            # Extract job listings
            jobs = []
            job_selectors = [
                '[data-testid*="job"]',
                '.job-card',
                'article',
                '[class*="JobCard"]'
            ]
            
            for selector in job_selectors:
                try:
                    job_elements = page.locator(selector)
                    count = await job_elements.count()
                    
                    if count > 0:
                        logger.info(f"Found {count} job listings")
                        
                        # Extract first 10 jobs
                        for i in range(min(count, 10)):
                            try:
                                job_element = job_elements.nth(i)
                                
                                # Extract job details
                                job_data = {}
                                
                                # Title
                                title_selectors = ['h2', 'h3', '[class*="title"]', 'a']
                                for title_sel in title_selectors:
                                    try:
                                        title = await job_element.locator(title_sel).first.inner_text()
                                        if title:
                                            job_data['title'] = title.strip()
                                            break
                                    except Exception:
                                        pass
                                
                                # Company
                                company_selectors = ['[class*="company"]', 'span', 'div']
                                for comp_sel in company_selectors:
                                    try:
                                        company = await job_element.locator(comp_sel).first.inner_text()
                                        if company and company != job_data.get('title'):
                                            job_data['company'] = company.strip()
                                            break
                                    except Exception:
                                        pass
                                
                                # Location
                                location_selectors = ['[class*="location"]', '[class*="place"]']
                                for loc_sel in location_selectors:
                                    try:
                                        location = await job_element.locator(loc_sel).first.inner_text()
                                        if location:
                                            job_data['location'] = location.strip()
                                            break
                                    except Exception:
                                        pass
                                
                                # URL
                                try:
                                    link = await job_element.locator('a').first.get_attribute('href')
                                    if link:
                                        if not link.startswith('http'):
                                            link = self.base_url + link
                                        job_data['url'] = link
                                except Exception:
                                    pass
                                
                                if job_data.get('title'):
                                    jobs.append(job_data)
                                    
                            except Exception as e:
                                logger.debug(f"Failed to extract job {i}: {e}")
                        
                        break
                except Exception as e:
                    logger.debug(f"Job selector {selector} failed: {e}")
            
            logger.info(f"Extracted {len(jobs)} matching jobs")
            
            return {
                "success": True,
                "jobs": jobs,
                "total_found": len(jobs),
                "filters_applied": filters or {}
            }
            
        except Exception as e:
            logger.error(f"Job matching failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "jobs": []
            }
    
    async def apply_to_job(
        self,
        page: Page,
        job_url: str,
        application_data: dict
    ) -> dict:
        """Apply to a job on WTTJ"""
        try:
            logger.info(f"Applying to WTTJ job: {job_url}")
            
            # Navigate to job page
            await page.goto(job_url)
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            # Look for apply button
            apply_selectors = [
                'button:has-text("Apply")',
                'button:has-text("Postuler")',
                'a:has-text("Apply")',
                'a:has-text("Postuler")',
                '[data-testid*="apply"]',
                '.apply-button'
            ]
            
            apply_found = False
            for selector in apply_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.click(selector)
                        apply_found = True
                        logger.info(f"Apply button clicked using selector: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Failed to click apply with selector {selector}: {e}")
            
            if not apply_found:
                logger.warning("Could not find apply button")
                await page.screenshot(path=f"screenshots/wttj_no_apply_button.png")
                return {
                    "success": False,
                    "error": "Could not find apply button"
                }
            
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)
            
            # Upload resume if file input exists
            if application_data.get('resume_path'):
                file_inputs = page.locator('input[type="file"]')
                if await file_inputs.count() > 0:
                    try:
                        await file_inputs.first.set_input_files(application_data['resume_path'])
                        logger.info("Resume uploaded")
                    except Exception as e:
                        logger.warning(f"Failed to upload resume: {e}")
            
            # Fill cover letter if textarea exists
            if application_data.get('cover_letter'):
                cover_selectors = [
                    'textarea[name*="cover"]',
                    'textarea[name*="message"]',
                    'textarea[placeholder*="message"]',
                    'textarea[placeholder*="lettre"]',
                    'textarea'
                ]
                
                for selector in cover_selectors:
                    try:
                        if await page.locator(selector).count() > 0:
                            await page.fill(selector, application_data['cover_letter'])
                            logger.info("Cover letter filled")
                            break
                    except Exception:
                        pass
            
            await page.screenshot(path=f"screenshots/wttj_application_filled.png")
            
            # Submit application
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Submit")',
                'button:has-text("Envoyer")',
                'button:has-text("Send")',
                'input[type="submit"]'
            ]
            
            submit_clicked = False
            for selector in submit_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.click(selector)
                        submit_clicked = True
                        logger.info(f"Submit clicked using selector: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Failed to submit with selector {selector}: {e}")
            
            if not submit_clicked:
                # Maybe the application was already complete after clicking apply
                logger.info("No explicit submit button found - application may be complete")
            
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)
            
            await page.screenshot(path="screenshots/wttj_application_complete.png")
            
            return {
                "success": True,
                "message": "Application submitted successfully",
                "job_url": job_url
            }
            
        except Exception as e:
            logger.error(f"Job application failed: {e}")
            await page.screenshot(path="screenshots/wttj_application_error.png")
            return {
                "success": False,
                "error": str(e)
            }
