#!/usr/bin/env python3
"""
TLS Fingerprinting Bypass for WTTJ
Mimics Chrome's exact TLS handshake to bypass network-level detection
"""
import tls_client
import json
import time
import random
import string
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TLSBypassClient:
    """
    Uses tls-client to mimic Chrome's TLS fingerprint
    Bypasses network-level anti-bot detection
    """
    
    def __init__(self, browser_version: str = "chrome_120"):
        """
        Initialize TLS client with specific browser fingerprint
        
        Args:
            browser_version: Chrome version to mimic
                Options: chrome_103, chrome_104, chrome_105, chrome_106, 
                        chrome_107, chrome_108, chrome_109, chrome_110,
                        chrome_111, chrome_112, chrome_116_PSK,
                        chrome_117, chrome_120, safari_15_6_1,
                        safari_16_0, safari_ios_15_5, safari_ios_15_6,
                        safari_ios_16_0, firefox_102, firefox_104,
                        firefox_105, firefox_106, firefox_108, firefox_110,
                        firefox_117, okhttp4_android_7, okhttp4_android_8,
                        okhttp4_android_9, okhttp4_android_10,
                        okhttp4_android_11, okhttp4_android_12,
                        okhttp4_android_13
        """
        self.session = tls_client.Session(
            client_identifier=browser_version,
            random_tls_extension_order=True
        )
        
        # Set realistic headers that match Chrome
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
        })
        
        logger.info(f"✅ TLS client initialized with {browser_version} fingerprint")
    
    def create_account(self, email: str, password: str, first_name: str, last_name: str = "") -> Dict:
        """
        Create WTTJ account using TLS bypass
        
        This sends the signup request directly to WTTJ's API endpoint,
        bypassing the browser automation entirely.
        """
        try:
            logger.info(f"🔐 Creating account with TLS bypass: {email}")
            
            # Step 1: Get CSRF token from signup page
            logger.info("  [1/3] Getting CSRF token...")
            signup_page = self.session.get(
                'https://www.welcometothejungle.com/en/authenticate/signup'
            )
            
            if signup_page.status_code != 200:
                logger.error(f"  ✗ Failed to load signup page: {signup_page.status_code}")
                return {"success": False, "error": f"HTTP {signup_page.status_code}"}
            
            # Extract CSRF token from page (would need to parse HTML)
            # For now, let's try without it or find the API endpoint
            logger.info("  ✓ Page loaded")
            
            # Step 2: Find the actual signup API endpoint
            # WTTJ likely uses a GraphQL or REST endpoint for signup
            logger.info("  [2/3] Looking for signup API endpoint...")
            
            # Common patterns for WTTJ API
            api_endpoints = [
                'https://www.welcometothejungle.com/api/v1/users',
                'https://api.welcometothejungle.com/v1/users',
                'https://www.welcometothejungle.com/graphql',
                'https://api.welcometothejungle.com/graphql',
            ]
            
            # Try to find the signup endpoint by analyzing the page
            # This would require parsing the JavaScript bundles
            logger.info("  ⚠️  API endpoint detection not implemented yet")
            
            # Step 3: Send signup request
            logger.info("  [3/3] Would send signup request here...")
            
            return {
                "success": False,
                "error": "API endpoint discovery needed",
                "note": "TLS bypass is working, but need to find the signup API endpoint"
            }
            
        except Exception as e:
            logger.error(f"TLS bypass error: {e}")
            return {"success": False, "error": str(e)}
    
    def find_ats_url(self, job_url: str) -> Optional[str]:
        """
        Find the underlying ATS (Applicant Tracking System) URL
        
        WTTJ jobs often redirect to:
        - Lever (lever.co)
        - Greenhouse (greenhouse.io)
        - Workday (workday.com)
        - SmartRecruiters (smartrecruiters.com)
        
        If we find the ATS URL, we can submit directly and bypass WTTJ entirely!
        """
        try:
            logger.info(f"🔍 Finding ATS URL for: {job_url}")
            
            response = self.session.get(job_url, allow_redirects=False)
            
            # Check for redirects
            if response.status_code in [301, 302, 303, 307, 308]:
                redirect_url = response.headers.get('Location')
                logger.info(f"  ✓ Found redirect: {redirect_url}")
                
                # Check if it's a known ATS
                ats_patterns = {
                    'lever.co': 'Lever',
                    'greenhouse.io': 'Greenhouse',
                    'workday.com': 'Workday',
                    'smartrecruiters.com': 'SmartRecruiters',
                    'jobvite.com': 'Jobvite',
                    'breezy.hr': 'BreezyHR',
                    'recruitee.com': 'Recruitee',
                }
                
                for pattern, ats_name in ats_patterns.items():
                    if pattern in redirect_url:
                        logger.info(f"  ✓ Detected ATS: {ats_name}")
                        return redirect_url
            
            # If no redirect, check the page content for ATS iframes or forms
            if response.status_code == 200:
                content = response.text
                
                # Look for embedded ATS forms
                for pattern, ats_name in [
                    ('lever.co', 'Lever'),
                    ('greenhouse.io', 'Greenhouse'),
                    ('workday.com', 'Workday'),
                ]:
                    if pattern in content:
                        logger.info(f"  ✓ Found embedded {ats_name} in page")
                        # Would need to extract the actual form URL
                        return f"Found {ats_name} - need to extract URL"
            
            logger.info("  ✗ No direct ATS URL found")
            return None
            
        except Exception as e:
            logger.error(f"Error finding ATS URL: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test if TLS bypass is working"""
        try:
            response = self.session.get('https://www.welcometothejungle.com')
            
            if response.status_code in [200, 202]:  # 202 = Accepted (also success)
                logger.info("✅ TLS bypass working - successfully connected to WTTJ")
                logger.info(f"   Response code: {response.status_code}")
                return True
            else:
                logger.warning(f"⚠️  Unexpected status code: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ TLS bypass test failed: {e}")
            return False


def test_tls_bypass():
    """Test the TLS bypass"""
    print("\n" + "="*80)
    print("TLS FINGERPRINTING BYPASS TEST")
    print("="*80)
    print("\nThis mimics Chrome's exact TLS handshake to bypass anti-bot detection")
    print("="*80)
    
    client = TLSBypassClient(browser_version="chrome_120")
    
    print("\n[1/3] Testing connection...")
    if client.test_connection():
        print("      ✓ TLS bypass is working!")
    else:
        print("      ✗ TLS bypass failed")
        return
    
    print("\n[2/3] Testing job URL analysis...")
    test_job = "https://www.welcometothejungle.com/en/companies/some-company/jobs/some-job"
    ats_url = client.find_ats_url(test_job)
    if ats_url:
        print(f"      ✓ Found: {ats_url}")
    else:
        print("      ✗ No ATS URL found (expected for test URL)")
    
    print("\n[3/3] Testing account creation endpoint...")
    result = client.create_account(
        email="test@example.com",
        password="TestPass123!",
        first_name="Test"
    )
    print(f"      Result: {result}")
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("1. Need to find WTTJ's actual signup API endpoint")
    print("2. Extract CSRF token from signup page")
    print("3. Send POST request with TLS bypass")
    print("\nFor now, use semi-automated method (semi_auto_wttj.py)")
    print("="*80)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    test_tls_bypass()
