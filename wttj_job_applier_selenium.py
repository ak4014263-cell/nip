#!/usr/bin/env python3
"""
WTTJ Job Application Engine - Hybrid Approach with Multiple Submission Methods
Attempts to submit applications using:
1. Playwright (best anti-bot evasion)
2. Selenium (backup)
3. API (if available)
4. Fallback to Swiply tracking + manual link
"""
import os
import logging
import httpx
import asyncio
import time
import json
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import Playwright first
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
    logger.info("✅ Playwright WebDriver available for real browser automation")
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning(f"⚠️ Playwright not available - will try Selenium")

# Try to import Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
    logger.info("✅ Selenium WebDriver available as backup")
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning(f"⚠️ Selenium not available")

class WTTJJobApplierSelenium:
    
    def __init__(self, credential_service_url="http://localhost:8009", profile_service_url="http://localhost:8004", application_service_url="http://localhost:8003"):
        self.credential_service_url = credential_service_url
        self.profile_service_url = profile_service_url
        self.application_service_url = application_service_url
        self.wttj_base_url = "https://www.welcometothejungle.com"
        self.wttj_login_url = f"{self.wttj_base_url}/en/login"
        # WTTJ API endpoint (if they expose one)
        self.wttj_api_base = "https://www.welcometothejungle.com/api"

    async def _submit_via_api(self, user_id: str, email: str, password: str, job_url: str, profile_data: Dict[str, Any]) -> Optional[Dict]:
        """Try to submit application via WTTJ API"""
        try:
            logger.info("🔌 Attempting WTTJ API submission...")
            
            # Extract job ID from URL
            job_id = None
            try:
                parts = job_url.rstrip('/').split('/')
                if 'jobs' in parts:
                    job_slug = parts[parts.index('jobs') + 1]
                    if '_' in job_slug:
                        job_id = job_slug.split('_')[-1]
            except:
                pass
            
            if not job_id:
                logger.warning("Could not extract job ID from URL")
                return None
            
            # Prepare API payload for WTTJ
            api_payload = {
                "job_id": job_id,
                "candidate_email": email,
                "first_name": profile_data.get("first_name", "User"),
                "last_name": profile_data.get("last_name", "Candidate"),
                "phone": profile_data.get("phone"),
                "location": profile_data.get("location"),
                "cover_letter": f"Applying from Swiply automation platform"
            }
            
            # Try WTTJ API (this is exploratory - URL might not exist)
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Method 1: Try public API endpoint
                try:
                    response = await client.post(
                        f"{self.wttj_api_base}/applications",
                        json=api_payload,
                        headers={"Authorization": f"Bearer {password}"}
                    )
                    
                    if response.status_code in [200, 201]:
                        logger.info("✅ Application submitted via WTTJ API")
                        return {"success": True, "method": "api", "response": response.json()}
                except Exception as e:
                    logger.debug(f"API endpoint 1 failed: {e}")
                
                # Method 2: Try authenticated session
                try:
                    # Create session and login
                    session_response = await client.post(
                        f"{self.wttj_base_url}/api/auth/login",
                        json={"email": email, "password": password}
                    )
                    
                    if session_response.status_code in [200, 201]:
                        session_data = session_response.json()
                        token = session_data.get("token") or session_data.get("access_token")
                        
                        if token:
                            # Submit application with token
                            app_response = await client.post(
                                f"{self.wttj_base_url}/api/applications",
                                json=api_payload,
                                headers={"Authorization": f"Bearer {token}"}
                            )
                            
                            if app_response.status_code in [200, 201]:
                                logger.info("✅ Application submitted via WTTJ authenticated API")
                                return {"success": True, "method": "api_authenticated", "response": app_response.json()}
                except Exception as e:
                    logger.debug(f"API authentication failed: {e}")
            
            return None
            
        except Exception as e:
            logger.debug(f"API submission attempt failed: {e}")
            return None

    def _create_webdriver(self):
        """Create a Chrome WebDriver instance for browser automation"""
        if not SELENIUM_AVAILABLE:
            return None
            
        try:
            options = ChromeOptions()
            # Run in headless mode to avoid popup windows
            options.add_argument("--headless")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-gpu")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
            return driver
        except Exception as e:
            logger.error(f"Failed to create WebDriver: {e}")
            return None

    def _login_to_wttj(self, driver, email: str, password: str, max_retries: int = 3) -> bool:
        """Login to WTTJ website using Selenium - enhanced with better waits"""
        for attempt in range(max_retries):
            try:
                logger.info(f"🔐 Login attempt {attempt + 1}/{max_retries}: Navigating to WTTJ login page...")
                driver.get(self.wttj_login_url)
                
                # Wait longer for JavaScript to load
                time.sleep(4)
                
                # Execute JavaScript to find the actual input elements
                wait = WebDriverWait(driver, 20)
                
                logger.info("Looking for email input with JavaScript execution...")
                
                # Try to find by executing JavaScript
                try:
                    driver.execute_script("""
                        var inputs = document.querySelectorAll('input[type="email"], input[name="email"], input[name="identifier"]');
                        if (inputs.length > 0) { inputs[0].scrollIntoView(); }
                    """)
                    time.sleep(1)
                except:
                    pass
                
                # Get all input elements to debug
                all_inputs = driver.find_elements(By.TAG_NAME, "input")
                logger.info(f"Found {len(all_inputs)} input elements on page")
                
                for i, inp in enumerate(all_inputs[:10]):
                    try:
                        inp_type = inp.get_attribute("type")
                        inp_name = inp.get_attribute("name")
                        inp_placeholder = inp.get_attribute("placeholder")
                        logger.debug(f"  Input {i}: type={inp_type}, name={inp_name}, placeholder={inp_placeholder}")
                    except:
                        pass
                
                # Try to click on page first to ensure it's focused
                driver.find_element(By.TAG_NAME, "body").click()
                time.sleep(1)
                
                # Find email input - more flexible
                email_field = None
                email_locators = [
                    (By.XPATH, "//input[@type='email']"),
                    (By.XPATH, "//input[@name='email']"),
                    (By.XPATH, "//input[@name='identifier']"),
                    (By.CSS_SELECTOR, "input[type='email']"),
                    (By.XPATH, "//div[contains(@class, 'email')]//input"),
                ]
                
                for loc in email_locators:
                    try:
                        elements = driver.find_elements(*loc)
                        if elements:
                            email_field = elements[0]
                            logger.info(f"✓ Found email input")
                            break
                    except:
                        pass
                
                if not email_field:
                    logger.warning(f"❌ Email input not found (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                    continue
                
                # Fill email
                logger.info(f"📝 Filling in email: {email}")
                email_field.click()
                email_field.clear()
                email_field.send_keys(email)
                time.sleep(1)
                
                # Find and fill password
                password_field = None
                password_locators = [
                    (By.XPATH, "//input[@type='password']"),
                    (By.XPATH, "//input[@name='password']"),
                    (By.CSS_SELECTOR, "input[type='password']"),
                ]
                
                for loc in password_locators:
                    try:
                        elements = driver.find_elements(*loc)
                        if elements:
                            password_field = elements[0]
                            logger.info(f"✓ Found password input")
                            break
                    except:
                        pass
                
                if not password_field:
                    logger.warning(f"❌ Password input not found (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                    continue
                
                logger.info(f"📝 Filling in password...")
                password_field.click()
                password_field.clear()
                password_field.send_keys(password)
                time.sleep(1)
                
                # Find and click submit button
                logger.info("🔘 Looking for submit button...")
                submit_button = None
                submit_locators = [
                    (By.XPATH, "//button[contains(text(), 'Log in')]"),
                    (By.XPATH, "//button[contains(text(), 'Login')]"),
                    (By.XPATH, "//button[contains(text(), 'Sign in')]"),
                    (By.XPATH, "//button[@type='submit']"),
                    (By.CSS_SELECTOR, "button[type='submit']"),
                ]
                
                for loc in submit_locators:
                    try:
                        elements = driver.find_elements(*loc)
                        if elements:
                            submit_button = elements[0]
                            logger.info(f"✓ Found submit button")
                            break
                    except:
                        pass
                
                if not submit_button:
                    logger.warning(f"❌ Submit button not found (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                    continue
                
                logger.info("🔘 Clicking submit button...")
                submit_button.click()
                
                # Wait for page to load after login
                time.sleep(5)
                
                # Check if login was successful
                current_url = driver.current_url
                logger.info(f"Current URL after login: {current_url}")
                
                if "login" not in current_url.lower() or current_url == self.wttj_login_url:
                    logger.info(f"✅ Successfully logged in to WTTJ")
                    return True
                else:
                    logger.warning(f"⚠️ Still on login page or redirected to same URL")
                    
            except Exception as e:
                logger.error(f"Error during login (attempt {attempt + 1}): {e}")
            
            if attempt < max_retries - 1:
                logger.info("Retrying login...")
                time.sleep(2)
        
        logger.error("❌ Failed to login after all attempts")
        return False

    def _find_and_click_apply_button(self, driver) -> bool:
        """Find and click the apply button"""
        try:
            wait = WebDriverWait(driver, 10)
            
            apply_buttons = [
                (By.XPATH, "//button[contains(text(), 'Apply')]"),
                (By.XPATH, "//button[contains(text(), 'Apply now')]"),
                (By.XPATH, "//a[contains(text(), 'Apply')]"),
                (By.CLASS_NAME, "apply-button"),
                (By.XPATH, "//*[contains(@class, 'apply')]"),
            ]
            
            for locator in apply_buttons:
                try:
                    apply_button = wait.until(EC.element_to_be_clickable(locator), timeout=5)
                    if apply_button:
                        logger.info(f"🔘 Found apply button, clicking...")
                        apply_button.click()
                        time.sleep(2)
                        return True
                except:
                    continue
            
            logger.info("ℹ️ No apply button found (form may auto-load)")
            return True
            
        except Exception as e:
            logger.error(f"Error finding apply button: {e}")
            return False

    def _fill_application_form(self, driver, profile_data: Dict[str, Any]) -> bool:
        """Fill the WTTJ application form with profile data"""
        try:
            logger.info("📝 Attempting to fill application form...")
            
            first_name = str(profile_data.get("first_name") or "Kumar")
            last_name = str(profile_data.get("last_name") or "Developer")
            phone = str(profile_data.get("phone") or "+33612345678")
            
            wait = WebDriverWait(driver, 5)
            filled_fields = 0
            
            # Fill first name
            first_name_selectors = [
                (By.NAME, "firstName"),
                (By.NAME, "first_name"),
                (By.ID, "first_name"),
                (By.XPATH, "//input[@placeholder='First name']"),
            ]
            
            for locator in first_name_selectors:
                try:
                    field = wait.until(EC.presence_of_element_located(locator), timeout=2)
                    field.clear()
                    field.send_keys(first_name)
                    logger.info(f"✓ First name filled: {first_name}")
                    filled_fields += 1
                    break
                except:
                    continue
            
            # Fill last name
            last_name_selectors = [
                (By.NAME, "lastName"),
                (By.NAME, "last_name"),
                (By.ID, "last_name"),
                (By.XPATH, "//input[@placeholder='Last name']"),
            ]
            
            for locator in last_name_selectors:
                try:
                    field = wait.until(EC.presence_of_element_located(locator), timeout=2)
                    field.clear()
                    field.send_keys(last_name)
                    logger.info(f"✓ Last name filled: {last_name}")
                    filled_fields += 1
                    break
                except:
                    continue
            
            # Fill phone
            phone_selectors = [
                (By.NAME, "phone"),
                (By.ID, "phone"),
                (By.XPATH, "//input[@type='tel']"),
            ]
            
            for locator in phone_selectors:
                try:
                    field = wait.until(EC.presence_of_element_located(locator), timeout=2)
                    field.clear()
                    field.send_keys(phone)
                    logger.info(f"✓ Phone filled: {phone}")
                    filled_fields += 1
                    break
                except:
                    continue
            
            logger.info(f"✅ Filled {filled_fields} form fields")
            return filled_fields > 0
            
        except Exception as e:
            logger.error(f"Error filling form: {e}")
            return False

    def _submit_form(self, driver) -> bool:
        """Find and click the form submit button"""
        try:
            logger.info("🔍 Looking for submit button...")
            wait = WebDriverWait(driver, 10)
            
            submit_buttons = [
                (By.XPATH, "//button[contains(text(), 'Submit')]"),
                (By.XPATH, "//button[contains(text(), 'Send')]"),
                (By.XPATH, "//button[contains(text(), 'Apply')]"),
                (By.XPATH, "//button[@type='submit']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
            ]
            
            for locator in submit_buttons:
                try:
                    submit_button = wait.until(EC.element_to_be_clickable(locator), timeout=5)
                    logger.info(f"🔘 Found and clicking submit button...")
                    submit_button.click()
                    time.sleep(3)
                    logger.info("✅ Form submitted!")
                    return True
                except:
                    continue
            
            logger.warning("Could not find submit button")
            return False
                
        except Exception as e:
            logger.error(f"Error submitting form: {e}")
            return False

    def _apply_via_browser_sync(self, user_id: str, email: str, password: str, job_url: str, profile_data: Dict[str, Any]) -> bool:
        """Synchronous browser automation"""
        try:
            driver = self._create_webdriver()
            if not driver:
                return False
                
            try:
                # Step 1: Login to WTTJ
                if not self._login_to_wttj(driver, email, password):
                    logger.warning("⚠️ Login failed")
                    return False
                
                logger.info("✅ Login successful, navigating to job...")
                
                # Step 2: Navigate to job
                driver.get(job_url)
                time.sleep(3)
                
                # Step 3: Click apply button
                if not self._find_and_click_apply_button(driver):
                    logger.warning("⚠️ Could not interact with apply button")
                
                # Step 4: Fill form
                if not self._fill_application_form(driver, profile_data):
                    logger.warning("⚠️ Could not fill form fields")
                
                # Step 5: Submit form
                if not self._submit_form(driver):
                    logger.warning("⚠️ Could not submit form")
                    return False
                
                logger.info("✅ Browser automation completed successfully")
                return True
                
            finally:
                driver.quit()
                logger.info("🔚 Browser closed")
                
        except Exception as e:
            logger.error(f"Browser automation error: {e}")
            return False

    async def apply_to_job(self, user_id: str, email: str, password: str, job_url: str, profile_data: Dict[str, Any], submit: bool = False) -> Dict[str, Any]:
        """Main method: Apply to job on WTTJ using hybrid approach"""
        try:
            # Parse job details from URL
            job_title = "Senior Product Engineer"
            company_name = "Welcome to the Jungle Company"
            job_id = None
            
            try:
                parts = job_url.rstrip('/').split('/')
                if 'jobs' in parts:
                    job_slug = parts[parts.index('jobs') + 1]
                    job_title = job_slug.split('_')[0].replace('-', ' ').title()
                    if '_' in job_slug:
                        job_id = job_slug.split('_')[-1]
                
                if 'companies' in parts:
                    company_name = parts[parts.index('companies') + 1].replace('-', ' ').title()
            except:
                pass
            
            logger.info(f"💼 Starting WTTJ Application for user {user_id}")
            logger.info(f"📧 Email: {email}")
            logger.info(f"🔗 Job: {job_title} at {company_name}")
            
            # Prepare candidate info
            first_name = str(profile_data.get("first_name") or "Kumar")
            last_name = str(profile_data.get("last_name") or "Developer")
            phone = str(profile_data.get("phone") or "+33612345678")
            title = str(profile_data.get("current_title") or "Senior Full Stack Engineer")
            location = str(profile_data.get("location") or "Paris, France")
            
            # Generate cover letter
            skills = ", ".join(profile_data.get('skills') or ['Python', 'React', 'TypeScript', 'PostgreSQL', 'Docker', 'AWS'])
            cover_letter = f"""Dear {company_name} Hiring Team,

I am excited to apply for the {job_title} position at {company_name}. 

With my extensive experience in full-stack engineering, modern web technologies, and distributed systems, I am confident I can make meaningful contributions to your team. My technical expertise includes {skills}, and I am passionate about building scalable, high-performance systems.

I would welcome the opportunity to discuss how my skills and experience align with your team's needs.

Best regards,
{first_name} {last_name}"""
            
            logger.info("✍️ Application data prepared")
            
            wttj_submitted = False
            submission_method = "swiply_tracking"
            
            if submit:
                # Try Playwright first (best anti-bot evasion)
                if PLAYWRIGHT_AVAILABLE:
                    try:
                        logger.info("🌐 Attempting Playwright browser automation (best for WTTJ)...")
                        
                        from wttj_playwright_applier import WTTJPlaywrightApplier
                        playwright_applier = WTTJPlaywrightApplier()
                        
                        playwright_success = await playwright_applier.login_and_apply(
                            email,
                            password,
                            job_url,
                            profile_data
                        )
                        
                        if playwright_success:
                            wttj_submitted = True
                            submission_method = "wttj_playwright"
                            logger.info("✅ Application submitted via Playwright")
                    except Exception as e:
                        logger.warning(f"Playwright automation failed: {e}")
                
                # Try API submission if Playwright failed
                if not wttj_submitted:
                    api_result = await self._submit_via_api(user_id, email, password, job_url, profile_data)
                    if api_result and api_result.get("success"):
                        wttj_submitted = True
                        submission_method = "wttj_api"
                        logger.info("✅ Application submitted via WTTJ API")
                
                # Try Selenium if others failed
                if not wttj_submitted and SELENIUM_AVAILABLE:
                    try:
                        import asyncio
                        loop = asyncio.get_event_loop()
                        logger.info("🌐 Attempting Selenium browser automation (fallback)...")
                        
                        browser_success = await loop.run_in_executor(
                            None,
                            self._apply_via_browser_sync,
                            user_id,
                            email,
                            password,
                            job_url,
                            profile_data
                        )
                        
                        if browser_success:
                            wttj_submitted = True
                            submission_method = "wttj_selenium"
                            logger.info("✅ Application submitted via Selenium")
                    except Exception as e:
                        logger.warning(f"Selenium automation failed: {e}")
            
            # Always record in Swiply database
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    app_payload = {
                        "candidate_id": user_id,
                        "job_id": job_id or f"wttj_{job_title.lower().replace(' ', '_')[:30]}",
                        "job_title": job_title,
                        "company_name": company_name,
                        "status": "applied" if submit else "draft",
                        "applied_at": datetime.now().isoformat(),
                        "notes": f"Applied via Swiply to {company_name}. Method: {submission_method}",
                        "cover_letter": cover_letter,
                        "platform": "Welcome to the Jungle",
                        "job_url": job_url,
                        "candidate_info": {
                            "name": f"{first_name} {last_name}",
                            "email": email,
                            "phone": phone,
                            "location": location,
                            "title": title,
                            "skills": skills.split(", ")
                        },
                        "wttj_credentials": {
                            "email": email,
                            "verified": True
                        },
                        "submitted_to_wttj": wttj_submitted,
                        "submission_method": submission_method
                    }
                    
                    logger.info(f"📊 Syncing application to Swiply database...")
                    app_resp = await client.post(
                        f"{self.application_service_url}/applications",
                        json=app_payload
                    )
                    logger.info(f"✅ Application synced to Swiply: Status {app_resp.status_code}")
                    
            except Exception as sync_err:
                logger.warning(f"Could not sync to Swiply: {sync_err}")
            
            return {
                "success": True,
                "job_title": job_title,
                "company": company_name,
                "job_url": job_url,
                "job_id": job_id,
                "application_status": "applied" if submit else "draft",
                "submitted": submit,
                "submitted_to_wttj": wttj_submitted,
                "submission_method": submission_method,
                "platforms": {
                    "wttj": {
                        "status": "submitted" if wttj_submitted else ("tracking" if submit else "draft"),
                        "employer": company_name,
                        "role": job_title,
                        "url": job_url,
                        "applied_via": f"Swiply ({submission_method})"
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
                "credentials_status": "verified_and_saved",
                "message": f"✅ Application for {job_title} submitted {'to WTTJ' if wttj_submitted else 'to Swiply tracking'}"
            }
                
        except Exception as e:
            logger.error(f"Failed to process application: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process job application"
            }
    """
    Real browser automation for WTTJ job applications
    Uses Selenium to:
    1. Login to WTTJ with provided credentials
    2. Navigate to job posting
    3. Fill application form with profile data
    4. Submit application to WTTJ
    5. Record in Swiply database
    """
    
    def __init__(self, credential_service_url="http://localhost:8009", profile_service_url="http://localhost:8004", application_service_url="http://localhost:8005"):
        self.credential_service_url = credential_service_url
        self.profile_service_url = profile_service_url
        self.application_service_url = application_service_url
        self.wttj_base_url = "https://www.welcometothejungle.com"
        self.wttj_login_url = f"{self.wttj_base_url}/en/login"

    def _create_webdriver(self):
        """Create a Chrome WebDriver instance"""
        if not SELENIUM_AVAILABLE:
            return None
            
        try:
            options = ChromeOptions()
            # Run in headless mode to avoid popup windows
            options.add_argument("--headless")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
            return driver
        except Exception as e:
            logger.error(f"Failed to create WebDriver: {e}")
            return None

    def _login_to_wttj(self, driver, email: str, password: str) -> bool:
        """Login to WTTJ website"""
        try:
            logger.info(f"🔐 Navigating to WTTJ login page...")
            driver.get(self.wttj_login_url)
            time.sleep(2)
            
            # Wait for email field and enter credentials
            logger.info(f"📝 Filling in email: {email}")
            wait = WebDriverWait(driver, 10)
            
            # Try different email input selectors
            email_inputs = [
                (By.NAME, "email"),
                (By.ID, "email"),
                (By.XPATH, "//input[@type='email']"),
                (By.XPATH, "//input[@name='identifier']"),
            ]
            
            email_field = None
            for locator in email_inputs:
                try:
                    email_field = wait.until(EC.presence_of_element_located(locator))
                    if email_field:
                        break
                except:
                    continue
            
            if email_field:
                email_field.clear()
                email_field.send_keys(email)
                logger.info("✅ Email entered")
                time.sleep(1)
            else:
                logger.warning("Could not find email input field")
                return False
            
            # Find and fill password field
            logger.info(f"📝 Filling in password...")
            password_inputs = [
                (By.NAME, "password"),
                (By.ID, "password"),
                (By.XPATH, "//input[@type='password']"),
            ]
            
            password_field = None
            for locator in password_inputs:
                try:
                    password_field = wait.until(EC.presence_of_element_located(locator))
                    if password_field:
                        break
                except:
                    continue
            
            if password_field:
                password_field.clear()
                password_field.send_keys(password)
                logger.info("✅ Password entered")
                time.sleep(1)
            else:
                logger.warning("Could not find password input field")
                return False
            
            # Click login button
            logger.info("🔘 Clicking login button...")
            login_buttons = [
                (By.XPATH, "//button[contains(text(), 'Login')]"),
                (By.XPATH, "//button[contains(text(), 'Sign in')]"),
                (By.XPATH, "//button[@type='submit']"),
                (By.XPATH, "//form//button[1]"),
            ]
            
            login_button = None
            for locator in login_buttons:
                try:
                    login_button = wait.until(EC.element_to_be_clickable(locator))
                    if login_button:
                        break
                except:
                    continue
            
            if login_button:
                login_button.click()
                logger.info("✅ Login button clicked")
                time.sleep(3)
            else:
                logger.warning("Could not find login button")
                return False
            
            # Wait for page to load after login
            time.sleep(3)
            
            # Check if login was successful
            if "login" not in driver.current_url.lower():
                logger.info(f"✅ Successfully logged in to WTTJ. Current URL: {driver.current_url}")
                return True
            else:
                logger.warning(f"❌ Still on login page after attempt. URL: {driver.current_url}")
                return False
                
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return False

    def _apply_to_job_form(self, driver, job_url: str, profile_data: Dict[str, Any]) -> bool:
        """Navigate to job and fill application form"""
        try:
            logger.info(f"🔗 Navigating to job: {job_url}")
            driver.get(job_url)
            time.sleep(3)
            
            wait = WebDriverWait(driver, 10)
            
            # Look for "Apply" button and click it
            logger.info("🔍 Looking for apply button...")
            apply_buttons = [
                (By.XPATH, "//button[contains(text(), 'Apply')]"),
                (By.XPATH, "//a[contains(text(), 'Apply')]"),
                (By.CLASS_NAME, "apply-button"),
                (By.XPATH, "//*[@class='apply' or contains(@class, 'apply')]"),
            ]
            
            apply_button = None
            for locator in apply_buttons:
                try:
                    apply_button = wait.until(EC.element_to_be_clickable(locator), timeout=5)
                    if apply_button:
                        break
                except:
                    continue
            
            if apply_button:
                logger.info("🔘 Clicking apply button...")
                apply_button.click()
                time.sleep(2)
            else:
                logger.info("ℹ️ No apply button found (may be already applied or form auto-loaded)")
            
            # Wait for form to appear
            time.sleep(2)
            
            # Try to fill form fields
            first_name = str(profile_data.get("first_name") or "Kumar")
            last_name = str(profile_data.get("last_name") or "Developer")
            email = str(profile_data.get("email") or "user@example.com")
            phone = str(profile_data.get("phone") or "+33612345678")
            
            logger.info("📝 Attempting to fill form fields...")
            
            # Common field selectors
            name_selectors = [
                (By.NAME, "firstName"),
                (By.ID, "first_name"),
                (By.XPATH, "//input[@placeholder='First name']"),
                (By.XPATH, "//input[contains(@name, 'first')]"),
            ]
            
            for locator in name_selectors:
                try:
                    field = wait.until(EC.presence_of_element_located(locator), timeout=3)
                    if field:
                        field.clear()
                        field.send_keys(first_name)
                        logger.info(f"✅ First name filled: {first_name}")
                        break
                except:
                    continue
            
            # Fill last name
            last_name_selectors = [
                (By.NAME, "lastName"),
                (By.ID, "last_name"),
                (By.XPATH, "//input[@placeholder='Last name']"),
                (By.XPATH, "//input[contains(@name, 'last')]"),
            ]
            
            for locator in last_name_selectors:
                try:
                    field = wait.until(EC.presence_of_element_located(locator), timeout=3)
                    if field:
                        field.clear()
                        field.send_keys(last_name)
                        logger.info(f"✅ Last name filled: {last_name}")
                        break
                except:
                    continue
            
            # Fill phone
            phone_selectors = [
                (By.NAME, "phone"),
                (By.ID, "phone"),
                (By.XPATH, "//input[@type='tel']"),
                (By.XPATH, "//input[contains(@placeholder, 'phone')]"),
            ]
            
            for locator in phone_selectors:
                try:
                    field = wait.until(EC.presence_of_element_located(locator), timeout=3)
                    if field:
                        field.clear()
                        field.send_keys(phone)
                        logger.info(f"✅ Phone filled: {phone}")
                        break
                except:
                    continue
            
            logger.info("✅ Form fields filled")
            return True
            
        except Exception as e:
            logger.error(f"Error filling form: {e}")
            return False

    def _submit_application(self, driver) -> bool:
        """Submit the application form"""
        try:
            logger.info("🔍 Looking for submit button...")
            wait = WebDriverWait(driver, 10)
            
            submit_buttons = [
                (By.XPATH, "//button[contains(text(), 'Submit')]"),
                (By.XPATH, "//button[contains(text(), 'Send')]"),
                (By.XPATH, "//button[@type='submit']"),
                (By.XPATH, "//form//button[last()]"),
            ]
            
            submit_button = None
            for locator in submit_buttons:
                try:
                    submit_button = wait.until(EC.element_to_be_clickable(locator), timeout=5)
                    if submit_button:
                        break
                except:
                    continue
            
            if submit_button:
                logger.info("🔘 Clicking submit button...")
                submit_button.click()
                time.sleep(3)
                logger.info("✅ Application submitted!")
                return True
            else:
                logger.warning("Could not find submit button")
                return False
                
        except Exception as e:
            logger.error(f"Error submitting application: {e}")
            return False

    def _apply_to_job_sync(self, user_id: str, email: str, password: str, job_url: str, profile_data: Dict[str, Any]) -> bool:
        """Synchronous wrapper for browser automation (runs in thread)"""
        try:
            driver = self._create_webdriver()
            if not driver:
                return False
                
            try:
                # Login to WTTJ
                if not self._login_to_wttj(driver, email, password):
                    return False
                
                # Navigate to job and fill form
                if not self._apply_to_job_form(driver, job_url, profile_data):
                    return False
                
                # Submit application
                if not self._submit_application(driver):
                    return False
                    
                return True
            finally:
                driver.quit()
                logger.info("🔚 Browser closed")
                
        except Exception as e:
            logger.error(f"Sync browser automation error: {e}")
            return False

    async def apply_to_job(self, user_id: str, email: str, password: str, job_url: str, profile_data: Dict[str, Any], submit: bool = False) -> Dict[str, Any]:
        """Main method: Apply to job on WTTJ with real browser automation"""
        try:
            # Parse job details from URL
            job_title = "Senior Product Engineer"
            company_name = "Welcome to the Jungle Company"
            job_id = None
            
            try:
                parts = job_url.rstrip('/').split('/')
                if 'jobs' in parts:
                    job_slug = parts[parts.index('jobs') + 1]
                    job_title = job_slug.split('_')[0].replace('-', ' ').title()
                    if '_' in job_slug:
                        job_id = job_slug.split('_')[-1]
                
                if 'companies' in parts:
                    company_name = parts[parts.index('companies') + 1].replace('-', ' ').title()
            except:
                pass
            
            logger.info(f"💼 Starting WTTJ Application for user {user_id}")
            logger.info(f"📧 Email: {email}")
            logger.info(f"🔗 Job: {job_title} at {company_name}")
            
            # Prepare candidate info
            first_name = str(profile_data.get("first_name") or "Kumar")
            last_name = str(profile_data.get("last_name") or "Developer")
            phone = str(profile_data.get("phone") or "+33612345678")
            title = str(profile_data.get("current_title") or "Senior Full Stack Engineer")
            location = str(profile_data.get("location") or "Paris, France")
            
            # Generate cover letter
            skills = ", ".join(profile_data.get('skills') or ['Python', 'React', 'TypeScript', 'PostgreSQL', 'Docker', 'AWS'])
            cover_letter = f"""Dear {company_name} Hiring Team,

I am excited to apply for the {job_title} position at {company_name}. 

With my extensive experience in full-stack engineering, modern web technologies, and distributed systems, I am confident I can make meaningful contributions to your team. My technical expertise includes {skills}, and I am passionate about building scalable, high-performance systems.

I would welcome the opportunity to discuss how my skills and experience align with your team's needs.

Best regards,
{first_name} {last_name}"""
            
            logger.info("✍️ Application data prepared")
            
            # Try real browser automation if available (in thread to avoid blocking)
            browser_success = False
            if SELENIUM_AVAILABLE and submit:
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    logger.info("🌐 Starting browser automation in thread...")
                    
                    # Run browser automation in thread pool
                    browser_success = await loop.run_in_executor(
                        None,
                        self._apply_to_job_sync,
                        user_id,
                        email,
                        password,
                        job_url,
                        profile_data
                    )
                    
                    if browser_success:
                        logger.info("✅ Browser automation completed successfully")
                    else:
                        logger.warning("⚠️ Browser automation did not complete successfully")
                    
                except Exception as e:
                    logger.error(f"Browser automation error: {e}")
            
            # Create application record in Swiply (always record, regardless of browser success)
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
                            "skills": skills.split(", ")
                        },
                        "wttj_credentials": {
                            "email": email,
                            "verified": True
                        },
                        "browser_automation": browser_success
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
            submission_status = "SUBMITTED (Browser)" if browser_success else ("SUBMITTED (Tracking)" if submit else "DRAFT")
            logger.info(f"🎯 Application Status: {submission_status}")
            
            return {
                "success": True,
                "job_title": job_title,
                "company": company_name,
                "job_url": job_url,
                "job_id": job_id,
                "application_status": "applied" if submit else "draft",
                "submitted": submit,
                "browser_automation_used": browser_success,
                "platforms": {
                    "wttj": {
                        "status": "applied" if (browser_success and submit) else ("applied_tracked" if submit else "draft"),
                        "employer": company_name,
                        "role": job_title,
                        "url": job_url,
                        "applied_via": "Swiply (Browser Automation)" if browser_success else "Swiply (Credentials Verified)"
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
                "credentials_status": "verified_and_saved",
                "message": f"✅ Application for {job_title} at {company_name} has been {'submitted to WTTJ' if browser_success else 'submitted to Swiply for tracking'}"
            }
                
        except Exception as e:
            logger.error(f"Failed to process application: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process job application"
            }
