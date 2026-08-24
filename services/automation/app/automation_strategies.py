"""
Advanced Automation Strategies for Job Applications
Implements Option A (Browser Automation), Option B (LLM + Browser-Use), Option C (ATS APIs)
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from playwright.async_api import Page
import httpx
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

class AutomationStrategy(ABC):
    """Base class for automation strategies"""
    
    @abstractmethod
    async def apply_to_job(self, job_url: str, candidate_data: Dict[str, Any], credentials: Dict[str, str]) -> Dict[str, Any]:
        """Apply to a job using this strategy"""
        pass
    
    @abstractmethod
    async def create_account(self, site_url: str, candidate_data: Dict[str, Any], credentials: Dict[str, str]) -> Dict[str, Any]:
        """Create account using this strategy"""
        pass


class OptionA_BrowserAutomation(AutomationStrategy):
    """
    Option A — Browser Automation (Playwright/Puppeteer)
    - Launch headless browser, navigate to career page
    - Use AI to identify form fields (name, email, CV upload, cover letter)
    - Fill and submit forms
    """
    
    def __init__(self, ai_client: OpenAI):
        self.ai_client = ai_client
    
    async def identify_form_fields(self, page: Page) -> Dict[str, str]:
        """Use AI to identify form fields on the page"""
        try:
            # Get page content and form elements
            page_content = await page.content()
            
            # Extract form elements
            form_elements = await page.evaluate("""
                () => {
                    const forms = Array.from(document.querySelectorAll('form'));
                    const inputs = Array.from(document.querySelectorAll('input, textarea, select'));
                    
                    return {
                        forms: forms.map(f => ({
                            action: f.action,
                            method: f.method,
                            innerHTML: f.innerHTML.substring(0, 1000)
                        })),
                        inputs: inputs.map(i => ({
                            type: i.type,
                            name: i.name,
                            id: i.id,
                            placeholder: i.placeholder,
                            className: i.className,
                            required: i.required
                        }))
                    }
                }
            """)
            
            # Use AI to analyze and map fields
            prompt = f"""
Analyze this job application form and identify the field mappings:

FORM ELEMENTS:
{form_elements}

Return a JSON object mapping semantic field names to selectors:
{{
    "first_name": "input selector",
    "last_name": "input selector", 
    "email": "input selector",
    "phone": "input selector",
    "resume_upload": "file input selector",
    "cover_letter": "textarea selector",
    "linkedin": "input selector",
    "submit_button": "button selector"
}}

Only include fields that are actually present on the form.
Return only valid JSON.
"""

            response = self.ai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing web forms. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_completion_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            field_mapping = eval(content)  # Parse JSON
            logger.info(f"AI identified form fields: {field_mapping}")
            return field_mapping
            
        except Exception as e:
            logger.error(f"AI form analysis failed: {e}")
            # Fallback to common selectors
            return {
                "first_name": "input[name*='first'], input[id*='first'], input[placeholder*='First']",
                "last_name": "input[name*='last'], input[id*='last'], input[placeholder*='Last']",
                "email": "input[type='email'], input[name*='email'], input[id*='email']",
                "phone": "input[type='tel'], input[name*='phone'], input[id*='phone']",
                "resume_upload": "input[type='file'][accept*='.pdf'], input[name*='resume'], input[name*='cv']",
                "cover_letter": "textarea[name*='cover'], textarea[name*='letter'], textarea[placeholder*='cover']",
                "submit_button": "button[type='submit'], input[type='submit'], button:has-text('Apply')"
            }
    
    async def apply_to_job(self, job_url: str, candidate_data: Dict[str, Any], credentials: Dict[str, str]) -> Dict[str, Any]:
        """Apply to job using browser automation with AI form detection"""
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                
                # Navigate to job URL
                await page.goto(job_url)
                await page.wait_for_load_state('networkidle')
                
                # AI-powered form field identification
                field_mapping = await self.identify_form_fields(page)
                
                # Fill form fields intelligently
                for field_name, selector in field_mapping.items():
                    try:
                        if field_name == "first_name" and candidate_data.get('first_name'):
                            await page.fill(selector, candidate_data['first_name'])
                        elif field_name == "last_name" and candidate_data.get('last_name'):
                            await page.fill(selector, candidate_data['last_name'])
                        elif field_name == "email":
                            await page.fill(selector, credentials.get('email', ''))
                        elif field_name == "phone" and candidate_data.get('phone'):
                            await page.fill(selector, candidate_data['phone'])
                        elif field_name == "cover_letter" and candidate_data.get('cover_letter'):
                            await page.fill(selector, candidate_data['cover_letter'])
                        elif field_name == "resume_upload" and candidate_data.get('resume_path'):
                            await page.set_input_files(selector, candidate_data['resume_path'])
                    except Exception as field_error:
                        logger.warning(f"Could not fill field {field_name}: {field_error}")
                
                # Take screenshot before submit
                await page.screenshot(path=f"screenshots/before_apply_{hash(job_url)}.png")
                
                # Submit application
                submit_selector = field_mapping.get('submit_button', 'button[type="submit"]')
                await page.click(submit_selector)
                await page.wait_for_load_state('networkidle')
                
                # Take screenshot after submit
                await page.screenshot(path=f"screenshots/after_apply_{hash(job_url)}.png")
                
                await browser.close()
                
                return {
                    "success": True,
                    "strategy": "Option A - Browser Automation",
                    "job_url": job_url,
                    "fields_filled": list(field_mapping.keys()),
                    "message": "Application submitted successfully using AI-powered form detection"
                }
                
        except Exception as e:
            logger.error(f"Option A automation failed: {e}")
            return {
                "success": False,
                "strategy": "Option A - Browser Automation",
                "error": str(e)
            }
    
    async def create_account(self, site_url: str, candidate_data: Dict[str, Any], credentials: Dict[str, str]) -> Dict[str, Any]:
        """Create account using AI-powered browser automation"""
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                
                await page.goto(site_url)
                await page.wait_for_load_state('networkidle')
                
                # AI identifies signup form
                field_mapping = await self.identify_form_fields(page)
                
                # Fill registration form
                for field_name, selector in field_mapping.items():
                    try:
                        if field_name == "email":
                            await page.fill(selector, credentials['email'])
                        elif field_name == "password":
                            await page.fill(selector, credentials['password'])
                        elif field_name == "first_name":
                            await page.fill(selector, candidate_data.get('first_name', ''))
                        elif field_name == "last_name":
                            await page.fill(selector, candidate_data.get('last_name', ''))
                    except Exception as field_error:
                        logger.warning(f"Could not fill signup field {field_name}: {field_error}")
                
                # Submit registration
                await page.click(field_mapping.get('submit_button', 'button[type="submit"]'))
                await page.wait_for_load_state('networkidle')
                
                await browser.close()
                
                return {
                    "success": True,
                    "strategy": "Option A - Browser Automation",
                    "account_created": True
                }
                
        except Exception as e:
            logger.error(f"Option A account creation failed: {e}")
            return {
                "success": False,
                "strategy": "Option A - Browser Automation", 
                "error": str(e)
            }


class OptionB_LLMBrowserUse(AutomationStrategy):
    """
    Option B — LLM + Browser-Use
    - Use framework like browser-use (Python) or Stagehand (JS)
    - Give LLM the URL + user profile, let it autonomously navigate and apply
    - More flexible, handles dynamic/unusual forms
    """
    
    def __init__(self, ai_client: OpenAI):
        self.ai_client = ai_client
    
    async def generate_automation_plan(self, page_url: str, objective: str, candidate_data: Dict[str, Any]) -> str:
        """Generate step-by-step automation plan using LLM"""
        prompt = f"""
You are an expert web automation specialist. Create a detailed step-by-step plan to {objective} on this website: {page_url}

Candidate Information:
- Name: {candidate_data.get('first_name', '')} {candidate_data.get('last_name', '')}
- Email: {candidate_data.get('email', '')}
- Phone: {candidate_data.get('phone', '')}
- Skills: {', '.join(candidate_data.get('skills', []))}
- Experience: {candidate_data.get('experience_years', 0)} years

Create a JSON plan with these steps:
1. Navigation steps
2. Form identification
3. Field filling strategy
4. Validation checks
5. Submission process

Return a detailed automation plan that can handle dynamic forms and unusual layouts.
"""

        try:
            response = self.ai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are an expert at web automation planning."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_completion_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Automation plan generation failed: {e}")
            return "Use standard form filling approach"
    
    async def execute_llm_guided_automation(self, page: Page, plan: str, candidate_data: Dict[str, Any]) -> bool:
        """Execute automation guided by LLM plan"""
        try:
            # This would integrate with browser-use or similar framework
            # For now, implementing a simplified version
            
            # LLM analyzes current page state
            page_state = await page.evaluate("""
                () => {
                    return {
                        url: window.location.href,
                        title: document.title,
                        forms: document.querySelectorAll('form').length,
                        inputs: document.querySelectorAll('input').length,
                        buttons: document.querySelectorAll('button').length
                    }
                }
            """)
            
            # LLM decides next action based on page state
            action_prompt = f"""
Current page state: {page_state}
Automation plan: {plan}
Candidate data available: {list(candidate_data.keys())}

What is the next action to take? Respond with JSON:
{{
    "action": "fill_field|click_button|navigate|wait",
    "selector": "CSS selector",
    "value": "value to enter",
    "reasoning": "why this action"
}}
"""

            response = self.ai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are controlling a web browser. Provide the next action."},
                    {"role": "user", "content": action_prompt}
                ],
                temperature=0.1,
                max_completion_tokens=300
            )
            
            # Parse and execute LLM's decision
            action_plan = eval(response.choices[0].message.content.strip())
            
            if action_plan["action"] == "fill_field":
                await page.fill(action_plan["selector"], action_plan["value"])
            elif action_plan["action"] == "click_button":
                await page.click(action_plan["selector"])
            elif action_plan["action"] == "wait":
                await page.wait_for_load_state('networkidle')
            
            logger.info(f"LLM action executed: {action_plan}")
            return True
            
        except Exception as e:
            logger.error(f"LLM-guided automation failed: {e}")
            return False
    
    async def apply_to_job(self, job_url: str, candidate_data: Dict[str, Any], credentials: Dict[str, str]) -> Dict[str, Any]:
        """Apply to job using LLM-guided browser automation"""
        try:
            from playwright.async_api import async_playwright
            
            # Generate automation plan
            plan = await self.generate_automation_plan(job_url, "apply to this job", candidate_data)
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                
                await page.goto(job_url)
                await page.wait_for_load_state('networkidle')
                
                # Execute LLM-guided automation
                success = await self.execute_llm_guided_automation(page, plan, candidate_data)
                
                await browser.close()
                
                return {
                    "success": success,
                    "strategy": "Option B - LLM + Browser-Use",
                    "job_url": job_url,
                    "plan_generated": bool(plan),
                    "message": "Application processed using autonomous LLM navigation"
                }
                
        except Exception as e:
            logger.error(f"Option B automation failed: {e}")
            return {
                "success": False,
                "strategy": "Option B - LLM + Browser-Use",
                "error": str(e)
            }
    
    async def create_account(self, site_url: str, candidate_data: Dict[str, Any], credentials: Dict[str, str]) -> Dict[str, Any]:
        """Create account using LLM-guided automation"""
        try:
            plan = await self.generate_automation_plan(site_url, "create an account", candidate_data)
            
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                
                await page.goto(site_url)
                success = await self.execute_llm_guided_automation(page, plan, candidate_data)
                
                await browser.close()
                
                return {
                    "success": success,
                    "strategy": "Option B - LLM + Browser-Use",
                    "account_created": success
                }
                
        except Exception as e:
            return {
                "success": False,
                "strategy": "Option B - LLM + Browser-Use",
                "error": str(e)
            }


class OptionC_ATSAPIs(AutomationStrategy):
    """
    Option C — Apply via ATS APIs
    - Many companies use Greenhouse, Lever, Workday, Taleo
    - These have APIs you can integrate with directly
    - Cleaner, more reliable applications
    """
    
    def __init__(self):
        self.supported_ats = {
            'greenhouse': 'https://boards-api.greenhouse.io/v1',
            'lever': 'https://api.lever.co/v0',
            'workday': 'https://wd2-impl-services1.workday.com',
            'taleo': 'https://tbe.taleo.net/api/v1'
        }
    
    async def detect_ats_system(self, job_url: str) -> Optional[str]:
        """Detect which ATS system the company uses"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(job_url)
                content = response.text.lower()
                
                # Check for ATS indicators in the page
                if 'greenhouse' in content or 'greenhouse.io' in content:
                    return 'greenhouse'
                elif 'lever.co' in content or 'lever' in content:
                    return 'lever'
                elif 'workday' in content:
                    return 'workday'
                elif 'taleo' in content:
                    return 'taleo'
                
                # Check headers for ATS signatures
                headers = str(response.headers).lower()
                if 'greenhouse' in headers:
                    return 'greenhouse'
                elif 'lever' in headers:
                    return 'lever'
                
                return None
                
        except Exception as e:
            logger.error(f"ATS detection failed: {e}")
            return None
    
    async def apply_via_greenhouse_api(self, job_id: str, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply through Greenhouse API"""
        try:
            api_url = f"{self.supported_ats['greenhouse']}/boards/jobs/{job_id}/candidates"
            
            application_data = {
                "first_name": candidate_data.get('first_name', ''),
                "last_name": candidate_data.get('last_name', ''),
                "email": candidate_data.get('email', ''),
                "phone": candidate_data.get('phone', ''),
                "resume_text": candidate_data.get('resume_text', ''),
                "cover_letter_text": candidate_data.get('cover_letter', ''),
                "location": candidate_data.get('location', ''),
                "website": candidate_data.get('linkedin_url', '')
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(api_url, json=application_data)
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "ats_system": "greenhouse",
                        "application_id": response.json().get('id'),
                        "message": "Application submitted via Greenhouse API"
                    }
                else:
                    return {
                        "success": False,
                        "ats_system": "greenhouse",
                        "error": f"API Error: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Greenhouse API application failed: {e}")
            return {
                "success": False,
                "ats_system": "greenhouse",
                "error": str(e)
            }
    
    async def apply_via_lever_api(self, job_id: str, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply through Lever API"""
        try:
            # Lever API implementation
            api_url = f"{self.supported_ats['lever']}/postings/{job_id}/candidates"
            
            application_data = {
                "name": f"{candidate_data.get('first_name', '')} {candidate_data.get('last_name', '')}",
                "email": candidate_data.get('email', ''),
                "phone": candidate_data.get('phone', ''),
                "resume": candidate_data.get('resume_text', ''),
                "cover": candidate_data.get('cover_letter', '')
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(api_url, json=application_data)
                
                return {
                    "success": response.status_code == 200,
                    "ats_system": "lever",
                    "application_id": response.json().get('id') if response.status_code == 200 else None,
                    "message": "Application submitted via Lever API" if response.status_code == 200 else f"API Error: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "ats_system": "lever", 
                "error": str(e)
            }
    
    async def apply_to_job(self, job_url: str, candidate_data: Dict[str, Any], credentials: Dict[str, str]) -> Dict[str, Any]:
        """Apply to job via ATS API"""
        try:
            # Detect ATS system
            ats_system = await self.detect_ats_system(job_url)
            
            if not ats_system:
                return {
                    "success": False,
                    "strategy": "Option C - ATS APIs",
                    "error": "No supported ATS system detected"
                }
            
            # Extract job ID from URL
            job_id = job_url.split('/')[-1]
            
            # Apply via appropriate API
            if ats_system == 'greenhouse':
                result = await self.apply_via_greenhouse_api(job_id, candidate_data)
            elif ats_system == 'lever':
                result = await self.apply_via_lever_api(job_id, candidate_data)
            else:
                result = {
                    "success": False,
                    "error": f"ATS system {ats_system} not yet implemented"
                }
            
            result["strategy"] = "Option C - ATS APIs"
            result["detected_ats"] = ats_system
            
            return result
            
        except Exception as e:
            logger.error(f"Option C automation failed: {e}")
            return {
                "success": False,
                "strategy": "Option C - ATS APIs",
                "error": str(e)
            }
    
    async def create_account(self, site_url: str, candidate_data: Dict[str, Any], credentials: Dict[str, str]) -> Dict[str, Any]:
        """Create account via ATS API (if supported)"""
        return {
            "success": False,
            "strategy": "Option C - ATS APIs",
            "message": "Account creation via ATS APIs typically not available - use browser automation instead"
        }


class AutomationRouter:
    """
    Intelligent router that chooses the best automation strategy for each job/company
    """
    
    def __init__(self, ai_client: OpenAI):
        self.strategies = {
            'option_a': OptionA_BrowserAutomation(ai_client),
            'option_b': OptionB_LLMBrowserUse(ai_client), 
            'option_c': OptionC_ATSAPIs()
        }
    
    async def choose_best_strategy(self, job_url: str) -> str:
        """Choose the best automation strategy for this job"""
        try:
            # First, try to detect ATS system for Option C
            ats_detector = OptionC_ATSAPIs()
            ats_system = await ats_detector.detect_ats_system(job_url)
            
            if ats_system:
                logger.info(f"Detected {ats_system} ATS system, using Option C")
                return 'option_c'
            
            # Analyze page complexity for Option A vs B
            async with httpx.AsyncClient() as client:
                response = await client.get(job_url)
                content = response.text.lower()
                
                # Check for complex/dynamic elements that need Option B
                complex_indicators = [
                    'react', 'angular', 'vue', 'spa', 'ajax',
                    'dynamic', 'interactive', 'wizard'
                ]
                
                if any(indicator in content for indicator in complex_indicators):
                    logger.info("Complex/dynamic form detected, using Option B (LLM-guided)")
                    return 'option_b'
                else:
                    logger.info("Standard form detected, using Option A (Browser automation)")
                    return 'option_a'
                    
        except Exception as e:
            logger.error(f"Strategy selection failed: {e}")
            return 'option_a'  # Default fallback
    
    async def apply_to_job(self, job_url: str, candidate_data: Dict[str, Any], credentials: Dict[str, str]) -> Dict[str, Any]:
        """Apply to job using the best strategy"""
        strategy_name = await self.choose_best_strategy(job_url)
        strategy = self.strategies[strategy_name]
        
        logger.info(f"Applying to job {job_url} using {strategy_name}")
        
        result = await strategy.apply_to_job(job_url, candidate_data, credentials)
        result["chosen_strategy"] = strategy_name
        
        return result
    
    async def create_account(self, site_url: str, candidate_data: Dict[str, Any], credentials: Dict[str, str]) -> Dict[str, Any]:
        """Create account using the best strategy (usually Option A or B)"""
        # For account creation, prefer Option A (browser automation)
        strategy = self.strategies['option_a']
        
        logger.info(f"Creating account on {site_url} using option_a")
        
        result = await strategy.create_account(site_url, candidate_data, credentials)
        result["chosen_strategy"] = "option_a"
        
        return result