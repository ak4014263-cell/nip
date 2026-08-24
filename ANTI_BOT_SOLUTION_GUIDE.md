# Anti-Bot Detection Solution for WTTJ Automation

## Problem: "Button click: Manual" Error

This error occurs when Apify's browser automation framework detects that WTTJ's anti-bot system has blocked automated button clicks. The site uses fingerprinting to detect headless browsers and automation tools.

## Solutions Implemented

We've implemented **three complementary strategies** to bypass anti-bot detection:

---

## Strategy A: Stealth Browser Automation ✅ RECOMMENDED

### What it does
- Uses Playwright with advanced anti-detection techniques
- Simulates human-like behavior (mouse movements, typing delays, scrolling)
- Masks automation fingerprints (navigator.webdriver, plugins, etc.)

### Implementation
File: `services/automation/app/stealth_browser.py`

### Features
- ✅ Removes `navigator.webdriver` property
- ✅ Mocks realistic browser plugins
- ✅ Human-like typing with random delays and typos
- ✅ Random mouse movements and scrolling
- ✅ Realistic timing between actions
- ✅ Proper User-Agent and browser fingerprint

### Usage
```python
from stealth_browser import StealthBrowser, HumanBehaviorSimulator

browser = StealthBrowser(headless=False)
page = await browser.launch()

# Navigate with human behavior
await page.goto('https://www.welcometothejungle.com/...')
await HumanBehaviorSimulator.reading_pause(3, 5)

# Human-like typing
await browser.human_like_type('input[type="email"]', 'test@example.com')

# Human-like click
await browser.human_like_click('button[type="submit"]')
```

### When to use
- ✅ Best for: Standard forms, account creation, applications
- ✅ Reliability: High
- ✅ Bypasses most anti-bot systems
- ❌ Slower than API approach

---

## Strategy B: WelcomeKit API Integration ⚡ FASTEST

### What it does
- Direct API calls to WTTJ's backend (WelcomeKit)
- No browser needed = No bot detection
- Based on official documentation: https://developers.welcomekit.co/

### Implementation
File: `services/automation/app/wttj_api_client.py`

### Features
- ✅ Create candidate profiles
- ✅ Submit job applications
- ✅ Search jobs
- ✅ Update profiles
- ✅ No CAPTCHA or anti-bot issues
- ✅ Fastest method

### Usage
```python
from wttj_api_client import WTTJAPIClient

api = WTTJAPIClient(api_key="your_api_key")

# Create candidate
result = await api.create_candidate(
    email="john@example.com",
    first_name="John",
    last_name="Doe",
    phone="+33612345678"
)

# Apply to job
result = await api.apply_to_job(
    job_reference="job_ref_123",
    email="john@example.com",
    first_name="John",
    last_name="Doe",
    cover_letter="Dear hiring manager..."
)
```

### When to use
- ✅ Best for: High-volume automation, production systems
- ✅ Reliability: Excellent
- ✅ Speed: Instant (no browser overhead)
- ❌ Requires API key/credentials

---

## Strategy C: Algolia Direct Access 🔍 NO AUTH NEEDED

### What it does
- Direct access to WTTJ's Algolia-powered search
- Public API, no authentication required
- Bypasses web scraping entirely

### Implementation
File: `services/automation/app/wttj_api_client.py` (AlgoliaJobSearchClient)

### Features
- ✅ Search jobs without scraping
- ✅ No API key required
- ✅ Fast and reliable
- ✅ Rich filtering options

### Usage
```python
from wttj_api_client import AlgoliaJobSearchClient

algolia = AlgoliaJobSearchClient()

result = await algolia.search_jobs(
    query="Python Developer",
    location="Paris",
    contract_type="full_time",
    hits_per_page=20
)

print(f"Found {result['total_results']} jobs")
for job in result['jobs']:
    print(f"- {job['name']} at {job['organization']['name']}")
```

### When to use
- ✅ Best for: Job search and discovery
- ✅ Reliability: Excellent
- ✅ No authentication needed
- ✅ Faster than scraping

---

## Enhanced Adapter: Intelligent Strategy Selection

File: `services/automation/app/adapters/wttj_enhanced_adapter.py`

### What it does
Automatically selects the best strategy for each operation:

**Account Creation:**
1. Try API if available → 2. Fall back to stealth browser

**Job Search:**
1. Algolia direct access → 2. API fallback → 3. Browser scraping

**Job Application:**
1. Try API if job reference available → 2. Stealth browser automation

### Usage
```python
from adapters.wttj_enhanced_adapter import WTTJEnhancedAdapter

adapter = WTTJEnhancedAdapter(
    api_key="optional_api_key",
    use_stealth=True,
    headless=False
)

# Create account (automatically selects best method)
result = await adapter.create_account(
    email="test@example.com",
    password="SecurePass123!",
    first_name="John",
    last_name="Doe"
)

# Search jobs (automatically uses Algolia)
jobs = await adapter.search_jobs(
    query="Python",
    location="Paris"
)

# Apply to job (automatically selects best method)
result = await adapter.apply_to_job(
    job_url="https://www.welcometothejungle.com/en/jobs/...",
    email="test@example.com",
    first_name="John",
    last_name="Doe"
)
```

---

## Installation

### Python Dependencies
```bash
pip install playwright playwright-stealth httpx
python -m playwright install chromium
```

### Optional: Residential Proxies
For maximum reliability, consider using residential proxies:

1. **Bright Data** (formerly Luminati)
2. **Smartproxy**
3. **Oxylabs**

Configure in `stealth_browser.py`:
```python
def _get_proxy_config(self) -> Optional[Dict[str, Any]]:
    return {
        'server': 'http://proxy.example.com:8080',
        'username': 'your_username',
        'password': 'your_password'
    }
```

---

## Comparison Table

| Method | Speed | Reliability | Anti-Bot Bypass | Setup Difficulty |
|--------|-------|-------------|-----------------|------------------|
| **Stealth Browser** | Medium | High | ✅ Excellent | Easy |
| **WelcomeKit API** | ⚡ Fast | Excellent | ✅ N/A (No bot detection) | Medium (needs API key) |
| **Algolia Search** | ⚡ Fast | Excellent | ✅ N/A (Public API) | Easy |
| **Standard Playwright** | Medium | Low | ❌ Detected | Easy |
| **Selenium (old)** | Slow | Very Low | ❌ Always detected | Easy |

---

## Best Practices

### 1. For Account Creation
```python
# BEST: Use enhanced adapter (tries API first, falls back to stealth)
adapter = WTTJEnhancedAdapter(api_key=api_key, headless=False)
result = await adapter.create_account(email, password, first_name, last_name)
```

### 2. For Job Search
```python
# BEST: Use Algolia directly (fastest, no auth needed)
algolia = AlgoliaJobSearchClient()
jobs = await algolia.search_jobs(query="Python", location="Paris")
```

### 3. For Job Applications
```python
# BEST: Try API first if you have credentials
if has_api_key:
    api = WTTJAPIClient(api_key)
    result = await api.apply_to_job(job_ref, email, first_name, last_name)
else:
    # Use stealth browser
    browser = StealthBrowser(headless=False)
    # ... apply via browser
```

### 4. For Mass Automation
```python
# Use enhanced adapter with all strategies enabled
adapter = WTTJEnhancedAdapter(
    api_key=your_api_key,  # Optional but recommended
    use_stealth=True,
    headless=True  # Set to False for debugging
)

# It will automatically route to best strategy
for job in jobs:
    result = await adapter.apply_to_job(job_url, ...)
```

---

## Debugging Tips

### If stealth browser is still detected:

1. **Run in headed mode first:**
   ```python
   browser = StealthBrowser(headless=False)
   ```

2. **Add more human behavior:**
   ```python
   await browser.random_mouse_movement()
   await browser.random_scroll()
   await HumanBehaviorSimulator.reading_pause(5, 10)
   ```

3. **Use residential proxies:**
   ```python
   browser = StealthBrowser(headless=False, use_residential_proxy=True)
   ```

4. **Check browser fingerprint:**
   - Visit: https://bot.sannysoft.com/
   - Check for any red flags

### If API calls fail:

1. **Verify API key:**
   ```python
   api = WTTJAPIClient(api_key="your_actual_key")
   result = await api.get_candidate_profile("test_id")
   ```

2. **Check rate limits:**
   - Add delays between requests
   - Implement exponential backoff

3. **Fall back to browser:**
   ```python
   if not result["success"]:
       # Use stealth browser as fallback
   ```

---

## Next Steps

1. **Test stealth browser:**
   ```bash
   python services/automation/app/stealth_browser.py
   ```

2. **Test API client:**
   ```bash
   python services/automation/app/wttj_api_client.py
   ```

3. **Test enhanced adapter:**
   ```bash
   python services/automation/app/adapters/wttj_enhanced_adapter.py
   ```

4. **Integrate into your automation service:**
   - Update `services/automation/app/main.py`
   - Replace old browser automation with enhanced adapter
   - Test with real accounts

---

## Support

For issues or questions:
1. Check logs for detailed error messages
2. Run in non-headless mode to see what's happening
3. Verify all dependencies are installed
4. Test API connectivity first, then fall back to browser

---

## License & Credits

- Playwright Stealth techniques based on industry best practices
- WelcomeKit API documentation: https://developers.welcomekit.co/
- Algolia integration uses WTTJ's public search index
