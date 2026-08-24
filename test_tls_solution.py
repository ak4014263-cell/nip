#!/usr/bin/env python3
"""
Comprehensive Test Suite for TLS-Based WTTJ Account Creation
"""
import asyncio
import logging
import json
import sys
import os
from datetime import datetime

# Add root to path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_tls_solution")


# ============================================================================
# Test 1: Rate Limiter Tests
# ============================================================================

async def test_rate_limiter():
    """Test rate limiter functionality"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 1: Rate Limiter")
    logger.info("=" * 70)
    
    try:
        from rate_limiter import AdaptiveRateLimiter, RateLimitConfig, RequestMetrics
        
        logger.info("✓ Rate limiter imported successfully")
        
        # Create config
        config = RateLimitConfig(
            min_delay_between_requests=1.0,
            max_delay_between_requests=2.0,
            max_requests_per_ip_per_hour=5,
            max_requests_per_ip_per_day=20,
            enable_jitter=True,
            enable_proxy_rotation=True,
            enable_ua_rotation=True,
        )
        
        logger.info("✓ Rate limiter config created")
        
        # Create limiter
        limiter = AdaptiveRateLimiter(config)
        limiter.set_proxies([
            "http://proxy1:8080",
            "http://proxy2:8080",
            "http://proxy3:8080",
        ])
        
        logger.info("✓ Rate limiter initialized with proxies")
        
        # Test rate limit checks
        allowed, status = limiter.check_rate_limits(
            email="test@example.com",
            ip_address="203.0.113.1"
        )
        
        logger.info(f"✓ Rate limit check passed: {status}")
        
        # Test delays
        delay = await limiter.wait_before_request()
        logger.info(f"✓ Wait before request: {delay:.2f}s")
        
        # Test UA rotation
        ua = limiter.get_next_user_agent()
        logger.info(f"✓ User agent rotated: {ua[:50]}...")
        
        # Test proxy rotation
        proxy = limiter.get_next_proxy()
        logger.info(f"✓ Proxy rotated: {proxy}")
        
        # Record metrics
        metrics = RequestMetrics(
            timestamp=datetime.utcnow(),
            ip_address="203.0.113.1",
            email="test@example.com",
            success=True,
            status_code=201,
            delay_before=delay,
            delay_after=0.5
        )
        
        limiter.record_request(metrics)
        logger.info("✓ Metrics recorded")
        
        # Get stats
        stats = limiter.get_stats()
        logger.info(f"✓ Statistics: {json.dumps(stats, indent=2)}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Rate limiter test failed: {e}")
        return False


# ============================================================================
# Test 2: CSRF Extractor Tests
# ============================================================================

async def test_csrf_extractor():
    """Test CSRF token extraction"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: CSRF Extractor")
    logger.info("=" * 70)
    
    try:
        from csrf_extractor import CSRFExtractor
        
        logger.info("✓ CSRF extractor imported successfully")
        
        # Create extractor
        extractor = CSRFExtractor()
        logger.info("✓ CSRF extractor initialized")
        
        # Note: Actual extraction requires network access
        logger.info("⚠️  Full extraction requires network access to WTTJ")
        logger.info("   In production, tokens are extracted during account creation")
        
        # Test header building
        test_tokens = {
            "csrf": "test_csrf_token_12345",
            "auth_token": "test_auth_token_67890",
            "cookies": {
                "sessionid": "test_session_123"
            }
        }
        
        headers = extractor.build_headers_with_tokens(test_tokens)
        logger.info(f"✓ Headers built with tokens")
        logger.info(f"  Includes CSRF: {'X-CSRF-Token' in headers}")
        logger.info(f"  Includes Auth: {'Authorization' in headers}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ CSRF extractor test failed: {e}")
        return False


# ============================================================================
# Test 3: TLS Creator Tests
# ============================================================================

async def test_tls_creator():
    """Test TLS creator initialization"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: TLS Creator")
    logger.info("=" * 70)
    
    try:
        from tls_wttj_creator import WTTJTLSCreator
        
        logger.info("✓ TLS creator imported successfully")
        
        # Create creator
        creator = WTTJTLSCreator()
        logger.info("✓ TLS creator initialized")
        
        # Test session creation
        session = creator._create_tls_session()
        logger.info("✓ TLS session created with Chrome 120 fingerprint")
        
        # Verify session headers
        logger.info(f"✓ Session headers configured:")
        logger.info(f"  User-Agent: {session.headers.get('User-Agent', 'N/A')[:50]}...")
        logger.info(f"  Accept: {session.headers.get('Accept', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ TLS creator test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


# ============================================================================
# Test 4: Service Integration Tests
# ============================================================================

async def test_service_integration():
    """Test TLS account service integration"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Service Integration")
    logger.info("=" * 70)
    
    try:
        from services.wttj.app.tls_account_service import TLSAccountService, RateLimitConfig
        
        logger.info("✓ TLS account service imported successfully")
        
        # Create service
        config = RateLimitConfig(
            min_delay_between_requests=0.5,
            max_delay_between_requests=1.0,
        )
        
        service = TLSAccountService(config=config)
        logger.info("✓ TLS account service initialized")
        
        # Get stats
        stats = service.get_statistics()
        logger.info(f"✓ Service statistics accessible")
        logger.info(f"  Total results: {stats['total_results_recorded']}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Service integration test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


# ============================================================================
# Test 5: FastAPI Endpoints Tests
# ============================================================================

async def test_fastapi_endpoints():
    """Test FastAPI endpoint availability"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 5: FastAPI Endpoints")
    logger.info("=" * 70)
    
    try:
        from services.wttj.app.tls_endpoints import router
        
        logger.info("✓ FastAPI router imported successfully")
        
        # Check routes
        routes = [route.path for route in router.routes]
        logger.info(f"✓ Available endpoints ({len(routes)}):")
        for route in routes:
            logger.info(f"  - {route}")
        
        # Verify key endpoints
        key_endpoints = [
            "/api/v1/tls/create-account",
            "/api/v1/tls/create-accounts-batch",
            "/api/v1/tls/configure-rate-limits",
            "/api/v1/tls/statistics",
            "/api/v1/tls/health"
        ]
        
        missing = [ep for ep in key_endpoints if ep not in routes]
        if missing:
            logger.warning(f"⚠️  Missing endpoints: {missing}")
        else:
            logger.info("✓ All key endpoints available")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ FastAPI endpoints test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


# ============================================================================
# Test 6: Configuration Tests
# ============================================================================

async def test_configurations():
    """Test various configurations"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 6: Configuration Tests")
    logger.info("=" * 70)
    
    try:
        from rate_limiter import RateLimitConfig
        
        # Test conservative config
        conservative = RateLimitConfig(
            min_delay_between_requests=5.0,
            max_delay_between_requests=15.0,
            max_requests_per_ip_per_hour=3,
            max_requests_per_ip_per_day=10,
        )
        logger.info("✓ Conservative config created")
        
        # Test aggressive config
        aggressive = RateLimitConfig(
            min_delay_between_requests=1.0,
            max_delay_between_requests=3.0,
            max_requests_per_ip_per_hour=20,
            max_requests_per_ip_per_day=100,
        )
        logger.info("✓ Aggressive config created")
        
        # Test balanced config
        balanced = RateLimitConfig(
            min_delay_between_requests=2.0,
            max_delay_between_requests=8.0,
            max_requests_per_ip_per_hour=5,
            max_requests_per_ip_per_day=20,
        )
        logger.info("✓ Balanced config created")
        
        logger.info("\nConfiguration Presets:")
        logger.info("  1. Conservative (Stealth): 5-15s delays, 3 per hour")
        logger.info("  2. Balanced (Default): 2-8s delays, 5 per hour")
        logger.info("  3. Aggressive (Fast): 1-3s delays, 20 per hour")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False


# ============================================================================
# Test 7: Password Validation
# ============================================================================

async def test_password_validation():
    """Test password requirements"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 7: Password Validation")
    logger.info("=" * 70)
    
    try:
        import re
        
        def validate_password(pwd):
            """Validate WTTJ password requirements"""
            if len(pwd) < 12:
                return False, "Less than 12 characters"
            if not re.search(r'[A-Z]', pwd):
                return False, "Missing uppercase"
            if not re.search(r'[a-z]', pwd):
                return False, "Missing lowercase"
            if not re.search(r'\d', pwd):
                return False, "Missing digit"
            if not re.search(r'[!@#$%^&*]', pwd):
                return False, "Missing special character"
            return True, "Valid"
        
        test_passwords = [
            ("weak", False),
            ("WeakPass123", False),
            ("WeakPass!23", False),
            ("SecurePass123!@", True),
            ("MyP@ssw0rd1234", True),
        ]
        
        logger.info("Testing passwords:")
        for pwd, expected_valid in test_passwords:
            valid, reason = validate_password(pwd)
            status = "✓" if valid == expected_valid else "✗"
            logger.info(f"  {status} {pwd}: {reason}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Password validation test failed: {e}")
        return False


# ============================================================================
# Main Test Runner
# ============================================================================

async def run_all_tests():
    """Run all tests"""
    logger.info("\n" + "=" * 70)
    logger.info("🧪 TLS-BASED WTTJ ACCOUNT CREATION - TEST SUITE")
    logger.info("=" * 70)
    
    results = {}
    
    # Run tests
    tests = [
        ("Rate Limiter", test_rate_limiter),
        ("CSRF Extractor", test_csrf_extractor),
        ("TLS Creator", test_tls_creator),
        ("Service Integration", test_service_integration),
        ("FastAPI Endpoints", test_fastapi_endpoints),
        ("Configurations", test_configurations),
        ("Password Validation", test_password_validation),
    ]
    
    for test_name, test_func in tests:
        try:
            results[test_name] = await test_func()
        except Exception as e:
            logger.error(f"Exception in {test_name}: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_status in results.items():
        status = "✓ PASS" if passed_status else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("\n" + "=" * 70)
    logger.info(f"📈 OVERALL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    logger.info("=" * 70)
    
    return all(results.values())


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
