#!/usr/bin/env python3
"""
CSRF Token Extractor for WTTJ
Extracts CSRF tokens and other authentication artifacts
"""
import asyncio
import re
import json
import logging
from typing import Dict, Optional, Tuple, List
from playwright.async_api import async_playwright, Page
import tls_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSRFExtractor:
    """Extracts CSRF tokens and authentication data from WTTJ"""
    
    def __init__(self):
        self.base_url = "https://www.welcometothejungle.com"
        self.api_url = "https://api.welcometothejungle.com"
    
    async def extract_via_playwright(self, page: Page) -> Dict:
        """Extract tokens from page using Playwright"""
        try:
            logger.info("🔍 Extracting tokens via Playwright...")
            
            page_content = await page.content()
            
            tokens = {}
            
            # Pattern 1: CSRF in script tag (window object)
            csrf_patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.*?"csrf".*?})',
                r'"csrf"\s*:\s*"([^"]+)"',
                r'csrf["\']?\s*:\s*["\']([^"\']+)["\']',
                r'window\.csrf\s*=\s*["\']([^"\']+)["\']',
                r'csrfToken\s*[=:]\s*["\']([^"\']+)["\']',
            ]
            
            for pattern in csrf_patterns:
                match = re.search(pattern, page_content, re.IGNORECASE)
                if match:
                    if 'csrf' in tokens:
                        continue
                    token = match.group(1) if match.lastindex else match.group(1)
                    if len(token) > 10:  # Likely a real token
                        tokens['csrf'] = token
                        logger.info(f"✅ Found CSRF token: {token[:20]}...")
                        break
            
            # Pattern 2: CSRF in meta tag
            meta_csrf_match = re.search(r'<meta\s+name="csrf"\s+content="([^"]+)"', page_content)
            if meta_csrf_match and 'csrf' not in tokens:
                tokens['csrf'] = meta_csrf_match.group(1)
                logger.info(f"✅ Found CSRF in meta tag: {tokens['csrf'][:20]}...")
            
            # Pattern 3: CSRF in form hidden input
            form_csrf_match = re.search(r'<input[^>]*name="csrf"[^>]*value="([^"]+)"', page_content)
            if form_csrf_match and 'csrf' not in tokens:
                tokens['csrf'] = form_csrf_match.group(1)
                logger.info(f"✅ Found CSRF in form: {tokens['csrf'][:20]}...")
            
            # Pattern 4: API key or authentication token
            api_token_patterns = [
                r'"token"\s*:\s*"([^"]+)"',
                r'"accessToken"\s*:\s*"([^"]+)"',
                r'"authToken"\s*:\s*"([^"]+)"',
            ]
            
            for pattern in api_token_patterns:
                match = re.search(pattern, page_content)
                if match:
                    tokens['auth_token'] = match.group(1)
                    logger.info(f"✅ Found auth token: {tokens['auth_token'][:20]}...")
                    break
            
            # Extract cookies
            cookies = await page.context.cookies()
            token_cookies = {}
            
            for cookie in cookies:
                if any(keyword in cookie['name'].lower() for keyword in ['csrf', 'token', 'auth', 'session']):
                    token_cookies[cookie['name']] = cookie['value']
                    logger.info(f"🍪 Found token cookie: {cookie['name']}")
            
            tokens['cookies'] = token_cookies
            
            # Extract form data
            form_data = await page.evaluate("""() => {
                const forms = document.querySelectorAll('form');
                const data = [];
                forms.forEach(form => {
                    const inputs = form.querySelectorAll('input[type="hidden"]');
                    const formData = {};
                    inputs.forEach(input => {
                        formData[input.name] = input.value;
                    });
                    if (Object.keys(formData).length > 0) {
                        data.push(formData);
                    }
                });
                return data;
            }""")
            
            if form_data:
                tokens['form_data'] = form_data
                logger.info(f"📋 Found {len(form_data)} hidden form fields")
            
            return tokens
            
        except Exception as e:
            logger.error(f"❌ Error extracting via Playwright: {e}")
            return {}
    
    async def extract_via_network_interception(self) -> Dict:
        """Extract tokens by intercepting network requests"""
        try:
            logger.info("🔍 Extracting tokens via network interception...")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                captured_requests = []
                
                # Intercept requests
                async def handle_route(route):
                    request = route.request
                    captured_requests.append({
                        'url': request.url,
                        'method': request.method,
                        'headers': dict(request.headers),
                        'body': request.post_data,
                    })
                    await route.continue_()
                
                await page.route('**/*', handle_route)
                
                # Navigate to signup
                await page.goto(f"{self.base_url}/en/authenticate/signup", wait_until="networkidle")
                await asyncio.sleep(2)
                
                await browser.close()
                
                tokens = {}
                
                # Extract tokens from request headers
                for req in captured_requests:
                    headers = req['headers']
                    
                    # Check for CSRF token in headers
                    for header_name in ['x-csrf-token', 'x-requested-with', 'authorization']:
                        if header_name in headers:
                            tokens[header_name.replace('-', '_')] = headers[header_name]
                            logger.info(f"✅ Found header token {header_name}: {headers[header_name][:20]}...")
                
                return tokens
                
        except Exception as e:
            logger.error(f"❌ Error intercepting network: {e}")
            return {}
    
    async def extract_via_api_probe(self) -> Dict:
        """Extract tokens by probing API endpoints"""
        try:
            logger.info("🔍 Extracting tokens via API probe...")
            
            session = tls_client.Session(client_identifier="chrome_120")
            
            tokens = {}
            
            # Try to get initial state from API
            endpoints = [
                f"{self.api_url}/api/v1/auth/state",
                f"{self.api_url}/api/auth/state",
                f"{self.base_url}/api/auth/state",
            ]
            
            for endpoint in endpoints:
                try:
                    logger.info(f"📡 Probing: {endpoint}")
                    
                    response = session.get(endpoint, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"✅ API response: {json.dumps(data, indent=2)[:200]}...")
                        
                        # Extract tokens from response
                        if 'csrf' in data:
                            tokens['csrf'] = data['csrf']
                        if 'token' in data:
                            tokens['token'] = data['token']
                        if 'accessToken' in data:
                            tokens['access_token'] = data['accessToken']
                        
                        # Extract cookies
                        if response.cookies:
                            tokens['cookies'] = dict(response.cookies)
                        
                        return tokens
                        
                except Exception as e:
                    logger.debug(f"❌ Endpoint failed: {e}")
                    continue
            
            return tokens
            
        except Exception as e:
            logger.error(f"❌ Error probing API: {e}")
            return {}
    
    async def extract_all(self) -> Dict:
        """Extract tokens using all available methods"""
        try:
            logger.info("=" * 60)
            logger.info("🔐 Starting comprehensive token extraction")
            logger.info("=" * 60)
            
            all_tokens = {}
            
            # Method 1: Playwright DOM extraction
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    await page.goto(f"{self.base_url}/en/authenticate/signup", wait_until="networkidle")
                    
                    playwright_tokens = await self.extract_via_playwright(page)
                    all_tokens.update(playwright_tokens)
                    
                    await browser.close()
            except Exception as e:
                logger.warning(f"⚠️  Playwright extraction failed: {e}")
            
            # Method 2: Network interception
            try:
                network_tokens = await self.extract_via_network_interception()
                all_tokens.update(network_tokens)
            except Exception as e:
                logger.warning(f"⚠️  Network interception failed: {e}")
            
            # Method 3: API probing
            try:
                api_tokens = await self.extract_via_api_probe()
                all_tokens.update(api_tokens)
            except Exception as e:
                logger.warning(f"⚠️  API probing failed: {e}")
            
            logger.info("=" * 60)
            logger.info(f"✅ Extraction complete. Found {len(all_tokens)} token types")
            logger.info("=" * 60)
            
            return all_tokens
            
        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}")
            return {}
    
    def build_headers_with_tokens(self, tokens: Dict) -> Dict:
        """Build request headers with extracted tokens"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
        }
        
        # Add CSRF token if available
        if 'csrf' in tokens:
            headers['X-CSRF-Token'] = tokens['csrf']
            headers['X-Requested-With'] = 'XMLHttpRequest'
        
        # Add auth token if available
        if 'auth_token' in tokens:
            headers['Authorization'] = f"Bearer {tokens['auth_token']}"
        elif 'token' in tokens:
            headers['Authorization'] = f"Bearer {tokens['token']}"
        elif 'access_token' in tokens:
            headers['Authorization'] = f"Bearer {tokens['access_token']}"
        
        return headers


class TokenCache:
    """Cache for tokens to avoid repeated extraction"""
    
    def __init__(self, cache_duration: int = 3600):
        self.cache = {}
        self.cache_duration = cache_duration
        self.cache_time = {}
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached tokens"""
        import time
        
        if key not in self.cache:
            return None
        
        if time.time() - self.cache_time[key] > self.cache_duration:
            del self.cache[key]
            del self.cache_time[key]
            return None
        
        logger.info(f"📦 Using cached tokens for {key}")
        return self.cache[key]
    
    def set(self, key: str, tokens: Dict):
        """Cache tokens"""
        import time
        self.cache[key] = tokens
        self.cache_time[key] = time.time()
        logger.info(f"💾 Cached tokens for {key}")
    
    def clear(self, key: Optional[str] = None):
        """Clear cache"""
        if key:
            if key in self.cache:
                del self.cache[key]
            if key in self.cache_time:
                del self.cache_time[key]
        else:
            self.cache.clear()
            self.cache_time.clear()


# Global token cache
_token_cache = TokenCache()


async def extract_wttj_tokens(use_cache: bool = True) -> Dict:
    """
    Extract WTTJ tokens
    
    Args:
        use_cache: Whether to use cached tokens if available
    
    Returns:
        Dict with extracted tokens
    """
    cache_key = "wttj_tokens"
    
    if use_cache:
        cached = _token_cache.get(cache_key)
        if cached:
            return cached
    
    extractor = CSRFExtractor()
    tokens = await extractor.extract_all()
    
    if tokens and use_cache:
        _token_cache.set(cache_key, tokens)
    
    return tokens


# Test function
if __name__ == "__main__":
    async def test_extraction():
        tokens = await extract_wttj_tokens(use_cache=False)
        
        print("\n" + "=" * 60)
        print("📋 Extracted Tokens:")
        print("=" * 60)
        
        for key, value in tokens.items():
            if isinstance(value, dict):
                print(f"\n{key}:")
                for k, v in value.items():
                    if isinstance(v, str) and len(v) > 50:
                        print(f"  {k}: {v[:50]}...")
                    else:
                        print(f"  {k}: {v}")
            else:
                if isinstance(value, str) and len(value) > 50:
                    print(f"{key}: {value[:50]}...")
                else:
                    print(f"{key}: {value}")
        
        # Test header building
        extractor = CSRFExtractor()
        headers = extractor.build_headers_with_tokens(tokens)
        
        print("\n" + "=" * 60)
        print("📝 Request Headers:")
        print("=" * 60)
        
        for key, value in headers.items():
            if len(value) > 50:
                print(f"{key}: {value[:50]}...")
            else:
                print(f"{key}: {value}")
    
    asyncio.run(test_extraction())
