#!/usr/bin/env python3
"""
Intelligent Rate Limiter for WTTJ Account Creation
Prevents detection by simulating human behavior patterns
"""
import asyncio
import time
import random
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    # Time-based limits
    min_delay_between_requests: float = 2.0  # Minimum seconds between requests
    max_delay_between_requests: float = 8.0  # Maximum seconds between requests
    
    # Per-IP limits
    max_requests_per_ip_per_hour: int = 5    # Max accounts from single IP per hour
    max_requests_per_ip_per_day: int = 20    # Max accounts from single IP per day
    
    # Per-email limits
    max_requests_per_email_per_day: int = 1  # Only create account once per email
    
    # Burst protection
    max_burst_requests: int = 2               # Max consecutive requests without delay
    burst_reset_time: float = 60.0            # Reset burst counter after N seconds
    
    # Proxy rotation
    enable_proxy_rotation: bool = True
    proxy_change_interval: int = 3            # Change proxy every N requests
    
    # User-agent rotation
    enable_ua_rotation: bool = True
    ua_change_interval: int = 2               # Change UA every N requests
    
    # Jitter for human-like behavior
    enable_jitter: bool = True
    jitter_percentage: float = 0.2            # Add 0% to 20% random jitter


@dataclass
class RequestMetrics:
    """Metrics for a single request"""
    timestamp: datetime
    ip_address: Optional[str] = None
    email: Optional[str] = None
    success: bool = False
    status_code: int = 0
    error_message: Optional[str] = None
    delay_before: float = 0.0
    delay_after: float = 0.0


class AdaptiveRateLimiter:
    """Intelligent rate limiter that adapts to avoid detection"""
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self.request_history: List[RequestMetrics] = []
        self.ip_request_times: Dict[str, List[datetime]] = defaultdict(list)
        self.email_request_times: Dict[str, List[datetime]] = defaultdict(list)
        self.burst_counter = 0
        self.last_burst_reset = time.time()
        self.proxy_index = 0
        self.ua_index = 0
        self.request_count = 0
        
        # User agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        ]
        
        self.proxies = []  # Will be set externally
        
        logger.info("✅ Adaptive Rate Limiter initialized")
    
    def set_proxies(self, proxies: List[str]):
        """Set proxy list for rotation"""
        self.proxies = proxies
        logger.info(f"🔗 Loaded {len(proxies)} proxies for rotation")
    
    def _get_current_time(self) -> datetime:
        """Get current time"""
        return datetime.utcnow()
    
    def _check_ip_hourly_limit(self, ip_address: Optional[str]) -> Tuple[bool, str]:
        """Check if IP has exceeded hourly limit"""
        if not ip_address:
            return True, "No IP to check"
        
        now = self._get_current_time()
        one_hour_ago = now - timedelta(hours=1)
        
        # Clean old entries
        self.ip_request_times[ip_address] = [
            t for t in self.ip_request_times[ip_address] if t > one_hour_ago
        ]
        
        count = len(self.ip_request_times[ip_address])
        
        if count >= self.config.max_requests_per_ip_per_hour:
            return False, f"IP hourly limit reached ({count}/{self.config.max_requests_per_ip_per_hour})"
        
        return True, f"IP hourly: {count}/{self.config.max_requests_per_ip_per_hour}"
    
    def _check_ip_daily_limit(self, ip_address: Optional[str]) -> Tuple[bool, str]:
        """Check if IP has exceeded daily limit"""
        if not ip_address:
            return True, "No IP to check"
        
        now = self._get_current_time()
        one_day_ago = now - timedelta(days=1)
        
        # Clean old entries
        self.ip_request_times[ip_address] = [
            t for t in self.ip_request_times[ip_address] if t > one_day_ago
        ]
        
        count = len(self.ip_request_times[ip_address])
        
        if count >= self.config.max_requests_per_ip_per_day:
            return False, f"IP daily limit reached ({count}/{self.config.max_requests_per_ip_per_day})"
        
        return True, f"IP daily: {count}/{self.config.max_requests_per_ip_per_day}"
    
    def _check_email_daily_limit(self, email: Optional[str]) -> Tuple[bool, str]:
        """Check if email has exceeded daily limit"""
        if not email:
            return True, "No email to check"
        
        now = self._get_current_time()
        one_day_ago = now - timedelta(days=1)
        
        # Clean old entries
        self.email_request_times[email] = [
            t for t in self.email_request_times[email] if t > one_day_ago
        ]
        
        count = len(self.email_request_times[email])
        
        if count >= self.config.max_requests_per_email_per_day:
            return False, f"Email daily limit reached ({count}/{self.config.max_requests_per_email_per_day})"
        
        return True, f"Email daily: {count}/{self.config.max_requests_per_email_per_day}"
    
    def check_rate_limits(self, email: Optional[str], ip_address: Optional[str]) -> Tuple[bool, Dict[str, str]]:
        """
        Check all rate limits
        
        Returns:
            (allowed: bool, status_dict: Dict[str, str])
        """
        status = {}
        
        # Check IP hourly limit
        ip_hourly_ok, ip_hourly_msg = self._check_ip_hourly_limit(ip_address)
        status["ip_hourly"] = ip_hourly_msg
        
        # Check IP daily limit
        ip_daily_ok, ip_daily_msg = self._check_ip_daily_limit(ip_address)
        status["ip_daily"] = ip_daily_msg
        
        # Check email daily limit
        email_daily_ok, email_daily_msg = self._check_email_daily_limit(email)
        status["email_daily"] = email_daily_msg
        
        allowed = ip_hourly_ok and ip_daily_ok and email_daily_ok
        
        return allowed, status
    
    async def wait_before_request(self) -> float:
        """
        Wait appropriate time before next request
        Simulates human behavior with jitter and burst protection
        
        Returns:
            float: Actual delay applied (seconds)
        """
        # Check burst limit
        now = time.time()
        time_since_burst_reset = now - self.last_burst_reset
        
        if time_since_burst_reset > self.config.burst_reset_time:
            self.burst_counter = 0
            self.last_burst_reset = now
        
        # Base delay
        base_delay = random.uniform(
            self.config.min_delay_between_requests,
            self.config.max_delay_between_requests
        )
        
        # Add jitter for human-like behavior
        if self.config.enable_jitter:
            jitter = base_delay * random.uniform(0, self.config.jitter_percentage)
            base_delay += jitter
        
        # Increase delay if burst is active
        if self.burst_counter >= self.config.max_burst_requests:
            burst_penalty = random.uniform(5, 15)  # Add 5-15 seconds penalty
            base_delay += burst_penalty
            logger.info(f"⚠️  Burst limit active. Adding {burst_penalty:.1f}s penalty")
            self.burst_counter = 0
            self.last_burst_reset = time.time()
        
        self.burst_counter += 1
        
        logger.info(f"⏱️  Waiting {base_delay:.2f}s before next request (burst: {self.burst_counter})")
        await asyncio.sleep(base_delay)
        
        return base_delay
    
    async def wait_after_request(self, success: bool) -> float:
        """
        Wait appropriate time after request based on success/failure
        
        Args:
            success: Whether request was successful
        
        Returns:
            float: Actual delay applied (seconds)
        """
        if success:
            # Shorter delay after success
            delay = random.uniform(0.5, 2.0)
        else:
            # Longer delay after failure to avoid rate limiting
            delay = random.uniform(3.0, 10.0)
        
        logger.info(f"⏳ Waiting {delay:.2f}s after request ({'✓' if success else '✗'})")
        await asyncio.sleep(delay)
        
        return delay
    
    def get_next_user_agent(self) -> str:
        """Get next user agent for rotation"""
        if not self.config.enable_ua_rotation or not self.user_agents:
            return self.user_agents[0] if self.user_agents else ""
        
        if self.request_count % self.config.ua_change_interval == 0:
            self.ua_index = (self.ua_index + 1) % len(self.user_agents)
        
        ua = self.user_agents[self.ua_index]
        logger.info(f"🔄 Using User-Agent #{self.ua_index + 1}")
        return ua
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy for rotation"""
        if not self.config.enable_proxy_rotation or not self.proxies:
            return None
        
        if self.request_count % self.config.proxy_change_interval == 0:
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        
        proxy = self.proxies[self.proxy_index]
        logger.info(f"🔗 Using Proxy #{self.proxy_index + 1}/{len(self.proxies)}")
        return proxy
    
    def record_request(self, metrics: RequestMetrics):
        """Record request metrics"""
        self.request_history.append(metrics)
        self.request_count += 1
        
        if metrics.ip_address:
            self.ip_request_times[metrics.ip_address].append(metrics.timestamp)
        
        if metrics.email:
            self.email_request_times[metrics.email].append(metrics.timestamp)
        
        status = "✓" if metrics.success else "✗"
        logger.info(f"{status} Request #{self.request_count}: {metrics.email} - Status: {metrics.status_code}")
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        successful = sum(1 for m in self.request_history if m.success)
        failed = len(self.request_history) - successful
        
        total_delay = sum(m.delay_before + m.delay_after for m in self.request_history)
        
        return {
            "total_requests": len(self.request_history),
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful/len(self.request_history)*100):.1f}%" if self.request_history else "N/A",
            "total_delay_seconds": f"{total_delay:.1f}",
            "avg_delay_per_request": f"{(total_delay/len(self.request_history)):.2f}s" if self.request_history else "N/A",
            "unique_ips": len(self.ip_request_times),
            "unique_emails": len(self.email_request_times),
        }
    
    def export_report(self, filename: str = "rate_limiter_report.json"):
        """Export rate limiter report"""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "config": {
                "min_delay": self.config.min_delay_between_requests,
                "max_delay": self.config.max_delay_between_requests,
                "max_requests_per_ip_per_hour": self.config.max_requests_per_ip_per_hour,
                "max_requests_per_ip_per_day": self.config.max_requests_per_ip_per_day,
                "max_requests_per_email_per_day": self.config.max_requests_per_email_per_day,
            },
            "statistics": self.get_stats(),
            "history": [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "email": m.email,
                    "ip": m.ip_address,
                    "success": m.success,
                    "status_code": m.status_code,
                    "error": m.error_message,
                    "delay_before": f"{m.delay_before:.2f}s",
                    "delay_after": f"{m.delay_after:.2f}s",
                }
                for m in self.request_history
            ]
        }
        
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Report exported to {filename}")
        return report


class BurstProtection:
    """Protects against burst detection patterns"""
    
    def __init__(self, max_burst_size: int = 3, reset_after: float = 60.0):
        self.max_burst_size = max_burst_size
        self.reset_after = reset_after
        self.request_times: List[float] = []
    
    def is_safe_to_request(self) -> bool:
        """Check if safe to make request without triggering burst detection"""
        now = time.time()
        
        # Clean old entries
        self.request_times = [t for t in self.request_times if now - t < self.reset_after]
        
        # Check if we're in a burst
        if len(self.request_times) >= self.max_burst_size:
            time_since_first = now - self.request_times[0]
            if time_since_first < self.reset_after:
                return False
        
        self.request_times.append(now)
        return True
    
    def get_wait_time(self) -> float:
        """Get time to wait before next safe request"""
        if not self.request_times:
            return 0.0
        
        now = time.time()
        oldest = self.request_times[0]
        time_since_first = now - oldest
        
        if len(self.request_times) >= self.max_burst_size and time_since_first < self.reset_after:
            return self.reset_after - time_since_first
        
        return 0.0


# Test function
if __name__ == "__main__":
    async def test_rate_limiter():
        config = RateLimitConfig(
            min_delay_between_requests=1.0,
            max_delay_between_requests=3.0,
            enable_jitter=True,
            enable_ua_rotation=True,
            enable_proxy_rotation=True,
        )
        
        limiter = AdaptiveRateLimiter(config)
        limiter.set_proxies([
            "http://proxy1:8080",
            "http://proxy2:8080",
            "http://proxy3:8080",
        ])
        
        # Simulate requests
        for i in range(5):
            logger.info(f"\n📍 Request #{i+1}")
            
            # Check rate limits
            allowed, status = limiter.check_rate_limits(
                email=f"test{i}@example.com",
                ip_address="203.0.113.1"
            )
            
            if not allowed:
                logger.warning(f"❌ Rate limit exceeded: {status}")
                break
            
            logger.info(f"✓ Rate limits OK: {status}")
            
            # Wait before request
            delay = await limiter.wait_before_request()
            
            # Get proxy and UA
            proxy = limiter.get_next_proxy()
            ua = limiter.get_next_user_agent()
            
            # Simulate request
            metrics = RequestMetrics(
                timestamp=datetime.utcnow(),
                ip_address="203.0.113.1",
                email=f"test{i}@example.com",
                success=True,
                status_code=201,
                delay_before=delay,
                delay_after=0.5
            )
            
            limiter.record_request(metrics)
        
        # Print stats
        logger.info(f"\n📊 Statistics:\n{json.dumps(limiter.get_stats(), indent=2)}")
    
    asyncio.run(test_rate_limiter())
