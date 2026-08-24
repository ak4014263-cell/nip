#!/usr/bin/env python3
"""
WTTJ Account Creator using TLS Client
Bypasses anti-bot detection by mimicking Chrome's exact TLS handshake
"""
import asyncio
import json
import re
import logging
from typing import Dict, Optional, Tuple
import tls_client
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WTTJTLSCreator:
    """Creates WTTJ accounts using TLS client to bypass anti-bot detection"""
    
    def __init__(self, proxy: Optional[str] = None):
        """
        Initialize TLS creator
        
        Args:
            proxy: Optional proxy URL (format: http://ip:port or http://user:pass@ip:port)
        """
        self.proxy = proxy
        self.tls_session = None
        self.base_url = "https://www.welcometothejungle.com"
        self.api_url = "https://api.welcometothejungle.com"
        self.csrf_token = None
        self.cookies = {}
        
    def _create_tls_session(self) -> tls_client.Session:
        """Create TLS client session with Chrome 120 fingerprint"""
        try:
            session = tls_client.Session(
                client_identifier="chrome_120",
                random_tls_extension_order=True
            )
            
            # Set realistic headers
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0",
            })
            
            if self.proxy:
                session.proxy = self.proxy
                logger.info(f"🔗 Using proxy: {self.proxy}")
            
            logger.info("✅ TLS session created with Chrome 120 fingerprint")
            return session
        except Exception as e:
            logger.error(f"❌ Failed to create TLS session: {e}")
            raise
    
    async def extract_csrf_token(self) -> str:
        """Extract CSRF token from signup page using Playwright"""
        try:
            logger.info("🔍 Extracting CSRF token from signup page...")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Navigate to signup
                await page.goto(f"{self.base_url}/en/authenticate/signup", wait_until="networkidle")
                
                # Extract CSRF token from page
                csrf_patterns = [
                    # Look in script tags
                    'window.__INITIAL_STATE__.*?"csrf":"([^"]+)"',
                    # Look in meta tags
                    '<meta name="csrf" content="([^"]+)"',
                    # Look in window object
                    'window.csrfToken\s*=\s*["\']([^"\']+)["\']',
                    # Look in form hidden input
                    '<input[^>]*name="csrf"[^>]*value="([^"]+)"',
                    # Look in cookie
                    'csrf=([^;]+)',
                ]
                
                page_content = await page.content()
                
                for pattern in csrf_patterns:
                    match = re.search(pattern, page_content)
                    if match:
                        token = match.group(1)
                        logger.info(f"✅ CSRF token found: {token[:20]}...")
                        await browser.close()
                        return token
                
                # Try to get from cookies
                cookies = await page.context.cookies()
                for cookie in cookies:
                    if cookie['name'] == 'csrf':
                        logger.info(f"✅ CSRF token from cookie: {cookie['value'][:20]}...")
                        await browser.close()
                        return cookie['value']
                
                logger.warning("⚠️ CSRF token not found, proceeding without it")
                await browser.close()
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to extract CSRF token: {e}")
            return None
    
    async def get_signup_page_state(self) -> Dict:
        """Get initial page state including any required tokens"""
        try:
            logger.info("📄 Fetching signup page state...")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(f"{self.base_url}/en/authenticate/signup", wait_until="networkidle")
                
                # Extract initial state
                page_content = await page.content()
                
                # Get cookies
                cookies = await page.context.cookies()
                for cookie in cookies:
                    self.cookies[cookie['name']] = cookie['value']
                
                logger.info(f"✅ Got {len(cookies)} cookies")
                
                await browser.close()
                return {"cookies": self.cookies}
                
        except Exception as e:
            logger.error(f"❌ Failed to get page state: {e}")
            return {}
    
    def _build_signup_request(self, email: str, password: str, first_name: str, last_name: str) -> Dict:
        """Build signup request payload"""
        return {
            "email": email,
            "password": password,
            "firstName": first_name,
            "lastName": last_name,
            "acceptTerms": True,
            "acceptMarketing": False,
        }
    
    async def create_account_tls(self, email: str, password: str, first_name: str, last_name: str) -> Dict:
        """
        Create WTTJ account using TLS client
        
        Args:
            email: Account email
            password: Account password (must be strong: 12+ chars, upper, lower, number, special)
            first_name: User's first name
            last_name: User's last name
        
        Returns:
            Dict with success status and details
        """
        try:
            logger.info(f"\n🚀 Creating WTTJ account for {email}")
            logger.info("=" * 60)
            
            # Step 1: Get initial page state and cookies
            logger.info("📍 Step 1: Getting page state...")
            state = await self.get_signup_page_state()
            
            # Step 2: Extract CSRF token
            logger.info("📍 Step 2: Extracting CSRF token...")
            self.csrf_token = await self.extract_csrf_token()
            
            # Step 3: Create TLS session
            logger.info("📍 Step 3: Creating TLS session...")
            self.tls_session = self._create_tls_session()
            
            # Set cookies in TLS session
            if self.cookies:
                cookie_str = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
                self.tls_session.headers["Cookie"] = cookie_str
                logger.info(f"🍪 Set {len(self.cookies)} cookies")
            
            # Step 4: Send signup request via TLS
            logger.info("📍 Step 4: Sending signup request via TLS...")
            
            payload = self._build_signup_request(email, password, first_name, last_name)
            
            headers = {
                "Content-Type": "application/json",
                "Referer": f"{self.base_url}/en/authenticate/signup",
                "Origin": self.base_url,
            }
            
            if self.csrf_token:
                headers["X-CSRF-Token"] = self.csrf_token
            
            # Try multiple API endpoints
            endpoints = [
                f"{self.api_url}/api/v1/auth/signup",
                f"{self.api_url}/auth/signup",
                f"{self.base_url}/api/auth/signup",
            ]
            
            for endpoint in endpoints:
                try:
                    logger.info(f"🌐 Trying endpoint: {endpoint}")
                    
                    response = self.tls_session.post(
                        endpoint,
                        json=payload,
                        headers=headers,
                        timeout=30
                    )
                    
                    logger.info(f"📊 Response status: {response.status_code}")
                    logger.info(f"📝 Response headers: {dict(response.headers)}")
                    
                    if response.status_code == 200 or response.status_code == 201:
                        result = response.json()
                        logger.info(f"✅ Account created successfully!")
                        logger.info(f"📋 Response: {result}")
                        return {
                            "success": True,
                            "email": email,
                            "message": "Account created successfully via TLS",
                            "response": result
                        }
                    
                    elif response.status_code == 400:
                        error_data = response.json()
                        logger.warning(f"⚠️  Validation error: {error_data}")
                        continue
                    
                    elif response.status_code == 429:
                        logger.warning(f"⏱️  Rate limited. Waiting...")
                        await asyncio.sleep(5)
                        continue
                    
                    else:
                        logger.warning(f"⚠️  Unexpected status {response.status_code}: {response.text[:200]}")
                        
                except Exception as e:
                    logger.warning(f"❌ Endpoint failed: {e}")
                    continue
            
            return {
                "success": False,
                "email": email,
                "error": "All signup endpoints failed",
                "message": "Could not create account via TLS - trying fallback methods"
            }
            
        except Exception as e:
            logger.error(f"❌ Account creation failed: {e}")
            return {
                "success": False,
                "email": email,
                "error": str(e),
                "message": "TLS-based signup failed"
            }
    
    async def create_account_hybrid(self, email: str, password: str, first_name: str, last_name: str) -> Dict:
        """
        Hybrid approach: Use browser to fill form, TLS to submit
        This combines browser automation with TLS to bypass detection
        """
        try:
            logger.info(f"\n🔄 Hybrid account creation for {email}")
            logger.info("=" * 60)
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                
                # Step 1: Navigate to signup
                logger.info("📍 Step 1: Navigating to signup page...")
                await page.goto(f"{self.base_url}/en/authenticate/signup", wait_until="networkidle")
                await asyncio.sleep(2)
                
                # Step 2: Fill form fields
                logger.info("📍 Step 2: Filling form fields...")
                
                # Fill first name
                first_name_input = await page.query_selector('input[placeholder*="Anita"], input[name*="firstName"], input[name*="first_name"]')
                if first_name_input:
                    await first_name_input.fill(first_name)
                    logger.info(f"✓ First name: {first_name}")
                
                # Fill last name
                last_name_input = await page.query_selector('input[placeholder*="Doe"], input[name*="lastName"], input[name*="last_name"]')
                if last_name_input:
                    await last_name_input.fill(last_name)
                    logger.info(f"✓ Last name: {last_name}")
                
                # Fill email
                email_input = await page.query_selector('input[type="email"]')
                if email_input:
                    await email_input.fill(email)
                    logger.info(f"✓ Email: {email}")
                
                # Fill password
                password_input = await page.query_selector('input[type="password"]')
                if password_input:
                    await password_input.fill(password)
                    logger.info(f"✓ Password: ****")
                
                # Step 3: Extract CSRF token from page
                logger.info("📍 Step 3: Extracting CSRF token...")
                csrf_token = await self.extract_csrf_token()
                
                # Step 4: Get cookies
                cookies = await page.context.cookies()
                for cookie in cookies:
                    self.cookies[cookie['name']] = cookie['value']
                
                await browser.close()
                
                # Step 5: Submit via TLS
                logger.info("📍 Step 4: Submitting via TLS...")
                self.tls_session = self._create_tls_session()
                
                payload = self._build_signup_request(email, password, first_name, last_name)
                
                headers = {
                    "Content-Type": "application/json",
                    "Referer": f"{self.base_url}/en/authenticate/signup",
                    "Origin": self.base_url,
                }
                
                if csrf_token:
                    headers["X-CSRF-Token"] = csrf_token
                
                response = self.tls_session.post(
                    f"{self.api_url}/api/v1/auth/signup",
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"✅ Hybrid account creation successful!")
                    return {
                        "success": True,
                        "email": email,
                        "message": "Account created via hybrid method",
                        "method": "browser_fill + tls_submit"
                    }
                else:
                    logger.warning(f"⚠️  Submission failed: {response.status_code}")
                    return {
                        "success": False,
                        "email": email,
                        "error": f"HTTP {response.status_code}",
                        "method": "hybrid"
                    }
                
        except Exception as e:
            logger.error(f"❌ Hybrid account creation failed: {e}")
            return {
                "success": False,
                "email": email,
                "error": str(e),
                "method": "hybrid"
            }


# Async wrapper for standalone use
async def create_wttj_account_tls(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    proxy: Optional[str] = None,
    use_hybrid: bool = True
) -> Dict:
    """
    Create WTTJ account using TLS client
    
    Args:
        email: Account email
        password: Account password
        first_name: User's first name
        last_name: User's last name
        proxy: Optional proxy URL
        use_hybrid: Whether to use hybrid method (browser fill + TLS submit)
    
    Returns:
        Dict with success status and details
    """
    creator = WTTJTLSCreator(proxy=proxy)
    
    if use_hybrid:
        return await creator.create_account_hybrid(email, password, first_name, last_name)
    else:
        return await creator.create_account_tls(email, password, first_name, last_name)


if __name__ == "__main__":
    # Test the TLS creator
    async def test():
        result = await create_wttj_account_tls(
            email="test@example.com",
            password="TestPass123!@",
            first_name="Test",
            last_name="User",
            use_hybrid=True
        )
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())
