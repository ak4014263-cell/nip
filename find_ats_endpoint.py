#!/usr/bin/env python3
"""
ATS Endpoint Finder for WTTJ Jobs
Analyzes WTTJ job pages to find the underlying ATS (Lever, Greenhouse, etc.)
Then you can apply directly to the ATS, bypassing WTTJ's anti-bot entirely!
"""
import asyncio
import sys
import os
import re
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'automation', 'app'))

from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class ATSFinder:
    """
    Finds the underlying Applicant Tracking System (ATS) for WTTJ jobs
    """
    
    ATS_PATTERNS = {
        'lever.co': {
            'name': 'Lever',
            'apply_pattern': r'https://jobs\.lever\.co/[^/]+/[^/]+/apply',
            'job_pattern': r'https://jobs\.lever\.co/[^/]+/[^/]+',
        },
        'greenhouse.io': {
            'name': 'Greenhouse',
            'apply_pattern': r'https://boards\.greenhouse\.io/[^/]+/jobs/\d+',
            'job_pattern': r'https://boards\.greenhouse\.io/[^/]+/jobs/\d+',
        },
        'workday.com': {
            'name': 'Workday',
            'apply_pattern': r'https://[^.]+\.myworkdayjobs\.com/',
            'job_pattern': r'https://[^.]+\.myworkdayjobs\.com/',
        },
        'smartrecruiters.com': {
            'name': 'SmartRecruiters',
            'apply_pattern': r'https://jobs\.smartrecruiters\.com/[^/]+/\d+',
            'job_pattern': r'https://jobs\.smartrecruiters\.com/[^/]+/\d+',
        },
        'jobvite.com': {
            'name': 'Jobvite',
            'apply_pattern': r'https://jobs\.jobvite\.com/[^/]+/job/[^/]+',
            'job_pattern': r'https://jobs\.jobvite\.com/[^/]+/job/[^/]+',
        },
        'breezy.hr': {
            'name': 'BreezyHR',
            'apply_pattern': r'https://[^.]+\.breezy\.hr/p/[^/]+',
            'job_pattern': r'https://[^.]+\.breezy\.hr/p/[^/]+',
        },
        'recruitee.com': {
            'name': 'Recruitee',
            'apply_pattern': r'https://[^.]+\.recruitee\.com/o/[^/]+/c/[^/]+',
            'job_pattern': r'https://[^.]+\.recruitee\.com/o/[^/]+/c/[^/]+',
        },
        'ashbyhq.com': {
            'name': 'Ashby',
            'apply_pattern': r'https://jobs\.ashbyhq\.com/[^/]+/[^/]+',
            'job_pattern': r'https://jobs\.ashbyhq\.com/[^/]+/[^/]+',
        },
    }
    
    async def analyze_job(self, job_url: str) -> dict:
        """
        Analyze a WTTJ job page to find the underlying ATS
        """
        print(f"\n🔍 Analyzing: {job_url}")
        print("="*80)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Track network requests
            ats_urls = []
            
            def handle_request(request):
                url = request.url
                # Check if request goes to an ATS
                for domain, ats_info in self.ATS_PATTERNS.items():
                    if domain in url:
                        ats_urls.append({
                            'ats': ats_info['name'],
                            'url': url,
                            'type': 'network_request'
                        })
            
            page.on('request', handle_request)
            
            try:
                # Load the job page
                await page.goto(job_url, wait_until='networkidle', timeout=30000)
                await asyncio.sleep(3)
                
                # Get page content
                content = await page.content()
                
                # Look for ATS URLs in HTML
                print("\n[1/4] Checking HTML content...")
                for domain, ats_info in self.ATS_PATTERNS.items():
                    if domain in content:
                        # Try to extract the full URL
                        pattern = ats_info['job_pattern']
                        matches = re.findall(pattern, content)
                        if matches:
                            for match in matches:
                                print(f"      ✓ Found {ats_info['name']}: {match}")
                                ats_urls.append({
                                    'ats': ats_info['name'],
                                    'url': match,
                                    'type': 'html_content'
                                })
                
                # Look for apply button that might redirect
                print("\n[2/4] Checking apply button...")
                apply_buttons = await page.locator('button:has-text("Apply"), a:has-text("Apply")').all()
                
                for btn in apply_buttons:
                    href = await btn.get_attribute('href')
                    onclick = await btn.get_attribute('onclick')
                    
                    if href:
                        print(f"      Apply button href: {href}")
                        for domain, ats_info in self.ATS_PATTERNS.items():
                            if domain in href:
                                print(f"      ✓ Found {ats_info['name']} in apply button")
                                ats_urls.append({
                                    'ats': ats_info['name'],
                                    'url': href,
                                    'type': 'apply_button'
                                })
                
                # Check for iframes (embedded ATS forms)
                print("\n[3/4] Checking for embedded iframes...")
                frames = page.frames
                for frame in frames:
                    frame_url = frame.url
                    if frame_url and frame_url != 'about:blank':
                        print(f"      Frame: {frame_url}")
                        for domain, ats_info in self.ATS_PATTERNS.items():
                            if domain in frame_url:
                                print(f"      ✓ Found {ats_info['name']} iframe")
                                ats_urls.append({
                                    'ats': ats_info['name'],
                                    'url': frame_url,
                                    'type': 'iframe'
                                })
                
                # Check JavaScript variables
                print("\n[4/4] Checking JavaScript data...")
                try:
                    # Look for common JS variables that might contain ATS URLs
                    js_data = await page.evaluate('''() => {
                        return {
                            location: window.location.href,
                            dataAttributes: Array.from(document.querySelectorAll('[data-url], [data-apply-url], [data-job-url]')).map(el => ({
                                tag: el.tagName,
                                dataUrl: el.getAttribute('data-url'),
                                dataApplyUrl: el.getAttribute('data-apply-url'),
                                dataJobUrl: el.getAttribute('data-job-url')
                            }))
                        }
                    }''')
                    
                    for item in js_data.get('dataAttributes', []):
                        for key, value in item.items():
                            if value and isinstance(value, str):
                                for domain, ats_info in self.ATS_PATTERNS.items():
                                    if domain in value:
                                        print(f"      ✓ Found {ats_info['name']} in JS data")
                                        ats_urls.append({
                                            'ats': ats_info['name'],
                                            'url': value,
                                            'type': 'javascript_data'
                                        })
                except Exception as e:
                    print(f"      Could not extract JS data: {e}")
                
            except Exception as e:
                print(f"\n❌ Error analyzing job: {e}")
                return {"success": False, "error": str(e)}
            
            finally:
                await browser.close()
            
            # Remove duplicates
            unique_ats = {}
            for item in ats_urls:
                key = f"{item['ats']}_{item['url']}"
                if key not in unique_ats:
                    unique_ats[key] = item
            
            result = {
                "success": True,
                "job_url": job_url,
                "ats_found": list(unique_ats.values()),
                "count": len(unique_ats)
            }
            
            print("\n" + "="*80)
            print("RESULTS")
            print("="*80)
            
            if result['count'] > 0:
                print(f"\n✅ Found {result['count']} ATS endpoint(s):\n")
                for i, ats in enumerate(result['ats_found'], 1):
                    print(f"{i}. {ats['ats']}")
                    print(f"   URL: {ats['url']}")
                    print(f"   Source: {ats['type']}\n")
                
                print("💡 TIP: You can now apply directly to the ATS URL above,")
                print("   completely bypassing WTTJ's anti-bot detection!\n")
            else:
                print("\n⚠️  No direct ATS endpoint found.")
                print("   The job might be hosted directly on WTTJ.\n")
            
            print("="*80)
            
            return result


async def main():
    """
    Test with a WTTJ job URL
    """
    print("\n" + "="*80)
    print("ATS ENDPOINT FINDER FOR WTTJ")
    print("="*80)
    print("\nThis tool finds the underlying ATS (Applicant Tracking System)")
    print("for WTTJ jobs, so you can apply directly and bypass anti-bot!")
    print("="*80)
    
    # Example job URL (replace with real one)
    job_url = input("\nEnter WTTJ job URL: ").strip()
    
    if not job_url:
        print("\nUsing example URL...")
        job_url = "https://www.welcometothejungle.com/en/companies/datadog/jobs/senior-software-engineer-cloud-security-management_paris"
    
    finder = ATSFinder()
    result = await finder.analyze_job(job_url)
    
    if result['success'] and result['count'] > 0:
        print("\n🎯 SUCCESS! You can now:")
        print("   1. Go directly to the ATS URL found above")
        print("   2. Fill the application form there")
        print("   3. Submit without any anti-bot detection!")
    else:
        print("\n💡 If no ATS found, use the semi-automated method:")
        print("   python semi_auto_wttj.py")


if __name__ == '__main__':
    asyncio.run(main())
