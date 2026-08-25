#!/usr/bin/env python3
"""
Captcha Solver Integration for WTTJ Signup

Solves Google reCAPTCHA (v2-invisible and v3) using a third-party
captcha-solving service. Supports 2Captcha and CapSolver.

The service requires a PAID API key. Set it via environment variable:
    CAPTCHA_API_KEY=your_key_here
    CAPTCHA_PROVIDER=2captcha   # or "capsolver"

WTTJ uses reCAPTCHA with site key: 6Lek6X8jAAAAADI-_bRv_LqNz_S6LE5do6UZf6og

How it works:
  reCAPTCHA v3 / v2-invisible generate a fresh token at submit time via
  grecaptcha.execute(). To use a solved token, we override grecaptcha.execute
  on the page so that WTTJ's frontend receives OUR solved token instead of
  generating its own (which would fail the bot score).
"""
import os
import asyncio
import logging
from typing import Optional

import httpx

logger = logging.getLogger("captcha_solver")

# Default WTTJ reCAPTCHA site key (auto-detected at runtime, this is fallback)
WTTJ_SITE_KEY = "6Lek6X8jAAAAADI-_bRv_LqNz_S6LE5do6UZf6og"


class CaptchaSolver:
    """Solves reCAPTCHA via a third-party service (2Captcha / CapSolver)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("CAPTCHA_API_KEY", "").strip()
        self.provider = (provider or os.getenv("CAPTCHA_PROVIDER", "2captcha")).strip().lower()

    @property
    def enabled(self) -> bool:
        """True if a captcha API key is configured."""
        return bool(self.api_key)

    async def solve_recaptcha_v3(
        self,
        site_key: str,
        page_url: str,
        action: str = "submit",
        min_score: float = 0.3,
        timeout: int = 180,
    ) -> Optional[str]:
        """Solve reCAPTCHA v3 and return the token, or None on failure."""
        if not self.enabled:
            logger.warning("Captcha solver not enabled (no CAPTCHA_API_KEY)")
            return None

        if self.provider == "capsolver":
            return await self._solve_capsolver(site_key, page_url, action, min_score, timeout, version="v3")
        return await self._solve_2captcha(site_key, page_url, action, min_score, timeout, version="v3")

    async def solve_recaptcha_v2(
        self,
        site_key: str,
        page_url: str,
        invisible: bool = True,
        timeout: int = 180,
    ) -> Optional[str]:
        """Solve reCAPTCHA v2 (invisible) and return the token, or None on failure."""
        if not self.enabled:
            logger.warning("Captcha solver not enabled (no CAPTCHA_API_KEY)")
            return None

        if self.provider == "capsolver":
            return await self._solve_capsolver(site_key, page_url, "", 0, timeout, version="v2", invisible=invisible)
        return await self._solve_2captcha(site_key, page_url, "", 0, timeout, version="v2", invisible=invisible)

    # ------------------------------------------------------------------
    # 2Captcha implementation
    # ------------------------------------------------------------------
    async def _solve_2captcha(
        self,
        site_key: str,
        page_url: str,
        action: str,
        min_score: float,
        timeout: int,
        version: str = "v3",
        invisible: bool = True,
    ) -> Optional[str]:
        base = "https://2captcha.com"
        params = {
            "key": self.api_key,
            "method": "userrecaptcha",
            "googlekey": site_key,
            "pageurl": page_url,
            "json": 1,
        }
        if version == "v3":
            params["version"] = "v3"
            params["action"] = action
            params["min_score"] = min_score
        else:
            if invisible:
                params["invisible"] = 1

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Submit captcha task
                r = await client.post(f"{base}/in.php", data=params)
                data = r.json()
                if data.get("status") != 1:
                    logger.error(f"2Captcha submit failed: {data}")
                    return None
                captcha_id = data["request"]
                logger.info(f"2Captcha task submitted: {captcha_id} (version={version})")

                # Poll for result
                elapsed = 0
                await asyncio.sleep(15)  # initial wait
                elapsed += 15
                while elapsed < timeout:
                    res = await client.get(
                        f"{base}/res.php",
                        params={"key": self.api_key, "action": "get", "id": captcha_id, "json": 1},
                    )
                    res_data = res.json()
                    if res_data.get("status") == 1:
                        token = res_data["request"]
                        logger.info("✅ 2Captcha solved reCAPTCHA")
                        return token
                    if res_data.get("request") != "CAPCHA_NOT_READY":
                        logger.error(f"2Captcha error: {res_data}")
                        return None
                    await asyncio.sleep(5)
                    elapsed += 5

                logger.error("2Captcha timed out")
                return None
        except Exception as e:
            logger.error(f"2Captcha request error: {e}")
            return None

    # ------------------------------------------------------------------
    # CapSolver implementation
    # ------------------------------------------------------------------
    async def _solve_capsolver(
        self,
        site_key: str,
        page_url: str,
        action: str,
        min_score: float,
        timeout: int,
        version: str = "v3",
        invisible: bool = True,
    ) -> Optional[str]:
        base = "https://api.capsolver.com"
        if version == "v3":
            task = {
                "type": "ReCaptchaV3TaskProxyLess",
                "websiteURL": page_url,
                "websiteKey": site_key,
                "pageAction": action,
                "minScore": min_score,
            }
        else:
            task = {
                "type": "ReCaptchaV2TaskProxyLess",
                "websiteURL": page_url,
                "websiteKey": site_key,
                "isInvisible": invisible,
            }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    f"{base}/createTask",
                    json={"clientKey": self.api_key, "task": task},
                )
                data = r.json()
                if data.get("errorId") != 0:
                    logger.error(f"CapSolver create task failed: {data}")
                    return None
                task_id = data["taskId"]
                logger.info(f"CapSolver task created: {task_id} (version={version})")

                elapsed = 0
                await asyncio.sleep(5)
                elapsed += 5
                while elapsed < timeout:
                    res = await client.post(
                        f"{base}/getTaskResult",
                        json={"clientKey": self.api_key, "taskId": task_id},
                    )
                    res_data = res.json()
                    if res_data.get("status") == "ready":
                        token = res_data["solution"]["gRecaptchaResponse"]
                        logger.info("✅ CapSolver solved reCAPTCHA")
                        return token
                    if res_data.get("errorId") != 0:
                        logger.error(f"CapSolver error: {res_data}")
                        return None
                    await asyncio.sleep(5)
                    elapsed += 5

                logger.error("CapSolver timed out")
                return None
        except Exception as e:
            logger.error(f"CapSolver request error: {e}")
            return None


async def detect_recaptcha_config(page) -> dict:
    """
    Inspect the page to determine reCAPTCHA version and site key.
    Returns dict: {site_key, version, invisible}
    """
    try:
        config = await page.evaluate("""() => {
            const result = {site_key: null, version: null, invisible: false, scripts: []};

            // Find reCAPTCHA script tags to determine version
            document.querySelectorAll('script[src*="recaptcha"]').forEach(s => {
                result.scripts.push(s.src);
                if (s.src.includes('render=')) {
                    const m = s.src.match(/render=([^&]+)/);
                    if (m && m[1] !== 'explicit') {
                        result.site_key = m[1];
                        result.version = 'v3';
                    }
                }
            });

            // Look for v2 g-recaptcha element
            const el = document.querySelector('.g-recaptcha, [data-sitekey]');
            if (el) {
                result.site_key = el.getAttribute('data-sitekey') || result.site_key;
                if (el.getAttribute('data-size') === 'invisible') result.invisible = true;
                if (!result.version) result.version = 'v2';
            }

            // Check grecaptcha.enterprise
            if (window.grecaptcha && window.grecaptcha.enterprise) {
                result.enterprise = true;
            }

            return result;
        }""")
        logger.info(f"Detected reCAPTCHA config: {config}")
        return config
    except Exception as e:
        logger.warning(f"Could not detect reCAPTCHA config: {e}")
        return {"site_key": None, "version": None, "invisible": False}


async def inject_recaptcha_token(page, token: str):
    """
    Inject the solved reCAPTCHA token into the page.

    For v2: fills the g-recaptcha-response textarea and fires callbacks.
    For v3/invisible: overrides grecaptcha.execute to return our token so
    the site's own submit logic receives it.
    """
    try:
        await page.evaluate(
            """(token) => {
                // Fill v2 textarea if present
                let ta = document.getElementById('g-recaptcha-response');
                if (!ta) {
                    ta = document.createElement('textarea');
                    ta.id = 'g-recaptcha-response';
                    ta.name = 'g-recaptcha-response';
                    ta.style.display = 'none';
                    document.body.appendChild(ta);
                }
                ta.value = token;

                // Override grecaptcha.execute so the site's submit flow
                // receives our solved token instead of generating a new one.
                if (window.grecaptcha) {
                    const solved = token;
                    const origExecute = window.grecaptcha.execute;
                    window.grecaptcha.execute = function() {
                        return Promise.resolve(solved);
                    };
                    if (window.grecaptcha.enterprise) {
                        window.grecaptcha.enterprise.execute = function() {
                            return Promise.resolve(solved);
                        };
                    }
                }
            }""",
            token,
        )
        logger.info("✅ Injected reCAPTCHA token into page")
        return True
    except Exception as e:
        logger.error(f"Failed to inject token: {e}")
        return False
