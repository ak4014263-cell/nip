#!/usr/bin/env python3
"""
Local test script for WTTJ bot bypass
Run this to test the bot bypass locally before deploying
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from wttj_bot_bypass import WTTJBotBypass


async def test_bypass():
    """Test the complete bot bypass flow"""
    
    print("🤖 Testing WTTJ Bot Bypass Locally")
    print("=" * 50)
    
    # Configuration
    email = "test@example.com"
    password = "TestPass123!@"
    first_name = "TestUser"
    signup_url = "https://www.welcometothe.jungle/users/sign_up"
    
    print(f"\n📋 Test Configuration:")
    print(f"  Email: {email}")
    print(f"  Password: {password}")
    print(f"  First Name: {first_name}")
    print(f"  Signup URL: {signup_url}")
    print(f"  Headless: False (you'll see the browser)")
    
    bypass = WTTJBotBypass(headless=False, use_proxy=None)
    
    try:
        # Step 1: Launch browser
        print("\n🚀 Step 1/5: Launching Firefox browser...")
        await bypass.launch()
        print("✅ Browser launched successfully")
        
        # Step 2: Navigate and bypass bot challenge
        print("\n🤖 Step 2/5: Bypassing bot challenge...")
        result = await bypass.bypass_captcha(signup_url, timeout=60)
        if result:
            print("✅ Bot challenge bypassed")
        else:
            print("❌ Bot challenge bypass failed")
            return False
        
        # Step 3: Accept cookies
        print("\n🍪 Step 3/5: Accepting cookies...")
        await bypass.accept_cookies()
        print("✅ Cookies accepted")
        
        # Step 4: Fill form
        print("\n📝 Step 4/5: Filling signup form...")
        form_filled = await bypass.fill_signup_form(
            email=email,
            password=password,
            first_name=first_name
        )
        if form_filled:
            print("✅ Form filled successfully")
        else:
            print("⚠️  Form filling had issues")
        
        # Step 5: Click agree button
        print("\n👆 Step 5/5: Clicking 'Agree and create profile' button...")
        agree_clicked = await bypass.click_agree_button()
        if agree_clicked:
            print("✅ Agree button clicked successfully")
        else:
            print("❌ Could not click agree button")
            print("\n📸 Current page state:")
            print(f"  URL: {bypass.page.url}")
            print(f"  Title: {await bypass.page.title()}")
            
            # Get all buttons for debugging
            buttons = await bypass.page.evaluate("""
                () => Array.from(document.querySelectorAll('button'))
                    .map(btn => btn.textContent.trim())
                    .filter(text => text.length > 0)
            """)
            print(f"  Buttons on page: {buttons}")
        
        # Wait to see result
        print("\n⏳ Waiting 10 seconds to observe the result...")
        print("   (Check the browser window)")
        await asyncio.sleep(10)
        
        print("\n" + "=" * 50)
        print("✅ Test completed!")
        print(f"Final URL: {bypass.page.url}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        print("\n🔒 Closing browser...")
        await bypass.close()
        print("Done!")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  WTTJ Bot Bypass Local Test")
    print("=" * 50)
    print("\nThis will:")
    print("  1. Open Firefox browser (visible)")
    print("  2. Navigate to WTTJ signup page")
    print("  3. Accept cookies")
    print("  4. Solve captcha (if present)")
    print("  5. Fill the signup form")
    print("  6. Click 'Agree and create profile' button")
    print("\nPress Ctrl+C to cancel, or press Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nTest cancelled.")
        sys.exit(0)
    
    result = asyncio.run(test_bypass())
    
    if result:
        print("\n✅ SUCCESS: Bot bypass test passed!")
        sys.exit(0)
    else:
        print("\n❌ FAILED: Bot bypass test failed!")
        print("\nTroubleshooting tips:")
        print("  1. Check if Playwright is installed: pip install playwright")
        print("  2. Install Firefox browser: playwright install firefox")
        print("  3. Check the browser window for error messages")
        print("  4. Try running again (sometimes captcha needs manual solving)")
        sys.exit(1)
