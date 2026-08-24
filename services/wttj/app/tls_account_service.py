#!/usr/bin/env python3
"""
TLS-based WTTJ Account Creation Service
Integrates TLS creator, rate limiter, and CSRF extractor
"""
import asyncio
import logging
import os
import sys
from typing import Dict, Optional, List
from datetime import datetime

# Add root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import components
from tls_wttj_creator import WTTJTLSCreator, create_wttj_account_tls
from rate_limiter import AdaptiveRateLimiter, RateLimitConfig, RequestMetrics
from csrf_extractor import extract_wttj_tokens

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TLSAccountService:
    """Integrated service for TLS-based account creation with rate limiting"""
    
    def __init__(self, config: Optional[RateLimitConfig] = None, proxies: Optional[List[str]] = None):
        """
        Initialize the TLS account service
        
        Args:
            config: RateLimitConfig for rate limiting
            proxies: List of proxy URLs for rotation
        """
        self.rate_limiter = AdaptiveRateLimiter(config or RateLimitConfig())
        
        if proxies:
            self.rate_limiter.set_proxies(proxies)
        else:
            logger.warning("⚠️  No proxies configured. Using direct connection.")
        
        self.tls_creator = WTTJTLSCreator()
        self.creation_results = []
        
        logger.info("✅ TLS Account Service initialized")
    
    async def create_account_with_rate_limiting(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        ip_address: Optional[str] = None,
        use_hybrid: bool = True
    ) -> Dict:
        """
        Create WTTJ account with rate limiting
        
        Args:
            email: Account email
            password: Account password
            first_name: User's first name
            last_name: User's last name
            ip_address: IP address for rate limit tracking
            use_hybrid: Use hybrid method (browser fill + TLS submit)
        
        Returns:
            Dict with account creation result
        """
        try:
            logger.info(f"\n🚀 Creating account with rate limiting: {email}")
            logger.info("=" * 70)
            
            # Step 1: Check rate limits
            logger.info("📍 Step 1: Checking rate limits...")
            allowed, status = self.rate_limiter.check_rate_limits(email, ip_address)
            
            logger.info(f"   Rate limit status: {status}")
            
            if not allowed:
                logger.error(f"❌ Rate limit exceeded")
                return {
                    "success": False,
                    "email": email,
                    "error": "Rate limit exceeded",
                    "status": status,
                    "method": "rate_limited"
                }
            
            # Step 2: Wait before request (human-like delay)
            logger.info("📍 Step 2: Applying human-like delay...")
            delay_before = await self.rate_limiter.wait_before_request()
            
            # Step 3: Get user agent and proxy
            logger.info("📍 Step 3: Rotating user agent and proxy...")
            ua = self.rate_limiter.get_next_user_agent()
            proxy = self.rate_limiter.get_next_proxy()
            
            logger.info(f"   Using proxy: {proxy or 'direct connection'}")
            
            # Step 4: Create account
            logger.info("📍 Step 4: Creating account via TLS...")
            
            result = await create_wttj_account_tls(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                proxy=proxy,
                use_hybrid=use_hybrid
            )
            
            # Step 5: Wait after request
            logger.info("📍 Step 5: Post-request delay...")
            delay_after = await self.rate_limiter.wait_after_request(result.get("success", False))
            
            # Step 6: Record metrics
            logger.info("📍 Step 6: Recording metrics...")
            
            metrics = RequestMetrics(
                timestamp=datetime.utcnow(),
                ip_address=ip_address,
                email=email,
                success=result.get("success", False),
                status_code=result.get("response", {}).get("status", 0) if isinstance(result.get("response"), dict) else 0,
                error_message=result.get("error"),
                delay_before=delay_before,
                delay_after=delay_after
            )
            
            self.rate_limiter.record_request(metrics)
            self.creation_results.append({
                "timestamp": datetime.utcnow().isoformat(),
                "email": email,
                "result": result,
                "metrics": {
                    "delay_before": delay_before,
                    "delay_after": delay_after,
                    "proxy": proxy,
                    "user_agent": ua[:50] + "..." if len(ua) > 50 else ua
                }
            })
            
            logger.info("=" * 70)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Exception during account creation: {e}")
            
            metrics = RequestMetrics(
                timestamp=datetime.utcnow(),
                ip_address=ip_address,
                email=email,
                success=False,
                error_message=str(e),
                delay_before=0.0,
                delay_after=0.0
            )
            self.rate_limiter.record_request(metrics)
            
            return {
                "success": False,
                "email": email,
                "error": str(e),
                "method": "exception"
            }
    
    async def create_accounts_batch(
        self,
        accounts: List[Dict],
        ip_address: Optional[str] = None,
        use_hybrid: bool = True
    ) -> Dict:
        """
        Create multiple accounts with rate limiting
        
        Args:
            accounts: List of account dicts with keys: email, password, first_name, last_name
            ip_address: IP address for rate limit tracking
            use_hybrid: Use hybrid method
        
        Returns:
            Dict with batch results
        """
        try:
            logger.info(f"\n📦 Creating batch of {len(accounts)} accounts")
            logger.info("=" * 70)
            
            results = []
            successful = 0
            failed = 0
            
            for i, account in enumerate(accounts):
                try:
                    logger.info(f"\n[{i+1}/{len(accounts)}] Processing: {account['email']}")
                    
                    result = await self.create_account_with_rate_limiting(
                        email=account['email'],
                        password=account['password'],
                        first_name=account['first_name'],
                        last_name=account['last_name'],
                        ip_address=ip_address,
                        use_hybrid=use_hybrid
                    )
                    
                    results.append(result)
                    
                    if result.get("success"):
                        successful += 1
                    else:
                        failed += 1
                    
                except Exception as e:
                    logger.error(f"❌ Failed to create account {account['email']}: {e}")
                    results.append({
                        "success": False,
                        "email": account['email'],
                        "error": str(e)
                    })
                    failed += 1
            
            logger.info("=" * 70)
            logger.info(f"📊 Batch Complete: {successful} successful, {failed} failed")
            
            return {
                "total": len(accounts),
                "successful": successful,
                "failed": failed,
                "success_rate": f"{(successful/len(accounts)*100):.1f}%" if accounts else "N/A",
                "results": results,
                "statistics": self.rate_limiter.get_stats()
            }
            
        except Exception as e:
            logger.error(f"❌ Batch creation failed: {e}")
            return {
                "error": str(e),
                "total": len(accounts),
                "successful": 0,
                "failed": len(accounts)
            }
    
    def get_statistics(self) -> Dict:
        """Get service statistics"""
        return {
            "rate_limiter_stats": self.rate_limiter.get_stats(),
            "total_results_recorded": len(self.creation_results),
            "last_request": self.creation_results[-1] if self.creation_results else None
        }
    
    def export_report(self, filename: str = "tls_account_service_report.json"):
        """Export detailed report"""
        import json
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": self.get_statistics(),
            "creation_results": self.creation_results
        }
        
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Report exported to {filename}")
        return report


# Global service instance
_service_instance: Optional[TLSAccountService] = None


def get_service(
    config: Optional[RateLimitConfig] = None,
    proxies: Optional[List[str]] = None
) -> TLSAccountService:
    """Get or create service instance"""
    global _service_instance
    
    if _service_instance is None:
        _service_instance = TLSAccountService(config=config, proxies=proxies)
    
    return _service_instance


def reset_service():
    """Reset service instance"""
    global _service_instance
    _service_instance = None


# Test function
async def test_service():
    """Test the TLS account service"""
    
    # Create service with rate limiting config
    config = RateLimitConfig(
        min_delay_between_requests=2.0,
        max_delay_between_requests=5.0,
        max_requests_per_ip_per_hour=5,
        max_requests_per_ip_per_day=20,
        enable_jitter=True,
        enable_proxy_rotation=True,
        enable_ua_rotation=True,
    )
    
    service = TLSAccountService(config=config)
    
    # Set proxies (optional)
    # service.rate_limiter.set_proxies([
    #     "http://proxy1:8080",
    #     "http://proxy2:8080",
    # ])
    
    # Test single account creation
    logger.info("🧪 Testing single account creation...")
    result = await service.create_account_with_rate_limiting(
        email="test@example.com",
        password="SecurePass123!@",
        first_name="Test",
        last_name="User",
        ip_address="203.0.113.1",
        use_hybrid=True
    )
    
    logger.info(f"Result: {result}")
    
    # Get statistics
    stats = service.get_statistics()
    logger.info(f"\n📊 Statistics:\n{stats}")


if __name__ == "__main__":
    asyncio.run(test_service())
