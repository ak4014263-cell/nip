#!/usr/bin/env python3
"""
Parallel Registration System
Jab user Swipply par register kare, background mein WTTJ form bhi fill hota hai
"""
import asyncio
from playwright.async_api import async_playwright, Browser, Page
from typing import Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ParallelRegistrationManager:
    """
    User Swipply par registration kare, tab:
    1. Main browser: Swipply registration (user dekh sakta hai)
    2. Background browser: WTTJ form filling (hidden, automatic)
    
    Dono parallel chalenge!
    """
    
    def __init__(self):
        self.swipply_page: Optional[Page] = None
        self.wttj_page: Optional[Page] = None
        self.user_data: Dict = {}
        
    async def start_parallel_registration(self, 
                                         swipply_url: str = "http://localhost:5173/register",
                                         wttj_url: str = "https://www.welcometothejungle.com/en/authenticate/signup"):
        """
        Dono forms ek saath start karo
        
        Args:
            swipply_url: Swipply registration page
            wttj_url: WTTJ signup page
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            
            try:
                # Context 1: Swipply (Main - User visible)
                swipply_context = await browser.new_context()
                self.swipply_page = await swipply_context.new_page()
                
                # Context 2: WTTJ (Background - Hidden but can be checked)
                wttj_context = await browser.new_context()
                self.wttj_page = await wttj_context.new_page()
                
                logger.info("🚀 Starting parallel registration...")
                logger.info("   📱 Swipply: User will fill form")
                logger.info("   🌐 WTTJ: Background auto-filling")
                
                # Start both processes in parallel
                await asyncio.gather(
                    self.monitor_swipply_registration(),
                    self.auto_fill_wttj_form()
                )
                
                return {
                    "success": True,
                    "swipply_data": self.user_data,
                    "wttj_filled": True
                }
                
            finally:
                await browser.close()
    
    async def monitor_swipply_registration(self):
        """
        Swipply form ko monitor karo aur data extract karo
        """
        logger.info("📱 Loading Swipply registration page...")
        await self.swipply_page.goto("http://localhost:5173/register")
        
        # Wait for user to fill form
        logger.info("⏳ Waiting for user to fill Swipply form...")
        
        # Monitor form fields as user types
        await self.swipply_page.evaluate("""
            () => {
                // Listen to all input fields
                const inputs = document.querySelectorAll('input');
                inputs.forEach(input => {
                    input.addEventListener('input', (e) => {
                        console.log('Field changed:', e.target.name, e.target.value);
                    });
                });
            }
        """)
        
        # Extract data when user submits
        async def extract_data():
            """Extract form data from Swipply"""
            while True:
                try:
                    # Try to get field values
                    email = await self.swipply_page.locator('input[name="email"], input[type="email"]').input_value()
                    password = await self.swipply_page.locator('input[name="password"], input[type="password"]').first.input_value()
                    
                    # Try to get name fields
                    try:
                        first_name = await self.swipply_page.locator('input[name*="first"], input[placeholder*="First"]').input_value()
                    except:
                        first_name = ""
                    
                    try:
                        last_name = await self.swipply_page.locator('input[name*="last"], input[placeholder*="Last"]').input_value()
                    except:
                        last_name = ""
                    
                    # If we got data, store it
                    if email and password:
                        self.user_data = {
                            "email": email,
                            "password": password,
                            "first_name": first_name or "User",
                            "last_name": last_name or "Swipply",
                            "timestamp": datetime.now().isoformat()
                        }
                        logger.info(f"✅ Data captured from Swipply: {email}")
                        return True
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    await asyncio.sleep(1)
        
        # Keep extracting data
        await extract_data()
        
        # Wait for form submission
        logger.info("✅ Swipply registration complete!")
    
    async def auto_fill_wttj_form(self):
        """
        WTTJ form automatically fill karo (background mein)
        """
        logger.info("🌐 Loading WTTJ signup page (background)...")
        await self.wttj_page.goto("https://www.welcometothejungle.com/en/authenticate/signup")
        await asyncio.sleep(2)
        
        # Wait for user data from Swipply
        logger.info("⏳ Waiting for data from Swipply form...")
        while not self.user_data:
            await asyncio.sleep(0.5)
        
        logger.info("📝 Auto-filling WTTJ form with Swipply data...")
        
        # Fill WTTJ form with data from Swipply
        try:
            # Fill first name
            first_name_field = self.wttj_page.locator('input[placeholder*="Anita"], input[name*="first"]').first
            await first_name_field.fill(self.user_data['first_name'])
            await asyncio.sleep(0.5)
            logger.info(f"   ✓ First name: {self.user_data['first_name']}")
            
            # Fill email
            email_field = self.wttj_page.locator('input[type="email"]')
            await email_field.fill(self.user_data['email'])
            await asyncio.sleep(0.5)
            logger.info(f"   ✓ Email: {self.user_data['email']}")
            
            # Fill password
            # Note: WTTJ needs strong password, so we'll modify it
            strong_password = self.user_data['password'] + "Wttj2026!"
            password_field = self.wttj_page.locator('input[type="password"]').first
            await password_field.fill(strong_password)
            await asyncio.sleep(0.5)
            logger.info(f"   ✓ Password: {strong_password}")
            
            # Check checkbox
            try:
                checkbox = self.wttj_page.locator('input[type="checkbox"]').first
                await checkbox.click(force=True)
                logger.info("   ✓ Checkbox checked")
            except:
                pass
            
            # Verify button is enabled
            button = self.wttj_page.locator('button[type="submit"]').first
            is_enabled = await button.is_enabled()
            
            if is_enabled:
                logger.info("✅ WTTJ form is ready to submit!")
                logger.info("   Button is enabled - user can click when ready")
            else:
                logger.warning("⚠️  WTTJ button is disabled - check validation")
            
            # Keep page open for user to click
            logger.info("🖱️  Waiting for user to click 'Agree and Continue'...")
            await asyncio.sleep(300)  # Wait 5 minutes
            
        except Exception as e:
            logger.error(f"❌ Error filling WTTJ form: {e}")
    
    async def sync_form_data(self):
        """
        Real-time sync: Jaise hi user Swipply mein type kare, WTTJ mein bhi type ho
        """
        # This would need JavaScript injection on Swipply to capture keystrokes
        # and mirror them to WTTJ form
        pass


class SmartParallelRegistration:
    """
    Advanced version: Real-time sync between forms
    """
    
    async def start_smart_sync(self):
        """
        User jab bhi Swipply mein field fill kare, 
        instantly WTTJ mein bhi wo field fill ho jaye
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            
            # Create two pages side by side
            swipply_page = await browser.new_page()
            wttj_page = await browser.new_page()
            
            # Load both forms
            await swipply_page.goto("http://localhost:5173/register")
            await wttj_page.goto("https://www.welcometothejungle.com/en/authenticate/signup")
            
            # Setup real-time sync
            await swipply_page.expose_function("syncToWTTJ", 
                lambda field, value: self.sync_field_to_wttj(wttj_page, field, value))
            
            # Inject listener on Swipply
            await swipply_page.evaluate("""
                () => {
                    const fieldMap = {
                        'email': 'email',
                        'password': 'password',
                        'firstName': 'firstName',
                        'lastName': 'lastName'
                    };
                    
                    document.querySelectorAll('input').forEach(input => {
                        input.addEventListener('input', (e) => {
                            const fieldType = e.target.name || e.target.type;
                            window.syncToWTTJ(fieldType, e.target.value);
                        });
                    });
                }
            """)
            
            logger.info("🔄 Real-time sync enabled!")
            logger.info("   Type in Swipply → Instantly appears in WTTJ")
            
            await asyncio.sleep(600)  # Keep open for 10 minutes
    
    async def sync_field_to_wttj(self, wttj_page: Page, field: str, value: str):
        """Instantly sync field value to WTTJ"""
        try:
            if field == 'email':
                await wttj_page.fill('input[type="email"]', value)
            elif field == 'password':
                await wttj_page.fill('input[type="password"]', value + "Wttj2026!")
            elif 'first' in field.lower():
                await wttj_page.fill('input[placeholder*="Anita"]', value)
            
            logger.info(f"🔄 Synced {field}: {value}")
        except Exception as e:
            logger.error(f"Sync error: {e}")


async def main():
    """
    Example usage
    """
    print("\n" + "="*80)
    print("PARALLEL REGISTRATION SYSTEM")
    print("="*80)
    print("\nHow it works:")
    print("  1. User fills Swipply registration form (main window)")
    print("  2. WTTJ form fills automatically in background")
    print("  3. When user submits Swipply, WTTJ is ready to submit too!")
    print("="*80)
    
    choice = input("\nChoose mode:\n  1. Parallel (separate windows)\n  2. Real-time sync\nChoice: ")
    
    if choice == "2":
        manager = SmartParallelRegistration()
        await manager.start_smart_sync()
    else:
        manager = ParallelRegistrationManager()
        result = await manager.start_parallel_registration()
        print(f"\n✅ Result: {result}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    asyncio.run(main())
