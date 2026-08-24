# Swipe-Triggered Automation Flow (NO AI)

## Overview
When a user swipes right on a job in the JobSwipe UI, the system automatically applies to that job using their saved WTTJ credentials and profile data. The entire process uses **direct field mapping** with no AI involved.

## Architecture

```
User Swipes Right
       ↓
Frontend (JobSwipe.tsx)
       ↓
POST /swipe-job → API Gateway (Port 8000)
       ↓
POST /swipe-apply → WTTJ Service (Port 8012)
       ↓
SwipeAutomationHandler
       ↓
WTTJFirefoxApplier (NO AI)
       ↓
Firefox Browser Automation
       ↓
WTTJ Login → Navigate to Job → Fill Form → Submit
```

## Flow Steps

### 1. User Swipes Right
- User sees a job in the JobSwipe interface
- User swipes right or clicks "Apply"
- Frontend sends request to `/swipe-job`

### 2. API Gateway Routes Request
**File:** `api_gateway.py`
**Endpoint:** `POST /swipe-job`

```python
@app.post("/swipe-job")
async def swipe_job(request: Request):
    # Extracts: user_id, job_id, job_url, action
    # Routes to WTTJ service: POST /swipe-apply
```

### 3. WTTJ Service Handles Swipe
**File:** `services/wttj/app/main.py`
**Endpoint:** `POST /swipe-apply`

```python
@app.post("/swipe-apply")
async def swipe_and_apply(request: dict, db: SessionLocal = Depends(get_db)):
    # Uses SwipeAutomationHandler
    # Retrieves credentials and profile
    # Triggers Firefox automation
```

### 4. Swipe Handler Processes Request
**File:** `services/wttj/app/swipe_handler.py`
**Class:** `SwipeAutomationHandler`

**What it does:**
1. ✅ Retrieves saved WTTJ credentials from database
2. ✅ Gets user profile data (name, phone, location, etc.)
3. ✅ Creates application record (status: pending)
4. ✅ Triggers Firefox automation
5. ✅ Updates application status based on result

```python
async def handle_swipe_right(user_id, job_id, job_url, db_session):
    # 1. Get credentials
    credential = db_session.query(Credential).filter(...)
    
    # 2. Get profile
    profile = db_session.query(UserProfile).filter(...)
    
    # 3. Build profile data dict
    profile_data = {
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "phone": profile.phone,
        "location": profile.current_location,
        # ... etc
    }
    
    # 4. Trigger automation
    applier = WTTJFirefoxApplier()
    result = await applier.apply_to_job(...)
    
    # 5. Update status
    application.status = "submitted" if result["success"] else "failed"
```

### 5. Firefox Automation Executes
**File:** `services/wttj/app/wttj_firefox_applier.py`
**Class:** `WTTJFirefoxApplier`

**NO AI - Pure selector-based form filling**

```python
async def apply_to_job(email, password, job_url, profile_data, headless=False):
    # 1. Launch Firefox (visible browser)
    browser = await playwright.firefox.launch(headless=False)
    
    # 2. Login to WTTJ
    await self._login(page, email, password)
    
    # 3. Navigate to job URL
    await page.goto(job_url)
    
    # 4. Click "Apply" button
    await self._click_apply_button(page)
    
    # 5. Fill application form (NO AI)
    await self._fill_wttj_modal(page, profile_data, email)
    
    # 6. Accept terms
    await self._accept_terms(page)
    
    # 7. Submit application
    await self._submit_form(page)
```

## Form Filling Logic (NO AI)

The `_fill_wttj_modal` method uses **hardcoded selector-based filling**:

### Field Mapping
```python
# First Name
for sel in ['input[name*="first" i]', 'input[name="firstName"]', ...]:
    await page.fill(sel, profile_data["first_name"])

# Last Name  
for sel in ['input[name*="last" i]', 'input[name="lastName"]', ...]:
    await page.fill(sel, profile_data["last_name"])

# Email
for sel in ['input[type="email"]', 'input[name*="email" i]', ...]:
    await page.fill(sel, email)

# Phone
for sel in ['input[type="tel"]', 'input[name*="phone" i]', ...]:
    await page.fill(sel, profile_data["phone"])

# Location
for sel in ['input[name*="city" i]', 'input[name*="location" i]', ...]:
    await page.fill(sel, profile_data["location"])

# LinkedIn
if profile_data["linkedin_url"]:
    for sel in ['input[name*="linkedin" i]', ...]:
        await page.fill(sel, profile_data["linkedin_url"])

# Cover Letter / Motivation
textareas = await page.locator("textarea:visible").all()
for ta in textareas:
    label = await self._get_label(page, ta)
    if "cover" in label.lower():
        await ta.fill(cover_letter)
    else:
        await ta.fill(motivation)

# Yes/No Radios (assume YES for eligibility)
for sel in ['input[type="radio"][value="true"]', ...]:
    radios = await page.locator(sel).all()
    for radio in radios:
        await radio.check()

# Resume Upload
file_inputs = await page.locator('input[type="file"]').all()
await file_input.set_input_files(profile_data["resume_path"])
```

### Cover Letter Generation
**NO AI - Template-based:**

```python
cover_letter = f"""Dear Hiring Team,

I am {first_name} {last_name}, a {title} based in {location}. 
I am writing to express my strong interest in this position.

{bio[:300] if bio else 'I bring solid technical skills...'}

I am available {availability.lower()} and excited about the opportunity.

Best regards,
{first_name} {last_name}"""
```

## Cookie Handling & Anti-Bot Bypass

### Session Persistence
```python
COOKIE_FILE = pathlib.Path("scratch/wttj_session.json")

# Save cookies after successful login
cookies = await page.context.cookies()
COOKIE_FILE.write_text(json.dumps(cookies))

# Restore cookies for future runs
if COOKIE_FILE.exists():
    cookies = json.loads(COOKIE_FILE.read_text())
    await page.context.add_cookies(cookies)
```

### Cookie Banner Dismissal
```python
async def _dismiss_cookies(self, page: Page):
    for sel in [
        'button#axeptio_btn_acceptAll',
        'button:has-text("OK for me")',
        'button:has-text("Accept all")',
        'button:has-text("Tout accepter")',
    ]:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible():
                await btn.click()
                break
        except Exception:
            pass
```

## Database Schema

### Credentials Table
```sql
CREATE TABLE credentials (
    id VARCHAR PRIMARY KEY,
    candidate_id VARCHAR,
    careerSite VARCHAR,  -- "WTTJ"
    email VARCHAR,
    password VARCHAR,
    isVerified BOOLEAN,
    created_at TIMESTAMP
);
```

### User Profile Table
```sql
CREATE TABLE user_profiles (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR,
    first_name VARCHAR,
    last_name VARCHAR,
    phone VARCHAR,
    current_location VARCHAR,
    current_title VARCHAR,
    linkedin_url VARCHAR,
    github_url VARCHAR,
    portfolio_url VARCHAR,
    bio TEXT,
    summary TEXT,
    cover_letter_template TEXT,
    resume_path VARCHAR,
    availability VARCHAR,
    skills JSON
);
```

### Applications Table
```sql
CREATE TABLE applications (
    id VARCHAR PRIMARY KEY,
    candidate_id VARCHAR,
    job_id VARCHAR,
    status VARCHAR,  -- "pending", "submitted", "failed"
    application_method VARCHAR,  -- "Automated - Firefox"
    applied_at TIMESTAMP
);
```

## API Endpoints

### Frontend → Gateway
```http
POST /swipe-job
Content-Type: application/json

{
    "user_id": "user_123",
    "job_id": "job_456",
    "job_url": "https://www.welcometothejungle.com/en/companies/inato/jobs/...",
    "action": "apply"
}
```

### Gateway → WTTJ Service
```http
POST http://localhost:8012/swipe-apply
Content-Type: application/json

{
    "user_id": "user_123",
    "candidate_id": "user_123",
    "job_id": "job_456",
    "job_url": "https://www.welcometothejungle.com/en/companies/inato/jobs/...",
    "action": "apply"
}
```

### Response
```json
{
    "success": true,
    "message": "Application submitted via Firefox automation",
    "application_id": "app_789",
    "job_url": "https://...",
    "email": "user@example.com",
    "fields_filled": 15,
    "automation_method": "Firefox (No AI - Direct Field Mapping)",
    "status": "submitted",
    "timestamp": "2026-08-20T10:30:00Z"
}
```

## Error Handling

### No Credentials
```json
{
    "success": false,
    "error": "No WTTJ credentials found",
    "message": "Please connect your WTTJ account first",
    "action_required": "connect_wttj_account"
}
```

### Unverified Credentials
```json
{
    "success": false,
    "error": "WTTJ credentials not verified",
    "message": "Please verify your WTTJ account credentials",
    "action_required": "verify_wttj_account"
}
```

### Automation Failure
```json
{
    "success": false,
    "message": "Apply button not found",
    "job_url": "https://...",
    "status": "failed"
}
```

## Configuration

### Browser Settings
```python
# Visible browser (so user can see the magic!)
headless = False

# Firefox with realistic user agent
browser = await playwright.firefox.launch(headless=False)
context = await browser.new_context(
    viewport={"width": 1280, "height": 900},
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
)
```

### Timeouts
```python
# Page navigation
await page.goto(job_url, timeout=60000)  # 60 seconds

# Network idle
await page.wait_for_load_state("networkidle", timeout=15000)  # 15 seconds

# Login redirect
for _ in range(15):  # 15 seconds total
    if "/authenticate" not in page.url:
        break
    await asyncio.sleep(1)
```

## Testing

### Manual Test Flow
1. Start all services
2. Create WTTJ account for test user
3. Verify credentials in database
4. Navigate to JobSwipe UI
5. Swipe right on a job
6. Watch Firefox browser open and apply automatically
7. Verify application in database

### Test Endpoint
```bash
curl -X POST http://localhost:8000/swipe-job \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "job_url": "https://www.welcometothejungle.com/en/companies/inato/jobs/senior-product-engineer_paris_INATO_7ZmJa0k",
    "action": "apply"
  }'
```

## Screenshots & Logging

The automation takes screenshots at every major step:

```
screenshots/apply_debug/
  step_01_browser_launched.png
  step_02_after_login.png
  step_03_job_page_initial_load.png
  step_04_after_dismiss_cookies.png
  step_05_before_click_apply.png
  step_06_after_click_apply.png
  step_07_modal_fully_opened.png
  step_08_before_filling_form.png
  step_09_fill_resume_uploaded.png
  step_10_after_filling_form.png
  step_11_before_submit.png
  step_12_immediately_after_submit_click.png
  step_13_SUCCESS_final_page.png
```

## Advantages of NO AI Approach

✅ **Fast** - No API calls to AI services
✅ **Reliable** - Predictable behavior with selector-based filling
✅ **Cost-effective** - No AI API costs
✅ **Transparent** - Easy to debug and understand
✅ **Privacy** - No data sent to external AI services
✅ **Deterministic** - Same input = same output
✅ **Maintainable** - Simple to update selectors when UI changes

## Key Files

- `services/wttj/app/wttj_firefox_applier.py` - Firefox automation (NO AI)
- `services/wttj/app/swipe_handler.py` - Swipe event handler
- `services/wttj/app/main.py` - WTTJ service endpoints
- `api_gateway.py` - Gateway routing
- `shared/models.py` - Database models

## Future Enhancements

1. **Parallel Applications** - Apply to multiple jobs simultaneously
2. **Application Tracking** - Real-time status updates in UI
3. **Smart Retry** - Automatic retry on transient failures
4. **Success Rate Metrics** - Track automation success rates
5. **Multi-Platform** - Extend to LinkedIn, Indeed, etc.
