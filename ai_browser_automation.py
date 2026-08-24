#!/usr/bin/env python3
"""
AI-Powered WTTJ Account Creation
Uses OpenAI GPT-5 to understand and interact with the page
"""
import asyncio
import time
import uuid
import base64
import os
from playwright.async_api import async_playwright, Page, Browser
from openai import OpenAI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "your-openai-api-key"))


class AIBrowserAutomation:
    """AI-powered browser automation using GPT-5"""
    
    def __init__(self):
        self.page: Page = None
        self.browser: Browser = None
        self.context = None
        
    async def setup_browser(self):
        """Setup Playwright browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=[
                '--window-size=1280,900',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            java_script_enabled=True
        )
        # Mask automation
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)
        self.page = await self.context.new_page()
        self.page.set_default_timeout(60000)
    
    async def take_screenshot(self, save_path="screenshot.png"):
        """Take screenshot and return base64 encoded image"""
        screenshot_bytes = await self.page.screenshot(path=save_path)
        return base64.b64encode(screenshot_bytes).decode('utf-8')
    
    async def ask_ai_about_page(self, screenshot_base64, question):
        """Ask GPT-5 about the page - SYNC call wrapped for async"""
        def _sync_call():
            try:
                response = client.chat.completions.create(
                    model="gpt-5",  # GPT-5 with vision
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": question
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{screenshot_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=500
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                logger.error(f"AI query error: {e}")
                return None
        
        # Run sync OpenAI call in thread pool
        return await asyncio.to_thread(_sync_call)
    
    async def ai_find_and_click_button(self):
        """Use AI to find and click the submit button"""
        try:
            logger.info("AI analyzing page to find submit button...")
            
            # Take screenshot
            screenshot = await self.take_screenshot("wttj_page.png")
            
            # Ask AI where the button is
            question = """
            You are looking at a WTTJ (Welcome to the Jungle) signup page.
            
            Task: Find the submit/signup button on this page.
            
            Please provide:
            1. Exact text on the button
            2. Button location (approximate x, y coordinates from top-left, or description like "bottom center")
            3. Any issues you see (disabled, validation errors, missing fields)
            4. Suggestions to make the button clickable
            
            Be specific and concise.
            """
            
            ai_response = await self.ask_ai_about_page(screenshot, question)
            logger.info(f"AI Response:\n{ai_response}")
            
            # Ask AI for the exact selector
            selector_question = """
            Based on this WTTJ signup page screenshot, what is the best CSS selector or XPath to click the submit button?
            
            Provide ONLY the selector, in this format:
            CSS: button[type="submit"]
            or
            XPATH: //button[contains(text(), 'Sign up')]
            
            Choose the most reliable selector.
            """
            
            selector_response = await self.ask_ai_about_page(screenshot, selector_question)
            logger.info(f"AI Selector: {selector_response}")
            
            # Parse selector from AI response
            selector = None
            selector_type = None
            
            if selector_response and "CSS:" in selector_response:
                selector = selector_response.split("CSS:")[1].strip().split("\n")[0]
                selector_type = "css"
            elif selector_response and "XPATH:" in selector_response:
                selector = selector_response.split("XPATH:")[1].strip().split("\n")[0]
                selector_type = "xpath"
            
            if selector:
                logger.info(f"Attempting to click using {selector_type}: {selector}")
                
                # Find element with Playwright
                if selector_type == "css":
                    button = self.page.locator(selector).first
                else:
                    button = self.page.locator(f"xpath={selector}").first
                
                # Wait for element to be visible
                await button.wait_for(state="visible", timeout=10000)
                
                # Scroll to button
                await button.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                
                # Try multiple click strategies
                try:
                    await button.click(timeout=5000)
                    logger.info("✓ Clicked (direct)")
                    return True
                except:
                    try:
                        await button.click(force=True)
                        logger.info("✓ Clicked (force)")
                        return True
                    except:
                        try:
                            await button.evaluate("el => el.click()")
                            logger.info("✓ Clicked (JavaScript)")
                            return True
                        except:
                            logger.error("All click methods failed")
                            return False
            else:
                logger.error("Could not parse selector from AI response")
                return False
                
        except Exception as e:
            logger.error(f"AI button click error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def create_account(self, email, password, first_name, last_name):
        """Create WTTJ account with AI assistance"""
        try:
            await self.setup_browser()
            
            logger.info(f"Creating WTTJ account for {email}")
            
            # Navigate to signup
            logger.info("[1/6] Loading signup page...")
            await self.page.goto('https://www.welcometothejungle.com/en/authenticate/signup', wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(5)
            
            # Fill fields (standard automation)
            logger.info("[2/6] Filling email...")
            email_input = self.page.locator('input[type="email"]').first
            await email_input.clear()
            await email_input.fill(email)
            await asyncio.sleep(1)
            
            logger.info("[3/6] Filling password...")
            pwd_inputs = self.page.locator('input[type="password"]')
            count = await pwd_inputs.count()
            for i in range(count):
                pwd = pwd_inputs.nth(i)
                await pwd.clear()
                await pwd.fill(password)
                await asyncio.sleep(0.5)
            
            logger.info("[4/6] Filling name...")
            try:
                # Try to find first name field
                first_selectors = ['input[name*="first"]', 'input[placeholder*="First"]', 'input[placeholder*="Prénom"]']
                for selector in first_selectors:
                    try:
                        first_input = self.page.locator(selector).first
                        if await first_input.is_visible():
                            await first_input.clear()
                            await first_input.fill(first_name)
                            logger.info(f"  ✓ First name: {first_name}")
                            break
                    except:
                        continue
                
                # Try to find last name field
                last_selectors = ['input[name*="last"]', 'input[placeholder*="Last"]', 'input[placeholder*="Nom"]']
                for selector in last_selectors:
                    try:
                        last_input = self.page.locator(selector).first
                        if await last_input.is_visible():
                            await last_input.clear()
                            await last_input.fill(last_name)
                            logger.info(f"  ✓ Last name: {last_name}")
                            break
                    except:
                        continue
            except:
                pass
            
            logger.info("[5/6] Checking checkboxes...")
            checkboxes = self.page.locator('input[type="checkbox"]')
            count = await checkboxes.count()
            for i in range(count):
                cb = checkboxes.nth(i)
                try:
                    if await cb.is_visible() and not await cb.is_checked():
                        await cb.click(force=True)
                        await asyncio.sleep(0.3)
                except:
                    pass
            
            await asyncio.sleep(2)
            
            # Use AI to click submit
            logger.info("[6/6] Using AI to find and click submit button...")
            success = await self.ai_find_and_click_button()
            
            if success:
                await asyncio.sleep(5)
                
                # Check if account created
                current_url = self.page.url
                if 'authenticate/signup' not in current_url:
                    logger.info(f"✅ Account created! URL: {current_url}")
                    return {
                        "success": True,
                        "email": email,
                        "password": password,
                        "status": "created",
                        "url": current_url
                    }
                else:
                    # Ask AI what went wrong
                    screenshot = await self.take_screenshot("after_click.png")
                    error_question = "What error or issue do you see on this page? Is there a validation error or message?"
                    error_analysis = await self.ask_ai_about_page(screenshot, error_question)
                    
                    logger.warning(f"Still on signup page. AI analysis: {error_analysis}")
                    
                    return {
                        "success": False,
                        "error": "Form submission failed",
                        "ai_analysis": error_analysis
                    }
            else:
                return {
                    "success": False,
                    "error": "AI could not click button"
                }
                
        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            await asyncio.sleep(10)  # Keep browser open for review
            if self.browser:
                await self.browser.close()


async def main():
    """Test AI browser automation"""
    timestamp = int(time.time())
    email = f"ai_test_{timestamp}@gmail.com"
    password = f"Wttj2026!!${uuid.uuid4().hex[:6]}"
    
    print("\n" + "="*80)
    print("AI-POWERED WTTJ ACCOUNT CREATION (Playwright)")
    print("="*80)
    print(f"\nEmail: {email}")
    print(f"Password: {password}")
    print("\nUsing OpenAI GPT-5 to understand and interact with the page...")
    print("="*80 + "\n")
    
    ai_browser = AIBrowserAutomation()
    result = await ai_browser.create_account(
        email=email,
        password=password,
        first_name="AI",
        last_name="Test"
    )
    
    print("\n" + "="*80)
    print("RESULT")
    print("="*80)
    if result["success"]:
        print(f"✅ SUCCESS!")
        print(f"   Email: {result['email']}")
        print(f"   Password: {result['password']}")
        print(f"   URL: {result.get('url')}")
    else:
        print(f"❌ FAILED")
        print(f"   Error: {result.get('error')}")
        if result.get('ai_analysis'):
            print(f"   AI Analysis: {result['ai_analysis']}")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
