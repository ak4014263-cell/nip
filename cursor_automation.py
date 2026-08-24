#!/usr/bin/env python3
"""
WTTJ Account Creator with Cursor-Based Automation
Uses visual cursor movement to identify and interact with fields
WITH HUMAN-LIKE BEHAVIOR: Random delays, natural movements, variability
"""
import asyncio
import time
import uuid
import re
import random
from playwright.async_api import async_playwright, Page, Browser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CursorWTTJAutomation:
    """Creates WTTJ accounts using cursor-based field identification"""
    
    def __init__(self):
        self.page: Page = None
        self.browser: Browser = None
        self.context = None
        
    async def setup_browser(self):
        """Setup Playwright browser with cursor tracking"""
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
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        """)
        self.page = await self.context.new_page()
        try:
            from playwright_stealth import stealth_async
            await stealth_async(self.page)
        except Exception as stealth_err:
            logger.debug(f"Stealth module note: {stealth_err}")
            
        self.page.set_default_timeout(60000)
        
        # Add cursor tracking visualization
        await self.page.add_init_script("""
            // Create cursor indicator
            const cursor = document.createElement('div');
            cursor.id = 'automation-cursor';
            cursor.style.cssText = `
                position: fixed;
                width: 20px;
                height: 20px;
                border: 3px solid #ff0000;
                border-radius: 50%;
                background: rgba(255, 0, 0, 0.3);
                pointer-events: none;
                z-index: 999999;
                transform: translate(-50%, -50%);
                transition: all 0.1s ease;
            `;
            document.body.appendChild(cursor);
            
            // Track mouse movements
            document.addEventListener('DOMContentLoaded', () => {
                document.addEventListener('mousemove', (e) => {
                    cursor.style.left = e.pageX + 'px';
                    cursor.style.top = e.pageY + 'px';
                });
            });
        """)
    
    async def human_delay(self, min_ms=100, max_ms=500):
        """Human-like random delay"""
        delay = random.uniform(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
    
    async def move_mouse_naturally(self, from_x, from_y, to_x, to_y, steps=20):
        """Move mouse in a natural curved path"""
        # Add slight randomness to the path
        for i in range(steps):
            progress = i / steps
            # Ease-in-out curve
            ease = progress * progress * (3 - 2 * progress)
            
            # Add random wobble
            wobble_x = random.uniform(-5, 5)
            wobble_y = random.uniform(-5, 5)
            
            x = from_x + (to_x - from_x) * ease + wobble_x
            y = from_y + (to_y - from_y) * ease + wobble_y
            
            await self.page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.01, 0.03))
    
    async def hover_and_highlight(self, element, label=""):
        """Move cursor to element and highlight it with human-like movement"""
        try:
            # Get current mouse position
            current_pos = await self.page.evaluate("() => ({x: window.lastMouseX || 0, y: window.lastMouseY || 0})")
            
            # Get element bounding box
            box = await element.bounding_box()
            if box:
                # Calculate center with slight randomness (humans don't click exact center)
                center_x = box['x'] + box['width'] / 2 + random.uniform(-5, 5)
                center_y = box['y'] + box['height'] / 2 + random.uniform(-5, 5)
                
                logger.info(f"  🖱️  Moving cursor naturally to {label} at ({int(center_x)}, {int(center_y)})")
                
                # Move cursor naturally
                await self.move_mouse_naturally(
                    current_pos['x'], current_pos['y'],
                    center_x, center_y
                )
                
                # Update last position
                await self.page.evaluate(f"() => {{ window.lastMouseX = {center_x}; window.lastMouseY = {center_y}; }}")
                
                # Human-like pause before highlight
                await self.human_delay(100, 300)
                
                # Highlight element
                await element.evaluate("""
                    el => {
                        el.style.outline = '3px solid #00ff00';
                        el.style.outlineOffset = '2px';
                        setTimeout(() => {
                            el.style.outline = '';
                            el.style.outlineOffset = '';
                        }, 1000);
                    }
                """)
                
                await self.human_delay(200, 500)
                return True
        except Exception as e:
            logger.warning(f"Could not hover over {label}: {e}")
            return False
    
    async def cursor_click_element(self, element, label=""):
        """Click element using cursor movement with human-like behavior"""
        try:
            # Hover first with natural movement
            await self.hover_and_highlight(element, label)
            
            # Human-like pause before click
            await self.human_delay(200, 600)
            
            # Get box again for click
            box = await element.bounding_box()
            if box:
                # Add slight randomness to click position
                center_x = box['x'] + box['width'] / 2 + random.uniform(-3, 3)
                center_y = box['y'] + box['height'] / 2 + random.uniform(-3, 3)
                
                # Visual feedback - show click animation
                await element.evaluate("""
                    el => {
                        el.style.transform = 'scale(0.95)';
                        setTimeout(() => {
                            el.style.transform = '';
                        }, 200);
                    }
                """)
                
                # Perform click at cursor position with slight delay
                await self.human_delay(50, 150)
                await self.page.mouse.click(center_x, center_y)
                logger.info(f"  ✓ Clicked {label}")
                
                # Human-like pause after click
                await self.human_delay(300, 700)
                return True
        except Exception as e:
            logger.warning(f"Could not click {label}: {e}")
            return False
    
    async def cursor_fill_field(self, element, value, label=""):
        """Fill field using cursor and typing with human-like behavior"""
        try:
            # Move cursor and click to focus
            await self.hover_and_highlight(element, label)
            
            # Human pause before clicking
            await self.human_delay(200, 500)
            
            await self.cursor_click_element(element, label)
            
            # Human pause after focus
            await self.human_delay(100, 300)
            
            # Clear field
            await element.clear()
            
            # Human-like typing with variable delays
            for char in value:
                await element.type(char, delay=random.randint(50, 150))
                # Occasionally pause longer (as if thinking)
                if random.random() < 0.1:  # 10% chance
                    await self.human_delay(200, 500)
            
            logger.info(f"  ✓ Filled {label}: {value}")
            
            # Human pause after typing
            await self.human_delay(300, 700)
            return True
        except Exception as e:
            logger.warning(f"Could not fill {label}: {e}")
            return False
    
    async def find_and_click_submit_with_cursor(self):
        """Find submit button using cursor exploration"""
        try:
            logger.info("\n🔍 Searching for submit button with cursor...")
            
            # Get all buttons
            all_buttons = await self.page.locator('button').all()
            
            logger.info(f"Found {len(all_buttons)} buttons on page")
            
            for idx, btn in enumerate(all_buttons):
                try:
                    # Check if visible
                    is_visible = await btn.is_visible()
                    if not is_visible:
                        continue
                    
                    # Get button text
                    text = await btn.inner_text()
                    text = text.strip().lower()
                    
                    # Check if it's a submit-like button
                    submit_keywords = ['submit', 'sign up', 'create', 'agree', 'register', 'continue', 'next']
                    is_submit = any(keyword in text for keyword in submit_keywords)
                    
                    if is_submit:
                        logger.info(f"\n✨ Found potential submit button #{idx+1}: '{text}'")
                        
                        # Get button attributes
                        btn_type = await btn.get_attribute('type')
                        is_disabled = await btn.get_attribute('disabled')
                        is_enabled = await btn.is_enabled()
                        
                        logger.info(f"   Type: {btn_type}")
                        logger.info(f"   Enabled: {is_enabled}")
                        logger.info(f"   Disabled attr: {is_disabled}")
                        
                        # Hover over button to show it
                        await self.hover_and_highlight(btn, f"Button: {text}")
                        
                        if is_enabled and not is_disabled:
                            logger.info(f"   ✓ Button is clickable!")
                            
                            # Scroll into view with cursor following
                            await btn.scroll_into_view_if_needed()
                            await self.human_delay(500, 1000)
                            
                            # Try to click with cursor - MULTIPLE ATTEMPTS WITH HUMAN BEHAVIOR
                            logger.info(f"\n🖱️  Attempting human-like button clicks...")
                            
                            # Method 1: Multiple cursor clicks with hover
                            try:
                                for attempt in range(3):
                                    logger.info(f"   Human-like click attempt {attempt + 1}/3...")
                                    
                                    # Hover over button
                                    await self.hover_and_highlight(btn, f"Submit: {text}")
                                    await self.human_delay(300, 700)
                                    
                                    # Click with human behavior
                                    clicked = await self.cursor_click_element(btn, f"Submit: {text}")
                                    if clicked:
                                        logger.info(f"   ✅ Clicked with cursor (attempt {attempt + 1})!")
                                        await self.human_delay(1000, 2000)
                                        
                                        # Check if navigation happened
                                        if 'authenticate/signup' not in self.page.url:
                                            logger.info("   ✅ Navigation detected!")
                                            return True
                            except Exception as e1:
                                logger.warning(f"   Cursor clicks failed: {e1}")
                            
                            # Method 2: Hover + direct click with delays
                            try:
                                for attempt in range(3):
                                    logger.info(f"   Hover+click attempt {attempt + 1}/3...")
                                    
                                    # Get box for hover
                                    box = await btn.bounding_box()
                                    if box:
                                        # Move to button with natural movement
                                        current_pos = await self.page.evaluate("() => ({x: window.lastMouseX || 0, y: window.lastMouseY || 0})")
                                        target_x = box['x'] + box['width'] / 2 + random.uniform(-5, 5)
                                        target_y = box['y'] + box['height'] / 2 + random.uniform(-5, 5)
                                        
                                        await self.move_mouse_naturally(
                                            current_pos['x'], current_pos['y'],
                                            target_x, target_y
                                        )
                                        
                                        # Hover delay
                                        await self.human_delay(500, 1000)
                                        
                                        # Click
                                        await btn.click(timeout=3000)
                                        logger.info(f"   ✅ Hover+clicked (attempt {attempt + 1})!")
                                        await self.human_delay(1000, 2000)
                                        
                                        # Check if navigation happened
                                        if 'authenticate/signup' not in self.page.url:
                                            logger.info("   ✅ Navigation detected!")
                                            return True
                            except Exception as e2:
                                logger.warning(f"   Hover+click failed: {e2}")
                            
                            # Method 3: Mouse down + mouse up (more realistic)
                            try:
                                logger.info(f"   Trying mouse down/up...")
                                box = await btn.bounding_box()
                                if box:
                                    # Move to button
                                    target_x = box['x'] + box['width'] / 2 + random.uniform(-3, 3)
                                    target_y = box['y'] + box['height'] / 2 + random.uniform(-3, 3)
                                    
                                    current_pos = await self.page.evaluate("() => ({x: window.lastMouseX || 0, y: window.lastMouseY || 0})")
                                    await self.move_mouse_naturally(
                                        current_pos['x'], current_pos['y'],
                                        target_x, target_y
                                    )
                                    
                                    # Human pause
                                    await self.human_delay(400, 800)
                                    
                                    # Mouse down
                                    await self.page.mouse.down()
                                    await self.human_delay(50, 150)
                                    
                                    # Mouse up
                                    await self.page.mouse.up()
                                    logger.info(f"   ✅ Mouse down/up complete!")
                                    await self.human_delay(1000, 2000)
                                    
                                    if 'authenticate/signup' not in self.page.url:
                                        logger.info("   ✅ Navigation detected!")
                                        return True
                            except Exception as e3:
                                logger.warning(f"   Mouse down/up failed: {e3}")
                            
                            # Method 4: Double click with human timing
                            try:
                                logger.info(f"   Trying double click...")
                                box = await btn.bounding_box()
                                if box:
                                    target_x = box['x'] + box['width'] / 2 + random.uniform(-3, 3)
                                    target_y = box['y'] + box['height'] / 2 + random.uniform(-3, 3)
                                    
                                    # Move to button
                                    current_pos = await self.page.evaluate("() => ({x: window.lastMouseX || 0, y: window.lastMouseY || 0})")
                                    await self.move_mouse_naturally(
                                        current_pos['x'], current_pos['y'],
                                        target_x, target_y
                                    )
                                    
                                    await self.human_delay(300, 600)
                                    
                                    # Double click with human timing
                                    await self.page.mouse.click(target_x, target_y)
                                    await self.human_delay(100, 250)
                                    await self.page.mouse.click(target_x, target_y)
                                    
                                    logger.info(f"   ✅ Double clicked!")
                                    await self.human_delay(1000, 2000)
                                    
                                    if 'authenticate/signup' not in self.page.url:
                                        logger.info("   ✅ Navigation detected!")
                                        return True
                            except Exception as e4:
                                logger.warning(f"   Double click failed: {e4}")
                            
                            # Method 5: Press Enter key with delay
                            try:
                                logger.info(f"   Trying Enter key...")
                                await btn.focus()
                                await self.human_delay(300, 700)
                                await self.page.keyboard.press('Enter')
                                await self.human_delay(500, 1000)
                                
                                if 'authenticate/signup' not in self.page.url:
                                    logger.info(f"   ✅ Enter key worked!")
                                    return True
                            except Exception as e5:
                                logger.warning(f"   Enter key failed: {e5}")
                        else:
                            logger.warning(f"   ⚠️  Button is disabled or not enabled")
                            
                            # Check why it's disabled
                            parent_form = await btn.evaluate("""
                                el => {
                                    const form = el.closest('form');
                                    if (form) {
                                        const inputs = form.querySelectorAll('input[required]');
                                        const empty = [];
                                        inputs.forEach(inp => {
                                            if (!inp.value || inp.value.trim() === '') {
                                                empty.push(inp.name || inp.placeholder || inp.type);
                                            }
                                        });
                                        return {
                                            hasForm: true,
                                            requiredFields: Array.from(inputs).map(i => i.name || i.placeholder),
                                            emptyFields: empty
                                        };
                                    }
                                    return {hasForm: false};
                                }
                            """)
                            
                            if parent_form.get('hasForm'):
                                logger.info(f"   Required fields: {parent_form.get('requiredFields')}")
                                if parent_form.get('emptyFields'):
                                    logger.warning(f"   Empty fields: {parent_form.get('emptyFields')}")
                
                except Exception as e:
                    continue
            
            logger.warning("\n⚠️  No clickable submit button found")
            return False
            
        except Exception as e:
            logger.error(f"Error finding submit button: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def create_account(self, email, password, first_name, last_name):
        """Create WTTJ account with cursor-based automation"""
        try:
            await self.setup_browser()
            
            logger.info(f"\n{'='*80}")
            logger.info(f"🖱️  CURSOR-BASED WTTJ ACCOUNT CREATION")
            logger.info(f"{'='*80}")
            logger.info(f"\n📧 Email: {email}")
            logger.info(f"🔒 Password: {password}")
            logger.info(f"👤 Name: {first_name} {last_name}")
            logger.info(f"\n{'='*80}\n")
            
            # Navigate to signup
            logger.info("[1/7] Loading signup page...")
            await self.page.goto('https://www.welcometothejungle.com/en/authenticate/signup', wait_until='domcontentloaded', timeout=60000)
            await self.human_delay(3000, 5000)  # Human-like page load wait
            
            # Clean names
            clean_first = re.sub(r'[^a-zA-Z\s\-\']', '', first_name) or 'Alexandre'
            clean_last = re.sub(r'[^a-zA-Z\s\-\']', '', last_name) or 'Dupont'
            
            # Fill email with cursor
            logger.info("[2/7] 📧 Filling email field with cursor...")
            await self.human_delay(500, 1000)  # Pause before starting
            email_input = self.page.locator('input[type="email"]').first
            await self.cursor_fill_field(email_input, email, "Email field")
            
            # Fill password with cursor
            logger.info("[3/7] 🔒 Filling password fields with cursor...")
            await self.human_delay(300, 700)  # Pause between fields
            pwd_inputs = self.page.locator('input[type="password"]')
            count = await pwd_inputs.count()
            for i in range(count):
                pwd = pwd_inputs.nth(i)
                if await pwd.is_visible():
                    await self.cursor_fill_field(pwd, password, f"Password field #{i+1}")
                    await self.human_delay(200, 500)  # Pause between password fields
            
            # Fill first name with cursor
            logger.info("[4/7] 👤 Filling name fields with cursor...")
            await self.human_delay(400, 800)  # Pause before name fields
            first_selectors = ['input[name*="first"]', 'input[placeholder*="First"]', 'input[placeholder*="Prénom"]']
            for selector in first_selectors:
                try:
                    first_input = self.page.locator(selector).first
                    if await first_input.is_visible():
                        await self.cursor_fill_field(first_input, clean_first, "First name")
                        break
                except:
                    continue
            
            # Fill last name with cursor
            await self.human_delay(300, 600)  # Pause between first and last name
            last_selectors = ['input[name*="last"]', 'input[placeholder*="Last"]', 'input[placeholder*="Nom"]']
            for selector in last_selectors:
                try:
                    last_input = self.page.locator(selector).first
                    if await last_input.is_visible():
                        await self.cursor_fill_field(last_input, clean_last, "Last name")
                        break
                except:
                    continue
            
            # Check terms checkbox with cursor
            logger.info("[5/7] ✅ Checking terms checkbox with cursor...")
            await self.human_delay(500, 1000)  # Pause before checkbox
            checkboxes = self.page.locator('input[type="checkbox"]')
            count = await checkboxes.count()
            for i in range(count):
                cb = checkboxes.nth(i)
                try:
                    if await cb.is_visible() and not await cb.is_checked():
                        await self.cursor_click_element(cb, f"Checkbox #{i+1}")
                        await self.human_delay(200, 500)
                except:
                    pass
            
            await self.human_delay(1000, 2000)  # Pause after filling all fields
            
            # Find and click submit with cursor
            logger.info("[6/7] 🔘 Finding and clicking submit button with cursor...")
            success = await self.find_and_click_submit_with_cursor()
            
            if success:
                logger.info("[7/7] ⏳ Waiting for account creation...")
                await asyncio.sleep(5)
                
                # Check if account created
                current_url = self.page.url
                if 'authenticate/signup' not in current_url or any(kw in current_url for kw in ['onboarding', 'profile', 'welcome', 'preferences']):
                    logger.info(f"\n{'='*80}")
                    logger.info(f"✅ ACCOUNT CREATED SUCCESSFULLY!")
                    logger.info(f"{'='*80}")
                    logger.info(f"\n📧 Email: {email}")
                    logger.info(f"🔒 Password: {password}")
                    logger.info(f"🌐 Current URL: {current_url}")
                    logger.info(f"\n{'='*80}\n")
                    
                    return {
                        "success": True,
                        "email": email,
                        "password": password,
                        "first_name": clean_first,
                        "last_name": clean_last,
                        "status": "created",
                        "url": current_url,
                        "method": "cursor_automation"
                    }
                else:
                    logger.warning(f"\n⚠️  Still on signup page after click")
                    logger.info(f"Current URL: {current_url}")
            
            # If auto-click didn't work, wait for manual
            logger.info("\n" + "="*80)
            logger.info("⚠️  AUTOMATIC CLICK UNSUCCESSFUL - WAITING FOR MANUAL")
            logger.info("="*80)
            logger.info("\nThe form has been filled with:")
            logger.info(f"  📧 Email: {email}")
            logger.info(f"  🔒 Password: {password}")
            logger.info(f"  👤 Name: {clean_first} {clean_last}")
            logger.info("\nPlease click the submit button in the browser")
            logger.info("Waiting up to 120 seconds...")
            logger.info("="*80 + "\n")
            
            # Wait for navigation
            max_wait = 120
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                current_url = self.page.url
                
                if 'authenticate/signup' not in current_url or any(kw in current_url for kw in ['onboarding', 'profile', 'welcome', 'preferences', 'getting-started']):
                    logger.info(f"\n{'='*80}")
                    logger.info(f"✅ ACCOUNT CREATED! (Manual completion)")
                    logger.info(f"{'='*80}")
                    logger.info(f"\n📧 Email: {email}")
                    logger.info(f"🔒 Password: {password}")
                    logger.info(f"🌐 URL: {current_url}")
                    logger.info(f"\n{'='*80}\n")
                    
                    return {
                        "success": True,
                        "email": email,
                        "password": password,
                        "first_name": clean_first,
                        "last_name": clean_last,
                        "status": "created_manually",
                        "url": current_url,
                        "method": "manual_with_cursor"
                    }
                
                await asyncio.sleep(3)
            
            logger.warning("\n⚠️  Timeout waiting for account creation")
            return {
                "success": False,
                "email": email,
                "password": password,
                "status": "timeout",
                "message": "Manual completion required - timeout"
            }
                
        except Exception as e:
            logger.error(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            logger.info("\n🔒 Browser will close in 10 seconds...")
            await asyncio.sleep(10)
            if self.browser:
                await self.browser.close()


async def create_wttj_account_with_cursor(email: str, password: str, first_name: str, last_name: str) -> dict:
    """Async wrapper for cursor-based account creation"""
    creator = CursorWTTJAutomation()
    return await creator.create_account(email, password, first_name, last_name)


async def main():
    """Test cursor automation"""
    timestamp = int(time.time())
    email = f"cursor_test_{timestamp}@gmail.com"
    password = f"Wttj2026!!${uuid.uuid4().hex[:6]}"
    
    creator = CursorWTTJAutomation()
    result = await creator.create_account(
        email=email,
        password=password,
        first_name="Cursor",
        last_name="Test"
    )
    
    print("\n" + "="*80)
    print("FINAL RESULT")
    print("="*80)
    if result["success"]:
        print(f"✅ SUCCESS!")
        print(f"   Email: {result['email']}")
        print(f"   Password: {result['password']}")
        print(f"   Status: {result.get('status')}")
        print(f"   Method: {result.get('method')}")
        print(f"   URL: {result.get('url')}")
    else:
        print(f"❌ FAILED")
        print(f"   Error: {result.get('error') or result.get('message')}")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
