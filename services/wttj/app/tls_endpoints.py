#!/usr/bin/env python3
"""
FastAPI endpoints for TLS-based WTTJ account creation
"""
import os
import sys
import logging
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict
import json

# Add root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from services.wttj.app.tls_account_service import (
    get_service, reset_service, TLSAccountService, RateLimitConfig
)

# Import bot bypass handler
try:
    from wttj_bot_bypass import WTTJBotBypass
except ImportError:
    WTTJBotBypass = None
    logger_init = logging.getLogger(__name__)
    logger_init.warning("⚠️ Bot bypass handler not available")

# Import captcha solver (requires CAPTCHA_API_KEY env var to actually solve)
try:
    from captcha_solver import (
        CaptchaSolver, detect_recaptcha_config, inject_recaptcha_token, WTTJ_SITE_KEY
    )
except ImportError:
    CaptchaSolver = None
    detect_recaptcha_config = None
    inject_recaptcha_token = None
    WTTJ_SITE_KEY = "6Lek6X8jAAAAADI-_bRv_LqNz_S6LE5do6UZf6og"
    logging.getLogger(__name__).warning("⚠️ Captcha solver not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tls", tags=["TLS Account Creation"])


# ============================================================================
# Pydantic Models
# ============================================================================

class CreateAccountRequest(BaseModel):
    """Request to create a single account"""
    email: str
    password: str
    first_name: str
    last_name: str
    ip_address: Optional[str] = None
    use_hybrid: bool = True


class CreateAccountsBatchRequest(BaseModel):
    """Request to create multiple accounts"""
    accounts: List[Dict]  # List of account dicts
    ip_address: Optional[str] = None
    use_hybrid: bool = True


class RateLimitConfigRequest(BaseModel):
    """Configure rate limiting"""
    min_delay_between_requests: float = 2.0
    max_delay_between_requests: float = 8.0
    max_requests_per_ip_per_hour: int = 5
    max_requests_per_ip_per_day: int = 20
    max_requests_per_email_per_day: int = 1
    max_burst_requests: int = 2
    enable_jitter: bool = True
    enable_proxy_rotation: bool = True
    enable_ua_rotation: bool = True


class ProxyListRequest(BaseModel):
    """Configure proxies"""
    proxies: List[str]


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/create-account")
async def create_account(req: CreateAccountRequest, background_tasks: BackgroundTasks):
    """
    Create a single WTTJ account using TLS with rate limiting
    
    **Features:**
    - TLS fingerprinting bypass
    - Automatic rate limiting
    - User-agent rotation
    - Proxy rotation
    - Human-like delays
    
    **Example:**
    ```json
    {
        "email": "user@example.com",
        "password": "SecurePass123!@",
        "first_name": "John",
        "last_name": "Doe",
        "ip_address": "203.0.113.1",
        "use_hybrid": true
    }
    ```
    """
    try:
        logger.info(f"📍 TLS account creation request: {req.email}")
        
        service = get_service()
        
        result = await service.create_account_with_rate_limiting(
            email=req.email,
            password=req.password,
            first_name=req.first_name,
            last_name=req.last_name,
            ip_address=req.ip_address,
            use_hybrid=req.use_hybrid
        )
        
        return {
            "status": "created" if result.get("success") else "failed",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ Account creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-accounts-batch")
async def create_accounts_batch(req: CreateAccountsBatchRequest, background_tasks: BackgroundTasks):
    """
    Create multiple WTTJ accounts with rate limiting
    
    **Features:**
    - Batch processing with rate limiting
    - Progressive delays between accounts
    - Comprehensive statistics
    - Error recovery
    
    **Example:**
    ```json
    {
        "accounts": [
            {
                "email": "user1@example.com",
                "password": "SecurePass123!@",
                "first_name": "John",
                "last_name": "Doe"
            },
            {
                "email": "user2@example.com",
                "password": "AnotherPass456!@",
                "first_name": "Jane",
                "last_name": "Smith"
            }
        ],
        "ip_address": "203.0.113.1",
        "use_hybrid": true
    }
    ```
    """
    try:
        logger.info(f"📦 Batch account creation: {len(req.accounts)} accounts")
        
        service = get_service()
        
        result = await service.create_accounts_batch(
            accounts=req.accounts,
            ip_address=req.ip_address,
            use_hybrid=req.use_hybrid
        )
        
        return {
            "status": "batch_complete",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ Batch creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/configure-rate-limits")
async def configure_rate_limits(config: RateLimitConfigRequest):
    """
    Configure rate limiting parameters
    
    **Rate Limit Parameters:**
    - `min_delay_between_requests`: Minimum seconds between requests
    - `max_delay_between_requests`: Maximum seconds between requests
    - `max_requests_per_ip_per_hour`: Max accounts per IP per hour
    - `max_requests_per_ip_per_day`: Max accounts per IP per day
    - `max_requests_per_email_per_day`: Max creates per email per day
    - `enable_jitter`: Add randomness to delays
    - `enable_proxy_rotation`: Rotate proxies between requests
    - `enable_ua_rotation`: Rotate user agents between requests
    """
    try:
        logger.info("⚙️  Configuring rate limits...")
        
        # Create new config
        rate_config = RateLimitConfig(
            min_delay_between_requests=config.min_delay_between_requests,
            max_delay_between_requests=config.max_delay_between_requests,
            max_requests_per_ip_per_hour=config.max_requests_per_ip_per_hour,
            max_requests_per_ip_per_day=config.max_requests_per_ip_per_day,
            max_requests_per_email_per_day=config.max_requests_per_email_per_day,
            max_burst_requests=config.max_burst_requests,
            enable_jitter=config.enable_jitter,
            enable_proxy_rotation=config.enable_proxy_rotation,
            enable_ua_rotation=config.enable_ua_rotation,
        )
        
        # Reset service with new config
        reset_service()
        service = get_service(config=rate_config)
        
        logger.info("✅ Rate limits configured")
        
        return {
            "status": "configured",
            "config": {
                "min_delay": config.min_delay_between_requests,
                "max_delay": config.max_delay_between_requests,
                "max_requests_per_ip_per_hour": config.max_requests_per_ip_per_hour,
                "max_requests_per_ip_per_day": config.max_requests_per_ip_per_day,
                "enable_jitter": config.enable_jitter,
                "enable_proxy_rotation": config.enable_proxy_rotation,
                "enable_ua_rotation": config.enable_ua_rotation,
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Configuration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/configure-proxies")
async def configure_proxies(req: ProxyListRequest):
    """
    Configure proxy list for rotation
    
    **Example:**
    ```json
    {
        "proxies": [
            "http://user:pass@proxy1:8080",
            "http://user:pass@proxy2:8080",
            "http://user:pass@proxy3:8080"
        ]
    }
    ```
    """
    try:
        logger.info(f"🔗 Configuring {len(req.proxies)} proxies...")
        
        service = get_service()
        service.rate_limiter.set_proxies(req.proxies)
        
        logger.info("✅ Proxies configured")
        
        return {
            "status": "configured",
            "proxy_count": len(req.proxies)
        }
        
    except Exception as e:
        logger.error(f"❌ Proxy configuration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics():
    """Get current service statistics"""
    try:
        service = get_service()
        stats = service.get_statistics()
        
        return {
            "status": "ok",
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bypass-and-create-account")
async def bypass_and_create_account(
    email: str,
    password: str,
    first_name: str,
    signup_url: str = "https://www.welcometothejungle.com/fr/authenticate/signup",
    headless: bool = True,
    proxy: Optional[str] = None
):
    """
    Complete automated flow:
    1. Bypass bot/captcha challenge
    2. Fill signup form (First name, Email, Password)
    3. Click 'Agree and create profile' button
    
    **Example:**
    ```json
    {
        "email": "newuser@example.com",
        "password": "SecurePass123!@",
        "first_name": "John",
        "signup_url": "https://www.welcometothejungle.com/users/sign_up",
        "headless": false,
        "proxy": null
    }
    ```
    """
    if not WTTJBotBypass:
        raise HTTPException(
            status_code=503,
            detail="Bot bypass handler not available"
        )
    
    try:
        logger.info(f"🤖 Complete signup flow for {email}")
        
        # Fall back to PROXY_URL env var if no proxy passed in the request
        effective_proxy = proxy or os.getenv("PROXY_URL", "").strip() or None
        if effective_proxy:
            logger.info("🔗 Proxy configured for this signup")
        
        bypass = WTTJBotBypass(headless=headless, use_proxy=effective_proxy)
        
        try:
            # Step 1: Launch browser
            await bypass.launch()
            logger.info("✅ Browser launched")
            
            # Step 2: Bypass bot challenge
            logger.info("Step 1/4: Bypassing bot challenge...")
            result = await bypass.bypass_captcha(signup_url, timeout=60)
            if not result:
                return {
                    "status": "failed",
                    "step": "bot_bypass",
                    "message": "Failed to bypass bot challenge"
                }
            logger.info("✅ Bot challenge bypassed")
            
            # Step 3: Fill form
            logger.info("Step 2/4: Filling signup form...")
            form_filled = await bypass.fill_signup_form(
                email=email,
                password=password,
                first_name=first_name
            )
            if not form_filled:
                logger.warning("⚠️ Form filling encountered issues but continuing...")
            
            # Set up network monitoring to capture the registration API response
            captured_responses = []
            console_messages = []
            
            async def _on_response(response):
                try:
                    method = response.request.method
                    url_l = response.url.lower()
                    # Capture all POST/PUT (form submissions) and any registration-related calls
                    is_relevant = (
                        method in ("POST", "PUT", "PATCH")
                        or any(k in url_l for k in ["register", "signup", "sign_up", "graphql", "account", "auth"])
                    )
                    # Skip noise (analytics, tracking pixels, static assets)
                    is_noise = any(k in url_l for k in [
                        ".png", ".jpg", ".svg", ".css", ".woff", ".gif",
                        "google-analytics", "googletagmanager", "segment", "datadog",
                        "sentry", "hotjar", "doubleclick", "facebook", "/gtm", "/collect"
                    ])
                    if is_relevant and not is_noise:
                        entry = {
                            "url": response.url[:200],
                            "status": response.status,
                            "method": method,
                        }
                        try:
                            ct = response.headers.get("content-type", "")
                            if "json" in ct or "text" in ct:
                                body = await response.text()
                                entry["body"] = body[:400]
                        except Exception:
                            pass
                        captured_responses.append(entry)
                        logger.info(f"🌐 {method} {response.status} {response.url[:120]}")
                except Exception:
                    pass
            
            def _on_console(msg):
                try:
                    if msg.type in ("error", "warning"):
                        console_messages.append(f"[{msg.type}] {msg.text[:200]}")
                except Exception:
                    pass
            
            bypass.page.on("response", lambda r: asyncio.create_task(_on_response(r)))
            bypass.page.on("console", _on_console)
            bypass.page.on("pageerror", lambda e: console_messages.append(f"[pageerror] {str(e)[:200]}"))
            
            # Step 3.5: Solve reCAPTCHA (the confirmed blocker: server returns
            # 400 invalid_recaptcha for automated browsers without a valid token)
            captcha_info = {"attempted": False, "solved": False, "provider": None, "version": None}
            if CaptchaSolver is not None:
                solver = CaptchaSolver()
                captcha_info["provider"] = solver.provider
                if solver.enabled:
                    captcha_info["attempted"] = True
                    logger.info("🧩 Solving reCAPTCHA via captcha service...")
                    try:
                        cfg = await detect_recaptcha_config(bypass.page)
                        site_key = cfg.get("site_key") or WTTJ_SITE_KEY
                        version = cfg.get("version") or "v3"
                        captcha_info["version"] = version
                        page_url = bypass.page.url

                        token = None
                        if version == "v3":
                            token = await solver.solve_recaptcha_v3(
                                site_key=site_key, page_url=page_url, action="submit"
                            )
                            # Fallback to v2-invisible if v3 fails
                            if not token:
                                logger.info("v3 solve failed, trying v2-invisible...")
                                token = await solver.solve_recaptcha_v2(
                                    site_key=site_key, page_url=page_url, invisible=True
                                )
                        else:
                            token = await solver.solve_recaptcha_v2(
                                site_key=site_key, page_url=page_url,
                                invisible=cfg.get("invisible", True)
                            )

                        if token:
                            await inject_recaptcha_token(bypass.page, token)
                            captcha_info["solved"] = True
                            logger.info("✅ reCAPTCHA token injected")
                        else:
                            logger.warning("⚠️ Captcha service did not return a token")
                    except Exception as cap_ex:
                        logger.error(f"Captcha solving error: {cap_ex}")
                else:
                    logger.warning(
                        "⚠️ No CAPTCHA_API_KEY configured. Registration will be "
                        "rejected with invalid_recaptcha. Set CAPTCHA_API_KEY to enable."
                    )
            
            # Step 4: Click Agree button
            logger.info("Step 3/4: Clicking 'Agree and create profile' button...")
            agree_clicked = await bypass.click_agree_button()
            if not agree_clicked:
                return {
                    "status": "failed",
                    "step": "agree_button",
                    "message": "Could not find or click 'Agree and create profile' button"
                }
            logger.info("✅ Agree button clicked")
            
            # Step 5: Wait for account creation
            logger.info("Step 4/4: Waiting for account creation...")
            await asyncio.sleep(5)
            
            final_url = bypass.page.url if bypass.page else "unknown"
            initial_url = signup_url
            
            # Capture screenshot and any error messages for diagnosis
            error_messages = []
            page_title = ""
            try:
                page_title = await bypass.page.title()
                # Look for common error indicators
                error_messages = await bypass.page.evaluate("""() => {
                    const errors = [];
                    // Standard error selectors
                    document.querySelectorAll('[class*="error" i], [role="alert"], [class*="invalid" i], [class*="Error"]').forEach(el => {
                        const t = el.textContent.trim();
                        if (t && t.length < 300) errors.push(t);
                    });
                    return [...new Set(errors)].slice(0, 10);
                }""")
                
                # Save screenshot
                screenshot_dir = "/app/screenshots"
                os.makedirs(screenshot_dir, exist_ok=True)
                screenshot_path = f"{screenshot_dir}/signup_result_{email.replace('@','_at_')}.png"
                await bypass.page.screenshot(path=screenshot_path, full_page=True)
                logger.info(f"📸 Screenshot saved: {screenshot_path}")
            except Exception as diag_ex:
                logger.warning(f"Diagnostics capture failed: {diag_ex}")
            
            # Detect actual success: URL should change away from signup page
            url_changed = final_url != initial_url and "signup" not in final_url.lower() and "sign_up" not in final_url.lower()
            # Onboarding redirect also indicates success (use path-specific markers, NOT "welcome" which is in the domain)
            final_path = final_url.lower()
            onboarding_reached = any(k in final_path for k in ["/onboarding", "complete-profile", "/dashboard", "/home"])
            
            # Check captured API responses for registration result
            registration_api = [r for r in captured_responses if any(k in r["url"].lower() for k in ["registration", "register", "signup", "sign_up", "/api/v3/reg"])]
            api_success = any(r.get("status") in (200, 201, 204) for r in registration_api)
            api_rejected = any(r.get("status") in (400, 401, 403, 422, 429) for r in registration_api)
            
            if url_changed or onboarding_reached:
                status = "completed"
            elif api_rejected:
                status = "rejected_by_server"
            else:
                status = "form_submitted_but_not_navigated"
            
            logger.info(f"✅ Signup flow ended. Final URL: {final_url}, Changed: {url_changed}, Onboarding: {onboarding_reached}")
            logger.info(f"🌐 Captured {len(captured_responses)} API responses, registration-related: {len(registration_api)}")
            
            return {
                "status": status,
                "email": email,
                "message": (
                    "Account created successfully - redirected to onboarding" if (url_changed or onboarding_reached)
                    else "Form submitted but server rejected registration (likely reCAPTCHA/bot detection)" if api_rejected
                    else "Form submitted but page did not navigate - check reCAPTCHA and API responses"
                ),
                "steps_completed": [
                    "Bot challenge bypassed",
                    "Form filled (First name, Email, Password)",
                    "Agree button clicked",
                ],
                "initial_url": initial_url,
                "final_url": final_url,
                "url_changed": url_changed,
                "onboarding_reached": onboarding_reached,
                "page_title": page_title,
                "error_messages_on_page": error_messages,
                "api_responses": captured_responses[:20],
                "console_errors": console_messages[:20],
                "registration_api_success": api_success,
                "registration_api_rejected": api_rejected,
                "captcha": captcha_info,
            }
        
        finally:
            await bypass.close()
            
    except Exception as e:
        logger.error(f"❌ Signup flow error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Signup flow failed: {str(e)}")


@router.post("/bypass-bot-challenge")
async def bypass_bot_challenge(
    signup_url: str = "https://www.welcometothejungle.com/fr/authenticate/signup",
    headless: bool = True,
    proxy: Optional[str] = None
):
    """
    Bypass WTTJ bot/captcha challenge before account creation
    
    Opens Firefox browser and navigates through Cloudflare/reCAPTCHA challenges
    to get to the actual signup form.
    
    **Features:**
    - Handles Cloudflare challenges
    - Handles reCAPTCHA challenges
    - Stealth Firefox with anti-detection headers
    - Proxy support
    
    **Example:**
    ```json
    {
        "signup_url": "https://www.welcometothejungle.com/users/sign_up",
        "headless": false,
        "proxy": "http://user:pass@proxy:8080"
    }
    ```
    """
    if not WTTJBotBypass:
        raise HTTPException(
            status_code=503,
            detail="Bot bypass handler not available"
        )
    
    try:
        logger.info(f"🤖 Bot bypass requested for {signup_url}")
        
        bypass = WTTJBotBypass(headless=headless, use_proxy=proxy)
        
        try:
            await bypass.launch()
            result = await bypass.bypass_captcha(signup_url, timeout=60)
            
            if result:
                logger.info("✅ Bot challenge bypassed successfully")
                return {
                    "status": "bypassed",
                    "url": signup_url,
                    "message": "Successfully bypassed bot/captcha challenge",
                    "page_ready": True
                }
            else:
                logger.warning("⚠️ Bot bypass may have failed")
                return {
                    "status": "partial",
                    "url": signup_url,
                    "message": "Attempted bot bypass with uncertain result",
                    "page_ready": False
                }
        
        finally:
            await bypass.close()
            
    except Exception as e:
        logger.error(f"❌ Bot bypass error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Bot bypass failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check for TLS service"""
    try:
        service = get_service()
        
        return {
            "status": "healthy",
            "service": "tls-account-creation",
            "requests_processed": len(service.creation_results),
            "rate_limiter_active": True,
            "bot_bypass_available": WTTJBotBypass is not None
        }
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-report")
async def export_report(filename: str = "tls_account_service_report.json"):
    """Export detailed report of all operations"""
    try:
        service = get_service()
        report = service.export_report(filename)
        
        logger.info(f"📊 Report exported to {filename}")
        
        return {
            "status": "exported",
            "filename": filename,
            "records": len(report.get("creation_results", []))
        }
        
    except Exception as e:
        logger.error(f"❌ Report export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_service_endpoint():
    """Reset service instance"""
    try:
        reset_service()
        logger.info("🔄 Service reset")
        
        return {
            "status": "reset",
            "message": "Service instance has been reset"
        }
        
    except Exception as e:
        logger.error(f"❌ Reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export router
__all__ = ["router"]
