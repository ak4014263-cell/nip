"""
Test Script for WTTJ Ollama Automation
Tests account creation, profile setup, and job applications on Welcome to the Jungle
"""

import asyncio
import logging
import json
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from ollama_automation import (
    OllamaProfileEnhancer,
    WTTJAutomation,
    UserProfile,
    UserCredentials
)

from playwright.async_api import async_playwright

# Test configuration
TEST_CONFIG = {
    "user": {
        "email": "test.wttj.automation@example.com",
        "password": "TestWTTJ123!@#",
        "first_name": "Test",
        "last_name": "Automation",
        "phone": "+33 6 12 34 56 78",
        "location": "Paris, France"
    },
    "profile": {
        "headline": "Full Stack Developer",
        "bio": "Experienced developer with expertise in web technologies",
        "skills": ["Python", "React", "Node.js", "AWS", "Docker"],
        "experience_years": 5,
        "education": "Bachelor's in Computer Science",
        "linkedin_url": "https://linkedin.com/in/testuser"
    },
    "test_jobs": [
        "https://www.welcometothejungle.com/en/jobs",  # Job listings page
    ]
}


class WTTJTestSuite:
    """Complete test suite for WTTJ automation"""
    
    def __init__(self):
        self.enhancer = OllamaProfileEnhancer()
        self.wttj = WTTJAutomation(self.enhancer)
        self.test_results = {
            "start_time": datetime.now().isoformat(),
            "tests": {},
            "summary": {}
        }
    
    async def test_ollama_availability(self) -> bool:
        """Test if Ollama is available and working"""
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Ollama Availability")
        logger.info("="*60)
        
        try:
            import ollama
            models_response = ollama.list()
            
            # Extract model names from the response
            model_names = []
            if hasattr(models_response, 'models'):
                # If it's a Model object with .models attribute
                model_names = [m.model for m in models_response.models]
            elif isinstance(models_response, dict) and "models" in models_response:
                # If it's a dict with "models" key
                model_names = [m.get("model") if isinstance(m, dict) else m.model for m in models_response["models"]]
            
            logger.info(f"   Found {len(model_names)} models: {model_names}")
            
            if any("mistral" in m.lower() for m in model_names):
                logger.info("✅ Ollama available with Mistral model")
                logger.info(f"   Models: {model_names}")
                self.test_results["tests"]["ollama"] = {"status": "pass", "models": model_names}
                return True
            else:
                logger.warning("⚠️  Mistral model not found")
                logger.info("   Run: ollama pull mistral")
                self.test_results["tests"]["ollama"] = {"status": "fail", "reason": "mistral not found", "available_models": model_names}
                return False
        except Exception as e:
            logger.error(f"❌ Ollama not available: {e}")
            logger.info("   Make sure Ollama is running: ollama serve")
            self.test_results["tests"]["ollama"] = {"status": "fail", "error": str(e)}
            return False
    
    async def test_ai_content_generation(self) -> bool:
        """Test AI-powered content generation"""
        logger.info("\n" + "="*60)
        logger.info("TEST 2: AI Content Generation")
        logger.info("="*60)
        
        try:
            # Create test profile
            user = UserProfile(
                credentials=UserCredentials(**TEST_CONFIG["user"]),
                **TEST_CONFIG["profile"]
            )
            
            # Test bio generation
            logger.info("Testing bio generation...")
            bio = await self.enhancer.generate_profile_bio(user)
            logger.info(f"✅ Generated bio ({len(bio)} chars):")
            logger.info(f"   {bio[:100]}...")
            
            # Test application answers generation
            logger.info("\nTesting application answers generation...")
            answers = await self.enhancer.generate_application_answers(
                "Senior Developer",
                "TechCorp",
                "We are looking for a senior developer...",
                user
            )
            logger.info(f"✅ Generated answers ({len(answers)} fields):")
            for key, value in answers.items():
                logger.info(f"   {key}: {value[:80]}...")
            
            # Test ATS optimization
            logger.info("\nTesting ATS optimization...")
            ats_result = await self.enhancer.optimize_for_ats(
                "Senior Developer with 5 years of Python",
                "Must know Python, React, and AWS"
            )
            logger.info(f"✅ ATS Score: {ats_result.get('ats_score', 0)}/100")
            
            self.test_results["tests"]["ai_content"] = {
                "status": "pass",
                "bio_length": len(bio),
                "answers_generated": len(answers),
                "ats_score": ats_result.get('ats_score', 0)
            }
            return True
            
        except Exception as e:
            logger.error(f"❌ Content generation failed: {e}")
            self.test_results["tests"]["ai_content"] = {"status": "fail", "error": str(e)}
            return False
    
    async def test_wttj_account_creation(self) -> bool:
        """Test WTTJ account creation"""
        logger.info("\n" + "="*60)
        logger.info("TEST 3: WTTJ Account Creation")
        logger.info("="*60)
        
        browser = None
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context()
                page = await context.new_page()
                
                # Create test profile
                user = UserProfile(
                    credentials=UserCredentials(**TEST_CONFIG["user"]),
                    **TEST_CONFIG["profile"]
                )
                
                logger.info(f"Creating account for: {user.credentials.email}")
                result = await self.wttj.create_account(page, user)
                
                if result.get("success"):
                    logger.info("✅ Account creation initiated")
                    logger.info("   Note: May require email verification")
                    self.test_results["tests"]["wttj_account"] = {
                        "status": "pass",
                        "email": user.credentials.email,
                        "message": "Account creation successful"
                    }
                    await asyncio.sleep(5)  # Wait for page to load
                    success = True
                else:
                    logger.warning(f"⚠️  Account creation: {result.get('error')}")
                    self.test_results["tests"]["wttj_account"] = {
                        "status": "fail",
                        "error": result.get("error")
                    }
                    success = False
                
                await context.close()
                return success
            
        except Exception as e:
            logger.error(f"❌ Account creation failed: {e}")
            self.test_results["tests"]["wttj_account"] = {"status": "fail", "error": str(e)}
            return False
        finally:
            if browser:
                await browser.close()
    
    async def test_wttj_profile_setup(self) -> bool:
        """Test WTTJ profile setup"""
        logger.info("\n" + "="*60)
        logger.info("TEST 4: WTTJ Profile Setup")
        logger.info("="*60)
        
        browser = None
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context()
                page = await context.new_page()
                
                # Create test profile
                user = UserProfile(
                    credentials=UserCredentials(**TEST_CONFIG["user"]),
                    **TEST_CONFIG["profile"]
                )
                
                logger.info("Setting up WTTJ profile...")
                result = await self.wttj.setup_profile(page, user)
                
                if result.get("success"):
                    logger.info("✅ Profile setup completed")
                    logger.info(f"   Bio: {result.get('profile', {}).get('bio', 'N/A')[:50]}...")
                    logger.info(f"   Skills: {result.get('profile', {}).get('skills_count', 0)}")
                    self.test_results["tests"]["wttj_profile"] = {
                        "status": "pass",
                        "profile_data": result.get("profile")
                    }
                    success = True
                else:
                    logger.warning(f"⚠️  Profile setup: {result.get('error')}")
                    self.test_results["tests"]["wttj_profile"] = {
                        "status": "fail",
                        "error": result.get("error")
                    }
                    success = False
                
                await context.close()
                return success
            
        except Exception as e:
            logger.error(f"❌ Profile setup failed: {e}")
            self.test_results["tests"]["wttj_profile"] = {"status": "fail", "error": str(e)}
            return False
        finally:
            if browser:
                await browser.close()
    
    async def test_wttj_job_browsing(self) -> bool:
        """Test WTTJ job browsing and page navigation"""
        logger.info("\n" + "="*60)
        logger.info("TEST 5: WTTJ Job Browsing")
        logger.info("="*60)
        
        browser = None
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                
                logger.info("Navigating to WTTJ job listings...")
                await page.goto("https://www.welcometothejungle.com/en/jobs", wait_until="networkidle", timeout=30000)
                
                logger.info("✅ Navigated to job listings page")
                
                # Try to find job cards
                try:
                    job_cards = await page.query_selector_all('[data-testid*="job"]')
                    logger.info(f"   Found {len(job_cards)} job cards")
                except:
                    logger.info("   Could not count job cards (page structure may vary)")
                
                # Take screenshot
                await page.screenshot(path="wttj_jobs_page.png")
                logger.info("   Screenshot saved: wttj_jobs_page.png")
                
                self.test_results["tests"]["wttj_browsing"] = {
                    "status": "pass",
                    "url": "https://www.welcometothejungle.com/en/jobs",
                    "screenshot": "wttj_jobs_page.png"
                }
                
                return True
            
        except Exception as e:
            logger.error(f"❌ Job browsing failed: {e}")
            self.test_results["tests"]["wttj_browsing"] = {"status": "fail", "error": str(e)}
            return False
        finally:
            if browser:
                await browser.close()
    
    async def test_integration_with_backend(self) -> bool:
        """Test integration with automation service"""
        logger.info("\n" + "="*60)
        logger.info("TEST 6: Backend Integration")
        logger.info("="*60)
        
        try:
            import httpx
            
            # Check if automation service is running
            logger.info("Checking automation service...")
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get("http://localhost:8006/health")
                    logger.info("✅ Automation service is running")
                    self.test_results["tests"]["integration"] = {
                        "status": "pass",
                        "service_url": "http://localhost:8006",
                        "health": response.status_code == 200
                    }
                    return True
            except Exception as e:
                logger.warning(f"⚠️  Automation service not running: {e}")
                logger.info("   Start with: python -m uvicorn app.main:app --port 8006")
                self.test_results["tests"]["integration"] = {
                    "status": "fail",
                    "reason": "Service not running"
                }
                return False
            
        except Exception as e:
            logger.error(f"❌ Integration test failed: {e}")
            self.test_results["tests"]["integration"] = {"status": "fail", "error": str(e)}
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("\n" + "="*80)
        logger.info("🧪 WTTJ OLLAMA AUTOMATION TEST SUITE")
        logger.info("="*80)
        
        results = []
        
        # Test 1: Ollama availability
        results.append(await self.test_ollama_availability())
        if not results[-1]:
            logger.error("\n❌ Ollama not available. Cannot proceed with tests.")
            self.generate_report()
            return
        
        # Test 2: AI content generation
        results.append(await self.test_ai_content_generation())
        
        # Test 3: WTTJ account creation
        results.append(await self.test_wttj_account_creation())
        
        # Test 4: WTTJ profile setup
        results.append(await self.test_wttj_profile_setup())
        
        # Test 5: WTTJ job browsing
        results.append(await self.test_wttj_job_browsing())
        
        # Test 6: Backend integration
        results.append(await self.test_integration_with_backend())
        
        # Summary
        passed = sum(results)
        total = len(results)
        
        self.test_results["summary"] = {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": f"{(passed/total*100):.1f}%",
            "end_time": datetime.now().isoformat()
        }
        
        self.generate_report()
    
    def generate_report(self):
        """Generate test report"""
        logger.info("\n" + "="*80)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("="*80)
        
        summary = self.test_results["summary"]
        logger.info(f"\nTotal Tests: {summary.get('total_tests', 0)}")
        logger.info(f"Passed: {summary.get('passed', 0)} ✅")
        logger.info(f"Failed: {summary.get('failed', 0)} ❌")
        logger.info(f"Success Rate: {summary.get('success_rate', 'N/A')}")
        
        logger.info("\n" + "-"*80)
        logger.info("Detailed Results:")
        logger.info("-"*80)
        
        for test_name, test_result in self.test_results["tests"].items():
            status = "✅ PASS" if test_result.get("status") == "pass" else "❌ FAIL"
            logger.info(f"\n{status}: {test_name}")
            
            for key, value in test_result.items():
                if key != "status":
                    if isinstance(value, dict):
                        logger.info(f"   {key}: {json.dumps(value, indent=6)}")
                    else:
                        logger.info(f"   {key}: {value}")
        
        # Save report to file
        report_file = "wttj_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        logger.info(f"\n📄 Full report saved to: {report_file}")
        
        logger.info("\n" + "="*80)
        logger.info("🏁 TEST SUITE COMPLETE")
        logger.info("="*80)


async def main():
    """Run test suite"""
    suite = WTTJTestSuite()
    await suite.run_all_tests()


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  WTTJ OLLAMA AUTOMATION TEST SUITE                         ║
║                                                                            ║
║  This script tests the complete Ollama automation system for WTTJ         ║
║                                                                            ║
║  Prerequisites:                                                            ║
║  1. Ollama running: ollama serve                                          ║
║  2. Mistral model: ollama pull mistral                                    ║
║  3. Python packages: pip install playwright ollama                        ║
║                                                                            ║
║  What gets tested:                                                         ║
║  ✓ Ollama availability and model loading                                  ║
║  ✓ AI content generation (bios, answers, ATS optimization)               ║
║  ✓ WTTJ account creation automation                                       ║
║  ✓ WTTJ profile setup automation                                          ║
║  ✓ WTTJ job browsing and page navigation                                  ║
║  ✓ Backend integration                                                     ║
║                                                                            ║
║  Starting tests...                                                         ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())
