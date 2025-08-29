#!/usr/bin/env python3
"""
Migration Validation Script
Validates that the migration from API key to Redis session authentication is working correctly.
"""

import sys
import os
import json
import logging
import time

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from services.fortigate_service import fgt_api, get_interfaces
from services.redis_session_manager import get_redis_session_manager
from services.fortigate_redis_session import get_fortigate_redis_session_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_redis_connectivity():
    """Check if Redis is available and responding"""
    logger.info("Checking Redis connectivity...")
    
    try:
        redis_manager = get_redis_session_manager()
        health = redis_manager.health_check()
        
        if health.get("redis_connected"):
            logger.info("✅ Redis is connected and responding")
            logger.info(f"   Redis version: {health.get('redis_version', 'Unknown')}")
            logger.info(f"   Memory usage: {health.get('redis_memory', 'Unknown')}")
            return True
        else:
            logger.error("❌ Redis connection failed")
            logger.error(f"   Error: {health.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Redis connectivity check failed: {e}")
        return False


def check_fortigate_credentials():
    """Check if FortiGate credentials are properly configured"""
    logger.info("Checking FortiGate credentials...")
    
    try:
        session_manager = get_fortigate_redis_session_manager()
        health = session_manager.health_check()
        
        if (health.get("fortigate_ip") and 
            health.get("username") and 
            health.get("has_password")):
            logger.info("✅ FortiGate credentials are configured")
            logger.info(f"   FortiGate IP: {health.get('fortigate_ip')}")
            logger.info(f"   Username: {health.get('username')}")
            return True
        else:
            logger.error("❌ FortiGate credentials incomplete")
            logger.error(f"   IP: {health.get('fortigate_ip', 'Missing')}")
            logger.error(f"   Username: {health.get('username', 'Missing')}")
            logger.error(f"   Password: {'Present' if health.get('has_password') else 'Missing'}")
            return False
            
    except Exception as e:
        logger.error(f"❌ FortiGate credentials check failed: {e}")
        return False


def test_session_authentication():
    """Test session-based authentication"""
    logger.info("Testing session-based authentication...")
    
    try:
        # Force session mode (disable token fallback)
        original_fallback = os.environ.get("FORTIGATE_ALLOW_TOKEN_FALLBACK")
        os.environ["FORTIGATE_ALLOW_TOKEN_FALLBACK"] = "false"
        
        # Make API call which should use Redis session authentication
        result = fgt_api("cmdb/system/interface")
        
        # Restore original setting
        if original_fallback is not None:
            os.environ["FORTIGATE_ALLOW_TOKEN_FALLBACK"] = original_fallback
        else:
            os.environ.pop("FORTIGATE_ALLOW_TOKEN_FALLBACK", None)
        
        if "error" in result:
            error_type = result.get("error")
            if error_type == "authentication_failed":
                logger.error("❌ Session authentication failed")
                logger.error("   Check FortiGate username/password and network connectivity")
                return False
            elif error_type == "connection_error":
                logger.error("❌ Connection error")
                logger.error("   Check FortiGate IP address and network connectivity")
                return False
            else:
                logger.error(f"❌ API call failed: {error_type}")
                logger.error(f"   Details: {result.get('message', 'No details')}")
                return False
        else:
            logger.info("✅ Session authentication working")
            logger.info(f"   Retrieved {len(result.get('results', []))} interfaces")
            return True
            
    except Exception as e:
        logger.error(f"❌ Session authentication test failed: {e}")
        return False


def test_session_caching():
    """Test that sessions are being cached in Redis"""
    logger.info("Testing session caching in Redis...")
    
    try:
        redis_manager = get_redis_session_manager()
        
        # Get initial session info
        initial_info = redis_manager.get_session_info()
        initial_sessions = initial_info.get("total_sessions", 0)
        
        # Make API call which should create/use a session
        result = fgt_api("cmdb/system/interface")
        
        # Wait a moment for session to be stored
        time.sleep(1)
        
        # Get updated session info
        updated_info = redis_manager.get_session_info()
        updated_sessions = updated_info.get("total_sessions", 0)
        active_sessions = updated_info.get("active_sessions", 0)
        
        if active_sessions > 0:
            logger.info("✅ Session caching is working")
            logger.info(f"   Total sessions in Redis: {updated_sessions}")
            logger.info(f"   Active sessions: {active_sessions}")
            return True
        else:
            logger.warning("⚠️  No active sessions found in Redis")
            logger.warning("   Session may not be persisting (check Redis configuration)")
            return False
            
    except Exception as e:
        logger.error(f"❌ Session caching test failed: {e}")
        return False


def test_api_endpoints():
    """Test that API endpoints are working with Redis sessions"""
    logger.info("Testing API endpoints with Redis session authentication...")
    
    test_endpoints = [
        "cmdb/system/interface",
        "monitor/system/status"
    ]
    
    success_count = 0
    
    for endpoint in test_endpoints:
        try:
            logger.info(f"   Testing endpoint: {endpoint}")
            result = fgt_api(endpoint)
            
            if "error" not in result:
                success_count += 1
                logger.info(f"   ✅ {endpoint} - Success")
            else:
                logger.error(f"   ❌ {endpoint} - Error: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"   ❌ {endpoint} - Exception: {e}")
    
    if success_count == len(test_endpoints):
        logger.info("✅ All API endpoints working with Redis sessions")
        return True
    else:
        logger.error(f"❌ Only {success_count}/{len(test_endpoints)} endpoints successful")
        return False


def main():
    """Main validation function"""
    logger.info("=" * 60)
    logger.info("FORTIGATE REDIS SESSION MIGRATION VALIDATION")
    logger.info("=" * 60)
    
    checks = [
        ("Redis Connectivity", check_redis_connectivity),
        ("FortiGate Credentials", check_fortigate_credentials),
        ("Session Authentication", test_session_authentication),
        ("Session Caching", test_session_caching),
        ("API Endpoints", test_api_endpoints)
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        logger.info(f"\n{check_name}:")
        logger.info("-" * 40)
        
        try:
            result = check_func()
            results[check_name] = result
        except Exception as e:
            logger.error(f"❌ {check_name} failed with exception: {e}")
            results[check_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    
    total_checks = len(results)
    passed_checks = sum(1 for result in results.values() if result)
    failed_checks = total_checks - passed_checks
    
    logger.info(f"Total Checks: {total_checks}")
    logger.info(f"Passed: {passed_checks}")
    logger.info(f"Failed: {failed_checks}")
    logger.info(f"Success Rate: {(passed_checks/total_checks)*100:.1f}%")
    
    if failed_checks == 0:
        logger.info("\n🎉 MIGRATION VALIDATION SUCCESSFUL!")
        logger.info("Your FortiGate dashboard is now using Redis session authentication.")
    else:
        logger.error("\n⚠️  MIGRATION VALIDATION INCOMPLETE")
        logger.error("Some checks failed. Please review the errors above.")
        
        logger.info("\nFailed checks:")
        for check_name, result in results.items():
            if not result:
                logger.error(f"  ❌ {check_name}")
    
    return failed_checks == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)