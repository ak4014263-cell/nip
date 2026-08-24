#!/usr/bin/env python3
"""
FastAPI endpoints for TLS-based WTTJ account creation
"""
import os
import sys
import logging
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


@router.get("/health")
async def health_check():
    """Health check for TLS service"""
    try:
        service = get_service()
        
        return {
            "status": "healthy",
            "service": "tls-account-creation",
            "requests_processed": len(service.creation_results),
            "rate_limiter_active": True
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
