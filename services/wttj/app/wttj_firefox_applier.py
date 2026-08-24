import asyncio
import logging
import os
import sys
from playwright.async_api import async_playwright, Page, Locator

# Fix for Python 3.14+ on Windows - Playwright needs ProactorEventLoop for subprocesses
if sys.platform == 'win32':
    if sys.version_info >= (3, 14):
        # Python 3.14+ on Windows requires explicit event loop policy
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except AttributeError:
            pass
    else:
        # Python 3.8-3.13 on Windows
        try:
            if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except:
            pass

try:
    from services.wttj.app.live_state import update_live_state
except ImportError:
    from .live_state import update_live_state

logger = logging.getLogger(__name__)

os.makedirs("screenshots/apply_debug", exist_ok=True)

# Screenshot counter for sequential naming
screenshot_counter = 0

async def take_screenshot(page: Page, description: str):
    """Take a timestamped screenshot with description"""
    global screenshot_counter
    screenshot_counter += 1
    timestamp = asyncio.get_event_loop().time()
    filename = f"screenshots/apply_debug/step_{screenshot_counter:02d}_{description.replace(' ', '_').lower()}.png"
    try:
        await page.screenshot(path=filename, full_page=True)
        logger.info(f"📸 Screenshot saved: {filename}")
    except Exception as e:
        logger.warning(f"Failed to take screenshot {filename}: {e}")

class WTTJFirefoxApplier:
    def __init__(self):
        self.wttj_base_url = "https://www.welcometothejungle.com"
        self.wttj_login_url = f"{self.wttj_base_url}/en/authenticate/signin"

    async def apply_to_job(
        self,
        email: str,
        password: str,
        job_url: str,
        profile_data: dict,
        headless: bool = False,
    ) -> dict:
        global screenshot_counter
        screenshot_counter = 0  # Reset counter for each application
        
        logger.info(f"🚀 Starting Firefox automation for {email} → {job_url}")

        async with async_playwright() as p:
            # Launch Firefox with anti-detection settings
            browser = await p.firefox.launch(
                headless=headless,
                firefox_user_prefs={
                    # Disable automation detection
                    "dom.webdriver.enabled": False,
                    "useAutomationExtension": False,
                    # Privacy & security settings
                    "privacy.trackingprotection.enabled": True,
                    "privacy.trackingprotection.socialtracking.enabled": True,
                    "privacy.donottrackheader.enabled": True,
                    # Performance settings
                    "network.http.pipelining": True,
                    "network.http.proxy.pipelining": True,
                    "network.http.pipelining.maxrequests": 8,
                    # Disable WebRTC leak
                    "media.peerconnection.enabled": False,
                    # Mimic real browser
                    "general.platform.override": "Win64",
                    "general.oscpu.override": "Windows NT 10.0; Win64; x64",
                }
            )
            
            # Create context with realistic settings
            context = await browser.new_context(
                viewport={"width": 1366, "height": 768},  # Common resolution
                screen={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
                    "Gecko/20100101 Firefox/121.0"
                ),
                locale="en-US",
                timezone_id="Europe/Paris",
                permissions=["geolocation"],
                geolocation={"latitude": 48.8566, "longitude": 2.3522},  # Paris coordinates
                color_scheme="light",
                has_touch=False,
                device_scale_factor=1,
                is_mobile=False,
                extra_http_headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Cache-Control": "max-age=0",
                }
            )
            
            page = await context.new_page()
            
            # Inject anti-detection scripts
            await page.add_init_script("""
                // Override webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Override plugins to appear as a real browser
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en', 'fr']
                });
                
                // Override chrome property
                window.chrome = {
                    runtime: {}
                };
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Add realistic mouse movements
                let mouseX = 0;
                let mouseY = 0;
                document.addEventListener('mousemove', (e) => {
                    mouseX = e.clientX;
                    mouseY = e.clientY;
                });
            """)

            try:
                # ── 1. LOGIN ─────────────────────────────────────────────────
                await update_live_state("Logging In", 1, 10, self.wttj_login_url, "Starting Firefox automation and authenticating...", page=page)
                await take_screenshot(page, "browser_launched")
                await self._login(page, email, password)
                await take_screenshot(page, "after_login")

                # ── 2. GO TO JOB PAGE ─────────────────────────────────────────
                logger.info(f"Navigating to: {job_url}")
                await update_live_state("Loading Job Page", 2, 25, job_url, f"Navigating to {job_url}", page=page)
                await page.goto(job_url, timeout=60000)
                await take_screenshot(page, "job_page_initial_load")
                
                await page.wait_for_load_state("networkidle", timeout=15000)
                await asyncio.sleep(2)
                await take_screenshot(page, "job_page_after_network_idle")
                
                await self._dismiss_cookies(page)
                await take_screenshot(page, "after_dismiss_cookies")
                
                await update_live_state("Scanning Job", 2, 35, job_url, "Searching for application triggers...", page=page)

                # ── 3. CLICK APPLY ─────────────────────────────────────────────
                await take_screenshot(page, "before_click_apply")
                apply_clicked = await self._click_apply_button(page)
                await take_screenshot(page, "after_click_apply")
                
                if not apply_clicked:
                    logger.warning("Apply button not found")
                    await take_screenshot(page, "ERROR_no_apply_button")
                    await browser.close()
                    return {"success": False, "message": "Apply button not found", "job_url": job_url}

                # Wait for modal to fully animate in
                logger.info("⏳ Waiting for application modal to load...")
                await update_live_state("Opening Application", 3, 50, job_url, "Application modal detected, analyzing fields...", page=page)
                await asyncio.sleep(2)
                await take_screenshot(page, "modal_opening_2sec")
                await asyncio.sleep(3)
                await take_screenshot(page, "modal_fully_opened")

                # ── 4. FILL THE WTTJ APPLICATION MODAL ──────────────────────────
                await update_live_state("Form Filling", 4, 70, job_url, "Filling application fields with saved profile data...", page=page)
                await take_screenshot(page, "before_filling_form")
                
                filled = await self._fill_wttj_modal(page, profile_data, email)
                
                logger.info(f"📝 Filled {filled} fields")
                await take_screenshot(page, "after_filling_form")
                await update_live_state("Reviewing Form", 4, 85, job_url, f"Filled {filled} fields from profile.", page=page)

                # ── 5. ACCEPT TERMS ────────────────────────────────────────────
                await take_screenshot(page, "before_accept_terms")
                await self._accept_terms(page)
                await take_screenshot(page, "after_accept_terms")

                # ── 6. SUBMIT ───────────────────────────────────────────────────
                await update_live_state("Submitting", 5, 95, job_url, "Clicking submit button...", page=page)
                await take_screenshot(page, "before_submit")
                
                submitted = await self._submit_form(page)
                await take_screenshot(page, "immediately_after_submit_click")
                
                await asyncio.sleep(3)
                await take_screenshot(page, "3sec_after_submit")

                if submitted:
                    logger.info("🎉 Application submitted!")
                    await update_live_state("Complete", 6, 100, job_url, "Application sent successfully!", page=page, is_running=False)
                    await take_screenshot(page, "SUCCESS_final_page")
                    await browser.close()
                    return {
                        "success": True,
                        "message": "Application submitted via Firefox automation",
                        "job_url": job_url,
                        "fields_filled": filled,
                    }
                else:
                    logger.warning("⚠️ Submit failed — validation errors or submit button not found")
                    await update_live_state("Submit Failed", 6, 90, job_url, "❌ Validation errors detected or submit blocked. Check screenshots.", page=page, is_running=False)
                    await take_screenshot(page, "ERROR_submit_failed")
                    await asyncio.sleep(10)  # Leave browser open briefly so screenshot captures the error state
                    await browser.close()
                    return {
                        "success": False,
                        "message": f"Filled {filled} fields but couldn't submit",
                        "job_url": job_url,
                    }

            except Exception as e:
                logger.error(f"Automation error: {e}")
                try:
                    await take_screenshot(page, f"EXCEPTION_{str(e)[:30].replace(' ', '_')}")
                except Exception:
                    pass
                await browser.close()
                return {"success": False, "message": str(e), "error": str(e)}

    # ═══════════════════════════════════════════════════════════════════════════════

    async def _dismiss_cookies(self, page: Page):
        """Dismiss cookie consent with human-like behavior"""
        # Add random delay to mimic human reading time
        await asyncio.sleep(0.8 + (asyncio.get_event_loop().time() % 0.4))
        
        for sel in [
            'button#axeptio_btn_acceptAll',
            'button:has-text("OK for me")',
            'button:has-text("Accept all")',
            'button:has-text("Tout accepter")',
            'button:has-text("J\'accepte")',
        ]:
            try:
                btn = page.locator(sel).first
                if await btn.count() > 0 and await btn.is_visible():
                    # Move mouse to button (human-like)
                    box = await btn.bounding_box()
                    if box:
                        await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2, steps=10)
                        await asyncio.sleep(0.2)
                    
                    await btn.click()
                    await asyncio.sleep(0.5)
                    logger.info("✅ Cookie banner dismissed")
                    break
            except Exception as e:
                logger.debug(f"Cookie dismiss attempt failed: {e}")

    async def _login(self, page: Page, email: str, password: str):
        import json, pathlib
        logger.info(f"🔐 Logging in as {email}...")

        # ── Per-user cookie file — NEVER share sessions between users ──
        email_slug = email.replace("@", "_").replace(".", "_").lower()
        COOKIE_FILE = pathlib.Path(f"scratch/sessions/{email_slug}.json")
        COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)

        # ── Try restoring saved session for THIS specific user ──────────────────
        if COOKIE_FILE.exists():
            try:
                cookies = json.loads(COOKIE_FILE.read_text())
                await page.context.add_cookies(cookies)
                await take_screenshot(page, "login_cookies_loaded")
                
                # Add human-like delay before navigating
                await asyncio.sleep(1.2)
                
                await page.goto("https://www.welcometothejungle.com/en/me", timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_load_state("networkidle", timeout=10000)
                await take_screenshot(page, "login_session_check")
                
                if "me" in page.url and "authenticate" not in page.url:
                    # Verify this session belongs to the CORRECT user by checking the page for their email
                    page_content = await page.content()
                    email_local = email.split("@")[0].lower()
                    
                    sign_in_btn = page.locator('a[href*="/authenticate/signin"], button:has-text("Sign in")').first
                    not_signed_in = await sign_in_btn.count() > 0 and await sign_in_btn.is_visible(timeout=2000)
                    
                    if not not_signed_in:
                        logger.info(f"✅ Session restored from cookie cache for {email} — skipping login form")
                        await take_screenshot(page, "login_session_restored")
                        return
                    else:
                        logger.warning(f"⚠️ Session expired for {email} — re-logging in")
                else:
                    logger.warning(f"⚠️ Cached session for {email} did not redirect to /me — re-logging in")
                await take_screenshot(page, "login_session_expired")
            except Exception as e:
                logger.warning(f"Cookie restore failed for {email}: {e}")
                await take_screenshot(page, "login_cookie_restore_failed")

        # ── Full login flow for THIS user ──────────────────────────────────────
        logger.info(f"🔑 Starting fresh login for {email}")
        await asyncio.sleep(0.8 + (asyncio.get_event_loop().time() % 0.6))
        
        await page.goto(self.wttj_login_url, timeout=60000, wait_until="domcontentloaded")
        await take_screenshot(page, "login_page_loaded")
        
        # Wait for page to be ready
        await page.wait_for_load_state("networkidle", timeout=15000)
        await asyncio.sleep(1.5)
        await take_screenshot(page, "login_page_dom_ready")
        
        await self._dismiss_cookies(page)
        await take_screenshot(page, "login_cookies_dismissed")

        # Human-like typing for email
        try:
            email_input = await page.wait_for_selector('input[type="email"]', timeout=8000, state="visible")
            await take_screenshot(page, "login_email_field_found")
            
            # Click and focus
            await email_input.click()
            await asyncio.sleep(0.3)
            
            # Type with human-like speed
            for char in email:
                await page.keyboard.type(char)
                await asyncio.sleep(0.08 + (asyncio.get_event_loop().time() % 0.04))
            
            await asyncio.sleep(0.5)
            await take_screenshot(page, "login_email_filled")
        except Exception as e:
            logger.warning(f"⚠️ Email field error: {e}")
            await take_screenshot(page, "login_ERROR_email_field_not_found")
            return

        # Human-like typing for password
        try:
            password_input = await page.wait_for_selector('input[type="password"]', timeout=5000, state="visible")
            
            # Click and focus
            await password_input.click()
            await asyncio.sleep(0.3)
            
            # Type with human-like speed
            for char in password:
                await page.keyboard.type(char)
                await asyncio.sleep(0.07 + (asyncio.get_event_loop().time() % 0.03))
            
            await asyncio.sleep(0.6)
            await take_screenshot(page, "login_password_filled")
        except Exception as e:
            logger.warning(f"⚠️ Password field error: {e}")
            await take_screenshot(page, "login_ERROR_password_field_not_found")
            return

        # Human-like submit click
        await asyncio.sleep(0.4)
        await take_screenshot(page, "login_before_submit_click")
        
        try:
            submit_btn = page.locator('button[type="submit"]').last
            box = await submit_btn.bounding_box()
            if box:
                # Move mouse to button with steps (human-like)
                await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2, steps=15)
                await asyncio.sleep(0.3)
            
            await submit_btn.click()
            await take_screenshot(page, "login_submit_clicked")
        except Exception as e:
            logger.warning(f"⚠️ Submit click error: {e}")
            await page.locator('button[type="submit"]').last.click()
        
        logger.info("⏳ Waiting for login redirect...")

        # Wait until we're no longer on the auth page (with timeout)
        try:
            for i in range(20):  # 20 seconds max
                current_url = page.url
                if "/authenticate" not in current_url:
                    logger.info(f"✅ Redirected to: {current_url}")
                    break
                    
                # Check for CAPTCHA
                if await page.locator('iframe[src*="recaptcha"], div#captcha, div.captcha').count() > 0:
                    logger.warning("⚠️ CAPTCHA detected - pausing for manual intervention")
                    await asyncio.sleep(15)  # Give time for manual solving
                    
                await asyncio.sleep(1)
            
            await take_screenshot(page, "login_redirect_complete")
            
            # Check final status
            if "/authenticate" in page.url:
                logger.warning(f"⚠️ Login may have failed for {email} — still at: {page.url}")
                await take_screenshot(page, "login_ERROR_redirect_timeout")
            else:
                logger.info(f"✅ Logged in successfully as {email}! URL: {page.url}")
        except Exception as e:
            logger.warning(f"⚠️ Exception during login: {e}")

        await asyncio.sleep(2)
        await take_screenshot(page, "login_final_page")

        # Save cookies for THIS user only (per-user file)
        try:
            cookies = await page.context.cookies()
            COOKIE_FILE.write_text(json.dumps(cookies))
            logger.info(f"💾 Session cookies saved for {email} → {COOKIE_FILE}")
        except Exception as e:
            logger.warning(f"Could not save cookies for {email}: {e}")


    async def _click_apply_button(self, page: Page) -> bool:
        """Click apply button with human-like behavior"""
        for sel in [
            'button:has-text("Apply")',
            'button:has-text("Postuler")',
            'a:has-text("Apply now")',
            '[data-testid="apply-button"]',
            'button:has-text("Quick apply")',
        ]:
            try:
                loc = page.locator(sel).first
                if await loc.count() > 0 and await loc.is_visible():
                    logger.info(f"Clicking apply button: {sel}")
                    
                    # Scroll into view smoothly
                    await loc.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)
                    
                    # Get bounding box and move mouse naturally
                    box = await loc.bounding_box()
                    if box:
                        target_x = box['x'] + box['width'] / 2
                        target_y = box['y'] + box['height'] / 2
                        await page.mouse.move(target_x, target_y, steps=20)
                        await asyncio.sleep(0.3)
                    
                    await loc.click()
                    await asyncio.sleep(1.0)
                    return True
            except Exception as e:
                logger.debug(f"Apply button click failed for {sel}: {e}")
        return False

    async def _fill_wttj_modal(self, page: Page, profile_data: dict, email: str) -> int:
        """Fill WTTJ application modal form fields using direct field mapping (NO AI)"""
        filled = 0

        await take_screenshot(page, "fill_modal_start")

        # ── 1. Upload Resume (PDF only — targets resume input, NOT profile picture) ──
        # Build user-specific resume path from email
        email_slug = email.replace("@", "_").replace(".", "_")
        user_resume_pattern = os.path.abspath(
            os.path.join(os.path.dirname(__file__), f"../../../uploads/resumes/{email_slug}_professional_demo_resume.pdf")
        )
        
        # Ordered by preference — PDF only
        resume_paths = [
            profile_data.get("resume_path", ""),           # User's saved profile path
            user_resume_pattern,                            # Per-user upload (e.g. k45490335_gmail_com_...)
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../scratch/resume.pdf")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../test_resume.pdf")),
        ]
        valid_resume = next((p for p in resume_paths if p and os.path.exists(p) and p.lower().endswith(".pdf")), None)
        
        file_inputs = await page.locator('input[type="file"]').all()
        for fi in file_inputs:
            try:
                # Check what file types this input accepts
                accept_attr = (await fi.get_attribute("accept") or "").lower()
                
                # SKIP profile picture inputs — they only accept images (gif, jpeg, png, svg)
                is_image_input = (
                    "image" in accept_attr or
                    "jpg" in accept_attr or "jpeg" in accept_attr or
                    "png" in accept_attr or "gif" in accept_attr or "svg" in accept_attr
                ) and "pdf" not in accept_attr
                
                if is_image_input:
                    logger.info(f"⏭️ Skipping image/profile-picture file input (accept='{accept_attr}')")
                    continue
                
                # Check nearby label to further confirm it's a resume field
                fi_label = (await self._get_label(page, fi)).lower()
                is_profile_pic = any(k in fi_label for k in ["photo", "picture", "avatar", "profile pic", "image"])
                if is_profile_pic:
                    logger.info(f"⏭️ Skipping profile picture input (label='{fi_label}')")
                    continue
                
                # This is a resume/document input — upload PDF
                if valid_resume:
                    await fi.set_input_files(valid_resume)
                    filled += 1
                    logger.info(f"📁 Uploaded PDF resume to correct field: {os.path.basename(valid_resume)}")
                    await take_screenshot(page, "fill_resume_uploaded")
                else:
                    logger.warning("⚠️ No valid PDF resume found — skipping resume upload to avoid format error")
            except Exception as e:
                logger.debug(f"Skip file upload: {e}")





        # ── 2. Extract profile data ──────────────
        first_name   = profile_data.get("first_name", "")
        last_name    = profile_data.get("last_name", "")
        phone        = profile_data.get("phone", "+33 6 12 34 56 78")
        location     = profile_data.get("current_location") or profile_data.get("location", "Paris, France")
        title        = profile_data.get("current_title") or profile_data.get("title", "Software Engineer")
        linkedin     = profile_data.get("linkedin_url", "")
        github       = profile_data.get("github_url", "")
        portfolio    = profile_data.get("portfolio_url", "")
        availability = profile_data.get("availability", "Immediately")
        bio          = profile_data.get("bio", "")
        summary      = profile_data.get("summary", "")

        # Generate cover letter from profile
        cover_letter = profile_data.get("cover_letter_template") or profile_data.get("custom_pitch") or (
            f"Dear Hiring Team,\n\n"
            f"I am {first_name} {last_name}, a {title} based in {location}. "
            f"I am writing to express my strong interest in this position.\n\n"
            f"{bio[:300] if bio else 'I bring solid technical skills, a collaborative mindset, and a passion for building impactful products.'}\n\n"
            f"I am available {availability.lower()} and excited about the opportunity to contribute to your team.\n\n"
            f"Best regards,\n{first_name} {last_name}"
        )
        
        motivation = summary or (
            f"I am applying because this role aligns perfectly with my experience as a {title}. "
            f"I am excited about the opportunity to contribute my skills and grow within your organization."
        )

        # ── 3. Fill form fields systematically ──────────────

        # First Name
        for sel in ['input[name*="first" i]', 'input[name="firstName"]', 'input[placeholder*="first" i]', 'input[aria-label*="First" i]']:
            try:
                loc = page.locator(sel).first
                if await loc.count() > 0 and await loc.is_visible():
                    if not await loc.input_value():
                        await loc.fill(first_name); filled += 1; logger.info(f"✏️ First Name = {first_name}")
                    break
            except Exception: pass

        # Last Name
        for sel in ['input[name*="last" i]', 'input[name="lastName"]', 'input[placeholder*="last" i]', 'input[aria-label*="Last" i]']:
            try:
                loc = page.locator(sel).first
                if await loc.count() > 0 and await loc.is_visible():
                    if not await loc.input_value():
                        await loc.fill(last_name); filled += 1; logger.info(f"✏️ Last Name = {last_name}")
                    break
            except Exception: pass

        # Email
        for sel in ['input[type="email"]', 'input[name*="email" i]', 'input[placeholder*="email" i]']:
            try:
                loc = page.locator(sel).first
                if await loc.count() > 0 and await loc.is_visible():
                    if not await loc.input_value():
                        await loc.fill(email); filled += 1; logger.info(f"✏️ Email = {email}")
                    break
            except Exception: pass

        # Phone
        for sel in ['input[type="tel"]', 'input[name*="phone" i]', 'input[placeholder*="phone" i]', 'input[placeholder*="téléphone" i]']:
            try:
                loc = page.locator(sel).first
                if await loc.count() > 0 and await loc.is_visible():
                    if not await loc.input_value():
                        await loc.fill(phone); filled += 1; logger.info(f"✏️ Phone = {phone}")
                    break
            except Exception: pass

        # Location/City
        for sel in ['input[name*="city" i]', 'input[name*="location" i]', 'input[placeholder*="city" i]', 'input[placeholder*="ville" i]', 'input[aria-label*="City"]']:
            try:
                loc = page.locator(sel).first
                if await loc.count() > 0 and await loc.is_visible():
                    if not await loc.input_value():
                        await loc.fill(location); filled += 1; logger.info(f"✏️ Location = {location}")
                    break
            except Exception: pass

        # LinkedIn — always fill with valid URL (required by WTTJ)
        # Use saved URL if available, otherwise build a plausible LinkedIn URL
        linkedin_to_fill = linkedin
        if not linkedin_to_fill or not linkedin_to_fill.startswith("http"):
            linkedin_to_fill = f"https://www.linkedin.com/in/{first_name.lower()}-{last_name.lower()}"
        for sel in ['input[name*="linkedin" i]', 'input[placeholder*="linkedin" i]', 'input[aria-label*="linkedin" i]']:
            try:
                loc = page.locator(sel).first
                if await loc.count() > 0 and await loc.is_visible():
                    current = await loc.input_value()
                    if not current or not current.startswith("http"):
                        await loc.fill(linkedin_to_fill); filled += 1; logger.info(f"✏️ LinkedIn = {linkedin_to_fill}")
                    break
            except Exception: pass


        # GitHub
        if github:
            for sel in ['input[name*="github" i]', 'input[placeholder*="github" i]']:
                try:
                    loc = page.locator(sel).first
                    if await loc.count() > 0 and await loc.is_visible():
                        if not await loc.input_value():
                            await loc.fill(github); filled += 1; logger.info(f"✏️ GitHub = {github}")
                        break
                except Exception: pass

        # Portfolio/Website
        if portfolio:
            for sel in ['input[name*="portfolio" i]', 'input[name*="website" i]', 'input[placeholder*="portfolio" i]']:
                try:
                    loc = page.locator(sel).first
                    if await loc.count() > 0 and await loc.is_visible():
                        if not await loc.input_value():
                            await loc.fill(portfolio); filled += 1; logger.info(f"✏️ Portfolio = {portfolio}")
                        break
                except Exception: pass

        # Yes/No radios (assume yes for eligibility questions)
        for sel in ['input[type="radio"][value="true"]', 'input[type="radio"][value="yes"]', 'input[type="radio"][value="Yes"]']:
            try:
                radios = await page.locator(sel).all()
                for radio in radios:
                    if await radio.is_visible() and not await radio.is_checked():
                        await radio.check(); filled += 1
                        logger.info(f"✅ Checked YES radio")
            except Exception: pass
            
        for yes_label in ['label:has-text("Yes")', 'label:has-text("Oui")']:
            try:
                labels = await page.locator(yes_label).all()
                for lbl in labels:
                    if await lbl.is_visible():
                        await lbl.click(); await asyncio.sleep(0.3); filled += 1
                        logger.info(f"✅ Clicked YES label"); break
            except Exception: pass

        # Textareas (cover letter, motivation)
        textareas = await page.locator("textarea:visible").all()
        textarea_count = 0
        for ta in textareas:
            try:
                current = await ta.input_value()
                if current: continue
                label = await self._get_label(page, ta)
                label_lower = label.lower()
                if any(k in label_lower for k in ["cover", "letter", "lettre"]):
                    answer = cover_letter
                elif any(k in label_lower for k in ["motiv", "why", "pourquoi"]):
                    answer = motivation
                else:
                    answer = motivation
                await ta.fill(answer); filled += 1
                textarea_count += 1
                logger.info(f"✏️ Filled textarea: {label[:40]}")
                await take_screenshot(page, f"fill_textarea_{textarea_count}")
            except Exception as e:
                logger.debug(f"Skip textarea: {e}")

        # Sweep remaining empty text inputs
        # IMPORTANT: Skip URL/social fields to avoid Invalid URL errors
        # IMPORTANT: Skip optional text fields that may cause validation errors with generic text
        url_skip_keywords = ["twitter", "facebook", "website", "portfolio", "github", "instagram", "x.com", "social"]
        
        all_inputs = await page.locator('input:not([type="hidden"]):not([type="file"]):not([type="radio"]):not([type="checkbox"]):visible').all()
        for inp in all_inputs:
            try:
                if not await inp.input_value():
                    inp_type = await inp.get_attribute("type") or "text"
                    inp_name  = (await inp.get_attribute("name")  or "").lower()
                    inp_placeholder = (await inp.get_attribute("placeholder") or "").lower()
                    inp_label = await self._get_label(page, inp)
                    inp_label_lower = inp_label.lower()
                    inp_required = await inp.get_attribute("required")
                    inp_aria_req = await inp.get_attribute("aria-required")
                    is_required = inp_required is not None or inp_aria_req == "true"
                    
                    # LinkedIn field — always fill with valid URL
                    if "linkedin" in inp_name or "linkedin" in inp_placeholder or "linkedin" in inp_label_lower:
                        await inp.fill(linkedin_to_fill)
                        filled += 1
                        logger.info(f"✏️ Filled LinkedIn field in sweep: {linkedin_to_fill}")
                        continue
                    
                    # Skip URL-type inputs that are NOT LinkedIn (website, twitter, etc.)
                    if inp_type == "url":
                        if is_required:
                            # Required URL field — fill with linkedin as fallback
                            await inp.fill(linkedin_to_fill)
                            filled += 1
                            logger.info(f"✏️ Filled required URL field with LinkedIn fallback: {inp_name or inp_placeholder}")
                        else:
                            logger.info(f"⏭️ Skipping optional URL field: {inp_name or inp_placeholder}")
                        continue
                    
                    # Skip fields that are clearly optional social/url fields by name/placeholder/label
                    if any(kw in inp_name or kw in inp_placeholder or kw in inp_label_lower for kw in url_skip_keywords):
                        if is_required:
                            await inp.fill(linkedin_to_fill)
                            filled += 1
                            logger.info(f"✏️ Filled required social field with LinkedIn fallback: {inp_name or inp_placeholder}")
                        else:
                            logger.info(f"⏭️ Skipping optional social/URL field: {inp_name or inp_placeholder}")
                        continue
                    
                    if inp_type == "number":
                        await inp.fill("0")
                    elif inp_type == "email":
                        await inp.fill(email)
                    elif inp_type == "tel":
                        # Phone field — use real phone if available
                        if phone and phone != "N/A":
                            await inp.fill(phone)
                        else:
                            continue  # Skip if no real phone number
                    else:
                        # For generic text fields, only fill required ones
                        if is_required:
                            await inp.fill("Not specified")
                        else:
                            continue  # Skip optional fields
                    filled += 1
                    logger.info(f"✏️ Filled remaining {inp_type} input: {inp_name or inp_placeholder}")
            except Exception: pass

            
        # Sweep remaining empty dropdowns
        all_selects = await page.locator('select:visible').all()
        for sel_el in all_selects:
            try:
                val = await sel_el.input_value()
                if not val or val == "0" or val == "":
                    await sel_el.select_option(index=1)
                    filled += 1
                    logger.info(f"✅ Selected first valid option in dropdown")
            except Exception: pass
                
        await take_screenshot(page, f"fill_complete_{filled}_fields")

        # ── 4. Accept all terms and checkboxes ────────
        await take_screenshot(page, "fill_before_accept_terms")
        await self._accept_terms(page)
        await take_screenshot(page, "fill_after_accept_terms")

        await take_screenshot(page, "fill_all_complete_final")
        
        return filled

    async def _accept_terms(self, page: Page):
        """Accept terms of service and any required consent checkboxes."""
        consent_keywords = [
            "terms", "service", "agree", "accept", "consent", "rgpd",
            "gdpr", "privacy", "policy", "certify", "confirm", "authorize",
            "autorise", "cgu", "conditions",
        ]
        checkboxes = await page.locator('input[type="checkbox"]').all()
        for cb in checkboxes:
            try:
                if not await cb.is_visible():
                    continue
                label = (await self._get_label(page, cb)).lower()
                if any(k in label for k in consent_keywords) or label == "":
                    # Accept all unchecked boxes (many WTTJ forms have required terms with no label)
                    if not await cb.is_checked():
                        await cb.check()
                        logger.info(f"☑️ Accepted: {label[:50] or '(unlabeled)'}")
            except Exception:
                pass

    async def _submit_form(self, page: Page) -> bool:
        """Find and click the submit button, then verify no validation errors remain."""
        selectors = [
            # WTTJ specific
            'button:has-text("Submit my application")',
            'button:has-text("Envoyer ma candidature")',
            'button:has-text("Send my application")',
            'button:has-text("Send application")',
            'button:has-text("Submit application")',
            # Generic
            'button[type="submit"]:has-text("Submit")',
            'button[type="submit"]:has-text("Send")',
            'button[type="submit"]:has-text("Apply")',
            'button[type="submit"]:has-text("Postuler")',
            '[data-testid="submit-application"]',
            'button[type="submit"]',
        ]
        for sel in selectors:
            try:
                loc = page.locator(sel).last
                if await loc.count() > 0 and await loc.is_visible():
                    logger.info(f"🖱️ Clicking submit: {sel}")
                    
                    # Scroll to button
                    await loc.scroll_into_view_if_needed()
                    await asyncio.sleep(0.6)
                    
                    # Move mouse to button naturally
                    box = await loc.bounding_box()
                    if box:
                        target_x = box['x'] + box['width'] / 2
                        target_y = box['y'] + box['height'] / 2
                        await page.mouse.move(target_x, target_y, steps=25)
                        await asyncio.sleep(0.4)
                    
                    # Final pause before submitting (human hesitation)
                    await asyncio.sleep(0.8)
                    
                    await loc.click()
                    
                    # ── Wait then check for validation errors ────────────────
                    logger.info("⏳ Waiting 4 seconds to check for validation errors...")
                    await asyncio.sleep(4)
                    await take_screenshot(page, "after_submit_4sec_check")
                    
                    # Collect all visible validation errors
                    error_selectors = [
                        "[aria-invalid='true']",
                        "[class*='error' i]:not(script):not(style)",
                        "[class*='invalid' i]:not(script):not(style)",
                        "p:has-text('required')",
                        "span:has-text('required')",
                        "div:has-text('required')",
                        "p:has-text('is required')",
                        "span:has-text('is required')",
                        "p:has-text('This field')",
                        "[role='alert']",
                    ]
                    
                    visible_errors = []
                    for err_sel in error_selectors:
                        try:
                            err_els = await page.locator(err_sel).all()
                            for err_el in err_els:
                                if await err_el.is_visible():
                                    err_text = (await err_el.inner_text()).strip()
                                    if err_text and len(err_text) < 200 and err_text not in visible_errors:
                                        visible_errors.append(err_text)
                        except Exception:
                            pass
                    
                    if visible_errors:
                        logger.warning(f"❌ Validation errors detected after submit ({len(visible_errors)} errors):")
                        for i, err in enumerate(visible_errors, 1):
                            logger.warning(f"   {i}. {err}")
                        await update_live_state(
                            step_name="Validation Errors",
                            step_index=5,
                            progress=90,
                            url=page.url,
                            log_msg=f"❌ {len(visible_errors)} field error(s): {' | '.join(visible_errors[:3])}",
                            page=page
                        )
                        await take_screenshot(page, "ERRORS_validation_failed")
                        return False
                    
                    # Check for success indicators
                    success_indicators = [
                        "text=Application sent",
                        "text=Candidature envoyée",
                        "text=Thank you",
                        "text=Merci",
                        "text=successfully submitted",
                        "text=Application submitted",
                        "[class*='success' i]",
                        "[data-testid*='success']",
                    ]
                    for succ_sel in success_indicators:
                        try:
                            succ_el = page.locator(succ_sel).first
                            if await succ_el.count() > 0 and await succ_el.is_visible():
                                logger.info(f"🎉 Success indicator found: {succ_sel}")
                                await take_screenshot(page, "SUCCESS_confirmed")
                                return True
                        except Exception:
                            pass
                    
                    # If no errors and no explicit success message → assume success
                    logger.info("✅ No validation errors found — assuming application submitted successfully")
                    return True
            except Exception as e:
                logger.debug(f"Submit attempt failed for {sel}: {e}")
        return False

    async def _get_label(self, page: Page, element: Locator) -> str:
        """Get the human-readable label for a form element."""
        try:
            aria = await element.get_attribute("aria-label")
            if aria:
                return aria

            fid = await element.get_attribute("id")
            if fid:
                lbl = page.locator(f'label[for="{fid}"]')
                if await lbl.count() > 0:
                    return await lbl.first.inner_text()

            placeholder = await element.get_attribute("placeholder")
            if placeholder:
                return placeholder

            name = await element.get_attribute("name")
            if name:
                return name.replace("_", " ").replace("-", " ")

            parent = await element.evaluate(
                "(el) => el.closest('div, fieldset, label, li, section')?.innerText || ''"
            )
            return (parent or "")[:150]
        except Exception:
            return ""
