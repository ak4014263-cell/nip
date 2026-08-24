#!/usr/bin/env python3
"""
Complete Browser Automation - Apply to WTTJ Jobs
Works with actual WTTJ interface
"""
import asyncio
import sys
import os

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except:
    pass

from playwright.async_api import async_playwright

async def apply_to_wttj():
    """Apply to jobs on WTTJ"""
    
    WTTJ_EMAIL = "kio825648@gmail.com"
    WTTJ_PASSWORD = "#e2nU&C7l3T&6U^p"
    
    print("\n" + "="*80)
    print("WTTJ JOB APPLICATION - BROWSER AUTOMATION")
    print("="*80 + "\n")
    
    os.makedirs('screenshots', exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(viewport={'width': 1280, 'height': 720})
        
        try:
            # LOGIN
            print("[1/5] LOGIN TO WTTJ")
            print("-" * 80)
            print("Navigating to login page...")
            await page.goto('https://www.welcometothejungle.com/en/authenticate/signin', 
                          timeout=30000, wait_until='domcontentloaded')
            await asyncio.sleep(2)
            await page.screenshot(path='screenshots/step1_login.png')
            
            print("Filling email...")
            await page.fill('input[type="email"]', WTTJ_EMAIL)
            await asyncio.sleep(0.5)
            
            print("Filling password...")
            await page.fill('input[type="password"]', WTTJ_PASSWORD)
            await asyncio.sleep(0.5)
            
            print("Clicking login button...")
            await page.click('button[type="submit"]')
            await asyncio.sleep(4)
            await page.screenshot(path='screenshots/step2_logged_in.png')
            
            print(f"✓ Login complete. URL: {page.url}\n")
            
            # NAVIGATE TO JOB MATCHES
            print("[2/5] NAVIGATE TO JOB MATCHES")
            print("-" * 80)
            print("Going to job matches...")
            await page.goto('https://www.welcometothejungle.com/en/jobs-matches',
                          timeout=30000, wait_until='domcontentloaded')
            await asyncio.sleep(3)
            await page.screenshot(path='screenshots/step3_job_matches.png')
            print("✓ Job matches page loaded\n")
            
            # FIND AND SELECT FIRST JOB
            print("[3/5] SELECT FIRST JOB")
            print("-" * 80)
            
            # Get all job cards/items
            job_items = await page.locator('[data-testid*="job"], [class*="job-card"], article').all()
            print(f"Found {len(job_items)} job items")
            
            if len(job_items) > 0:
                # Click first job
                print("Clicking first job...")
                await job_items[0].click()
                await asyncio.sleep(2)
                await page.screenshot(path='screenshots/step4_job_selected.png')
                print("✓ Job selected\n")
            else:
                print("No jobs found\n")
                await browser.close()
                return
            
            # APPLY TO JOB
            print("[4/5] APPLY TO JOB")
            print("-" * 80)
            
            # Look for apply button/action
            apply_actions = [
                'button:has-text("Apply")',
                'button:has-text("Apply now")',
                'button:has-text("Postuler")',
                'a:has-text("Apply")',
                '[class*="apply"]',
                'button[aria-label*="apply" i]',
            ]
            
            applied = False
            for selector in apply_actions:
                try:
                    buttons = await page.locator(selector).all()
                    if len(buttons) > 0:
                        print(f"Found apply element: {selector}")
                        await buttons[0].click()
                        print("✓ Apply clicked")
                        applied = True
                        await asyncio.sleep(2)
                        break
                except:
                    pass
            
            if not applied:
                print("⚠️ Could not find apply button")
                # Try keyboard shortcut
                print("Trying keyboard action...")
                await page.keyboard.press('Enter')
                await asyncio.sleep(2)
            
            await page.screenshot(path='screenshots/step5_after_apply.png')
            print()
            
            # FILL APPLICATION FORM
            print("[5/5] FILL APPLICATION FORM")
            print("-" * 80)
            
            # Look for and fill any form fields
            all_inputs = await page.locator('input, textarea, [contenteditable="true"]').all()
            print(f"Found {len(all_inputs)} input fields")
            
            filled_count = 0
            for i, field in enumerate(all_inputs[:5]):
                try:
                    field_type = await field.get_attribute('type')
                    placeholder = await field.get_attribute('placeholder')
                    name = await field.get_attribute('name')
                    
                    visible = await field.is_visible()
                    if visible:
                        print(f"  Field {i+1}: type={field_type}, placeholder={placeholder}, name={name}")
                        
                        # Try to fill with appropriate data
                        if i == 0:
                            await field.fill('Kumar Developer')
                            filled_count += 1
                            print("    → Filled with name")
                        elif i == 1:
                            await field.fill(WTTJ_EMAIL)
                            filled_count += 1
                            print("    → Filled with email")
                        elif i == 2:
                            await field.fill('+33612345678')
                            filled_count += 1
                            print("    → Filled with phone")
                except Exception as e:
                    pass
            
            print(f"✓ Filled {filled_count} fields\n")
            await asyncio.sleep(1)
            await page.screenshot(path='screenshots/step6_form_filled.png')
            
            # SUBMIT
            print("[SUBMIT] SENDING APPLICATION")
            print("-" * 80)
            
            # Look for submit button
            submit_selectors = [
                'button:has-text("Send")',
                'button:has-text("Submit")',
                'button:has-text("Envoyer")',
                'button[type="submit"]',
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    buttons = await page.locator(selector).all()
                    if len(buttons) > 0:
                        print(f"Found submit button: {selector}")
                        # Scroll to button
                        await buttons[-1].scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)
                        await buttons[-1].click()
                        print("✓ Application sent!")
                        submitted = True
                        await asyncio.sleep(3)
                        break
                except:
                    pass
            
            if not submitted:
                print("⚠️ Could not find submit button")
            
            await page.screenshot(path='screenshots/step7_submitted.png')
            
            print("\n" + "="*80)
            print("✓ APPLICATION PROCESS COMPLETE!")
            print("="*80)
            print("\nScreenshots saved:")
            print("  step1_login.png - Login page")
            print("  step2_logged_in.png - After login")
            print("  step3_job_matches.png - Job matches")
            print("  step4_job_selected.png - Job selected")
            print("  step5_after_apply.png - After apply click")
            print("  step6_form_filled.png - Form filled")
            print("  step7_submitted.png - After submit")
            print("\nBrowser will close in 15 seconds...\n")
            
            await asyncio.sleep(15)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print("\nBrowser staying open for debugging (30 seconds)...")
            await asyncio.sleep(30)
        
        finally:
            await browser.close()
            print("Browser closed.\n")


if __name__ == "__main__":
    asyncio.run(apply_to_wttj())
