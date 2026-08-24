"""
Browser Controller with Remote Control
Allows Swiply dashboard to control WTTJ browser automation
"""
import asyncio
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import re
import logging

logger = logging.getLogger(__name__)


class RemoteControlledBrowser:
    """Browser that can be controlled remotely from Swiply dashboard"""
    
    def __init__(self):
        self.driver = None
        self.email = None
        self.password = None
        self.status = "idle"  # idle, filling, waiting_for_submit, submitting, success, error
        self.submit_requested = False
        
    def setup_driver(self):
        """Setup Chrome driver"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1280,900')
        
        self.driver = webdriver.Chrome(options=options)
        
    async def fill_signup_form(self, email: str, password: str, first_name: str, last_name: str):
        """Fill the WTTJ signup form and wait for user to trigger submit"""
        try:
            self.email = email
            self.password = password
            self.status = "filling"
            
            logger.info(f"🌐 Opening WTTJ signup for {email}")
            
            # Setup browser
            self.setup_driver()
            
            # Navigate to signup
            logger.info("[1/5] Loading signup page...")
            self.driver.get('https://www.welcometothejungle.com/en/authenticate/signup')
            await asyncio.sleep(3)
            
            # Fill email
            logger.info("[2/5] Filling email...")
            email_input = self.driver.find_element(By.CSS_SELECTOR, 'input[type="email"]')
            email_input.clear()
            email_input.send_keys(email)
            await asyncio.sleep(1)
            
            # Fill password
            logger.info("[3/5] Filling password...")
            password_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')
            for pwd_field in password_inputs:
                pwd_field.clear()
                pwd_field.send_keys(password)
                await asyncio.sleep(0.5)
            
            # Fill names
            logger.info("[4/5] Filling name...")
            clean_first = re.sub(r'[^a-zA-Z\s\-\']', '', first_name) or 'Alexandre'
            clean_last = re.sub(r'[^a-zA-Z\s\-\']', '', last_name) or 'Dupont'
            
            try:
                first_selectors = [
                    'input[name*="first"]',
                    'input[placeholder*="First"]',
                    'input[placeholder*="Prénom"]'
                ]
                
                for selector in first_selectors:
                    try:
                        name_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                        name_input.clear()
                        name_input.send_keys(clean_first)
                        logger.info(f"  ✓ First name: {clean_first}")
                        break
                    except:
                        continue
                
                last_selectors = [
                    'input[name*="last"]',
                    'input[placeholder*="Last"]',
                    'input[placeholder*="Nom"]'
                ]
                
                for selector in last_selectors:
                    try:
                        last_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                        last_input.clear()
                        last_input.send_keys(clean_last)
                        logger.info(f"  ✓ Last name: {clean_last}")
                        break
                    except:
                        continue
            except:
                pass
            
            # Check checkboxes
            try:
                checkboxes = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')
                for cb in checkboxes:
                    if not cb.is_selected():
                        self.driver.execute_script("arguments[0].click();", cb)
                        await asyncio.sleep(0.3)
            except:
                pass
            
            await asyncio.sleep(1)
            
            logger.info("[5/5] Form filled - waiting for submit trigger from dashboard...")
            self.status = "waiting_for_submit"
            
            # Wait for submit_requested flag or timeout
            max_wait = 300  # 5 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                if self.submit_requested:
                    logger.info("✓ Submit triggered from dashboard!")
                    break
                await asyncio.sleep(0.5)
            
            if not self.submit_requested:
                logger.warning("Timeout waiting for submit trigger")
                self.status = "error"
                return {
                    "success": False,
                    "error": "Timeout waiting for user to click submit button"
                }
            
            # Submit was requested - click the button
            return await self.click_submit_button()
            
        except Exception as e:
            logger.error(f"Error filling form: {e}")
            self.status = "error"
            return {
                "success": False,
                "error": str(e)
            }
    
    async def click_submit_button(self):
        """Click the submit button on WTTJ"""
        try:
            self.status = "submitting"
            logger.info("🔘 Clicking submit button...")
            
            # Find and click submit button
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            
            # Check if disabled
            if submit_btn.get_attribute('disabled'):
                logger.warning("Button is disabled - waiting for it to enable...")
                for i in range(20):
                    await asyncio.sleep(0.5)
                    if not submit_btn.get_attribute('disabled'):
                        break
            
            # Scroll to button
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
            await asyncio.sleep(1)
            
            # Try multiple click methods
            clicked = False
            
            # Method 1: Direct click
            try:
                submit_btn.click()
                clicked = True
                logger.info("✓ Clicked (direct)")
            except:
                pass
            
            # Method 2: JavaScript click
            if not clicked:
                try:
                    self.driver.execute_script("arguments[0].click();", submit_btn)
                    clicked = True
                    logger.info("✓ Clicked (JavaScript)")
                except:
                    pass
            
            # Method 3: ActionChains
            if not clicked:
                try:
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(self.driver)
                    actions.move_to_element(submit_btn).click().perform()
                    clicked = True
                    logger.info("✓ Clicked (ActionChains)")
                except:
                    pass
            
            if not clicked:
                logger.error("Failed to click submit button")
                self.status = "error"
                return {
                    "success": False,
                    "error": "Could not click submit button"
                }
            
            # Wait for navigation
            await asyncio.sleep(5)
            
            # Check if account created
            current_url = self.driver.current_url
            
            if 'authenticate/signup' not in current_url:
                logger.info(f"✅ Account created! Redirected to: {current_url}")
                self.status = "success"
                await asyncio.sleep(5)
                return {
                    "success": True,
                    "email": self.email,
                    "password": self.password,
                    "status": "created",
                    "url": current_url
                }
            else:
                logger.warning("Still on signup page after click")
                self.status = "error"
                return {
                    "success": False,
                    "error": "Form submission failed - still on signup page"
                }
                
        except Exception as e:
            logger.error(f"Error clicking submit: {e}")
            self.status = "error"
            return {
                "success": False,
                "error": str(e)
            }
    
    def trigger_submit(self):
        """Called from API endpoint when user clicks button in dashboard"""
        logger.info("📡 Received submit trigger from dashboard")
        self.submit_requested = True
    
    def get_status(self):
        """Get current status"""
        return {
            "status": self.status,
            "email": self.email,
            "submit_requested": self.submit_requested
        }
    
    def cleanup(self):
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass


# Global instance
browser_controller = RemoteControlledBrowser()
