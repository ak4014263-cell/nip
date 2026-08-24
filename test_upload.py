import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Login
        await page.goto("https://www.welcometothejungle.com/en/signin")
        await page.fill('input[type="email"]', "k45490335@gmail.com")
        await page.fill('input[type="password"]', "Wttj@Hon05ed2026!")
        await page.click('button[type="submit"]')
        
        try:
            await page.wait_for_url("**/onboarding/complete-profile*", timeout=15000)
            print("Reached onboarding profile screen!")
        except:
            print("Did not reach onboarding profile screen. URL:", page.url)

        await asyncio.sleep(4)

        # Remove axeptio cookies if any
        try:
            await page.evaluate("document.querySelectorAll('[class*=\"axeptio\"],[id*=\"axeptio\"]').forEach(e=>e.remove())")
        except: pass

        resume_path = os.path.abspath("scratch/resume.pdf")
        if not os.path.exists(resume_path):
            print(f"File not found: {resume_path}")
            return

        print("\n--- Trying set_input_files ---")
        for sel in ["input[type='file']", "input[accept*='pdf']", "input[accept*='.pdf']"]:
            loc = page.locator(sel).first
            count = await loc.count()
            print(f"Selector {sel} count: {count}")
            if count > 0:
                try:
                    await loc.set_input_files(resume_path, timeout=5000)
                    print(f"✅ Success with {sel}")
                except Exception as e:
                    print(f"❌ Error with {sel}: {e}")

        print("\n--- Trying expect_file_chooser ---")
        try:
            async with page.expect_file_chooser(timeout=5000) as fc_info:
                upload_btn = page.locator("button:has-text('Upload PDF'), button:has-text('Upload CV'), [class*='upload']").first
                await upload_btn.click(force=True)
            fc = await fc_info.value
            await fc.set_files(resume_path)
            print("✅ Success with file chooser")
        except Exception as e:
            print(f"❌ Error with file chooser: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
