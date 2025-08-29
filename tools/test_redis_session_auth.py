#!/usr/bin/env python3
"""
Redis Session Authentication Testing Script
Tests the new Redis-based session management system for FortiGate authentication.
"""

import sys
import os
import json
import time
import logging
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from services.redis_session_manager import get_redis_session_manager, cleanup_expired_sessions
from services.fortigate_redis_session import get_fortigate_redis_session_manager
from services.fortigate_service import fgt_api, get_interfaces

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RedisSessionTestSuite:
    """Comprehensive test suite for Redis session authentication"""
    
    def __init__(self):
        self.redis_manager = get_redis_session_manager()
        self.session_manager = get_fortigate_redis_session_manager()
        self.test_results = {}
        
    def run_all_tests(self):
        """Run all authentication tests"""
        logger.info("Starting Redis Session Authentication Test Suite")
        logger.info("=" * 60)
        
        test_methods = [
            self.test_redis_connection,
            self.test_redis_session_storage,
            self.test_fortigate_session_manager,
            self.test_session_expiration,
            self.test_session_cleanup,
            self.test_api_integration,
            self.test_concurrent_sessions,
            self.test_health_checks
        ]
        
        for test_method in test_methods:
            try:
                logger.info(f"\nRunning: {test_method.__name__}")
                result = test_method()
                self.test_results[test_method.__name__] = result
                status = "PASS" if result.get("success", False) else "FAIL"
                logger.info(f"Result: {status} - {result.get('message', '')}")
            except Exception as e:
                logger.error(f"Test {test_method.__name__} failed with exception: {e}")
                self.test_results[test_method.__name__] = {
                    "success": False,
                    "message": f"Exception: {str(e)}"
                }
        
        self.print_summary()

    def test_redis_connection(self):
        """Test Redis connectivity"""
        try:
            health = self.redis_manager.health_check()
            
            if health.get("redis_connected"):
                return {
                    "success": True,
                    "message": f"Redis connected at {health['redis_host']}:{health['redis_port']}",
                    "details": health
                }
            else:
                return {
                    "success": False,
                    "message": "Redis connection failed",
                    "details": health
                }
        except Exception as e:
            return {"success": False, "message": f"Redis connection test failed: {str(e)}"}

    def test_redis_session_storage(self):
        """Test Redis session storage and retrieval"""
        try:
            # Test session storage
            test_ip = "192.168.1.100"
            test_user = "testuser"
            test_session_key = "test_session_key_12345"
            
            # Store session
            store_result = self.redis_manager.store_session(
                test_ip, test_user, test_session_key, expires_in_minutes=5
            )
            
            if not store_result:
                return {"success": False, "message": "Failed to store test session"}
            
            # Retrieve session
            session_data = self.redis_manager.get_session(test_ip, test_user)
            
            if not session_data:
                return {"success": False, "message": "Failed to retrieve stored session"}
            
            # Validate session data
            if (session_data.session_key == test_session_key and
                session_data.fortigate_ip == test_ip and
                session_data.username == test_user and
                session_data.is_valid()):
                
                # Clean up test session
                self.redis_manager.delete_session(test_ip, test_user)
                
                return {
                    "success": True,
                    "message": "Session storage and retrieval working correctly",
                    "details": {
                        "stored_key": test_session_key,
                        "retrieved_key": session_data.session_key,
                        "is_valid": session_data.is_valid()
                    }
                }
            else:
                return {"success": False, "message": "Session data validation failed"}
                
        except Exception as e:
            return {"success": False, "message": f"Session storage test failed: {str(e)}"}

    def test_fortigate_session_manager(self):
        """Test FortiGate session manager integration"""
        try:
            # Test session manager health check
            health = self.session_manager.health_check()
            
            # Test credential loading
            has_credentials = (
                health.get("fortigate_ip") and 
                health.get("username") and 
                health.get("has_password")
            )
            
            if not has_credentials:
                return {
                    "success": False,
                    "message": "FortiGate credentials not properly loaded",
                    "details": health
                }
            
            # Test session info retrieval
            session_info = self.session_manager.get_session_info()
            
            return {
                "success": True,
                "message": "FortiGate session manager initialized correctly",
                "details": {
                    "health": health,
                    "session_info": session_info
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"FortiGate session manager test failed: {str(e)}"}

    def test_session_expiration(self):
        """Test session expiration handling"""
        try:
            test_ip = "192.168.1.101"
            test_user = "expiry_test"
            test_session_key = "expiry_test_session_12345"
            
            # Store session with very short expiration (1 minute)
            store_result = self.redis_manager.store_session(
                test_ip, test_user, test_session_key, expires_in_minutes=1
            )
            
            if not store_result:
                return {"success": False, "message": "Failed to store test session for expiration"}
            
            # Retrieve fresh session
            session_data = self.redis_manager.get_session(test_ip, test_user)
            
            if not session_data or not session_data.is_valid():
                return {"success": False, "message": "Fresh session should be valid"}
            
            # Manually expire the session by modifying the expiration time
            session_data.expires_at = datetime.now() - timedelta(minutes=1)
            
            # Check if expired session is detected
            if session_data.is_expired(buffer_minutes=0):
                # Clean up
                self.redis_manager.delete_session(test_ip, test_user)
                
                return {
                    "success": True,
                    "message": "Session expiration detection working correctly"
                }
            else:
                return {"success": False, "message": "Session expiration detection failed"}
                
        except Exception as e:
            return {"success": False, "message": f"Session expiration test failed: {str(e)}"}

    def test_session_cleanup(self):
        """Test automatic session cleanup"""
        try:
            # Create a few test sessions
            test_sessions = [
                ("192.168.1.200", "cleanup_test_1"),
                ("192.168.1.201", "cleanup_test_2"),
                ("192.168.1.202", "cleanup_test_3")
            ]
            
            # Store sessions
            for ip, user in test_sessions:
                self.redis_manager.store_session(ip, user, f"session_{user}", expires_in_minutes=5)
            
            # Get initial session count
            initial_info = self.redis_manager.get_session_info()
            initial_count = initial_info.get("total_sessions", 0)
            
            # Run cleanup (should not remove valid sessions)
            cleaned_count = self.redis_manager.cleanup_expired_sessions()
            
            # Clean up our test sessions
            for ip, user in test_sessions:
                self.redis_manager.delete_session(ip, user)
            
            return {
                "success": True,
                "message": f"Session cleanup completed. Cleaned {cleaned_count} expired sessions",
                "details": {
                    "initial_sessions": initial_count,
                    "cleaned_sessions": cleaned_count
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Session cleanup test failed: {str(e)}"}

    def test_api_integration(self):
        """Test API integration with Redis sessions"""
        try:
            # Test making an API call with session authentication
            logger.info("Testing API call with Redis session authentication...")
            
            # This will use the Redis session manager
            result = fgt_api("cmdb/system/interface")
            
            if "error" in result:
                error_type = result.get("error")
                if error_type == "authentication_failed":
                    return {
                        "success": False,
                        "message": "Authentication failed - check FortiGate credentials",
                        "details": result
                    }
                elif error_type == "connection_error":
                    return {
                        "success": False,
                        "message": "Connection error - check FortiGate IP and network connectivity",
                        "details": result
                    }
                else:
                    return {
                        "success": False,
                        "message": f"API call failed: {error_type}",
                        "details": result
                    }
            else:
                return {
                    "success": True,
                    "message": "API integration working with Redis sessions",
                    "details": {
                        "endpoint": "cmdb/system/interface",
                        "response_keys": list(result.keys()) if isinstance(result, dict) else "non-dict response"
                    }
                }
                
        except Exception as e:
            return {"success": False, "message": f"API integration test failed: {str(e)}"}

    def test_concurrent_sessions(self):
        """Test concurrent session handling"""
        try:
            import threading
            import time
            
            results = []
            
            def create_session(ip_suffix):
                try:
                    test_ip = f"192.168.1.{ip_suffix}"
                    test_user = f"concurrent_test_{ip_suffix}"
                    test_session_key = f"concurrent_session_{ip_suffix}"
                    
                    # Store session
                    store_result = self.redis_manager.store_session(
                        test_ip, test_user, test_session_key, expires_in_minutes=10
                    )
                    
                    # Retrieve session
                    session_data = self.redis_manager.get_session(test_ip, test_user)
                    
                    # Clean up
                    self.redis_manager.delete_session(test_ip, test_user)
                    
                    results.append({
                        "thread_id": ip_suffix,
                        "store_success": store_result,
                        "retrieve_success": session_data is not None and session_data.is_valid()
                    })
                except Exception as e:
                    results.append({
                        "thread_id": ip_suffix,
                        "error": str(e)
                    })
            
            # Create multiple threads
            threads = []
            for i in range(5):
                thread = threading.Thread(target=create_session, args=(300 + i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=10)
            
            # Analyze results
            successful_threads = sum(1 for r in results if r.get("store_success") and r.get("retrieve_success"))
            total_threads = len(results)
            
            return {
                "success": successful_threads == total_threads,
                "message": f"Concurrent sessions: {successful_threads}/{total_threads} successful",
                "details": results
            }
            
        except Exception as e:
            return {"success": False, "message": f"Concurrent sessions test failed: {str(e)}"}

    def test_health_checks(self):
        """Test health check endpoints"""
        try:
            # Redis session manager health check
            redis_health = self.redis_manager.health_check()
            
            # FortiGate session manager health check
            session_health = self.session_manager.health_check()
            
            # Session info
            session_info = self.redis_manager.get_session_info()
            
            redis_healthy = redis_health.get("redis_connected", False)
            session_manager_healthy = (
                session_health.get("fortigate_ip") and 
                session_health.get("username")
            )
            
            return {
                "success": redis_healthy and session_manager_healthy,
                "message": f"Health checks: Redis={'OK' if redis_healthy else 'FAIL'}, Session={'OK' if session_manager_healthy else 'FAIL'}",
                "details": {
                    "redis_health": redis_health,
                    "session_health": session_health,
                    "session_info": session_info
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Health checks test failed: {str(e)}"}

    def print_summary(self):
        """Print test results summary"""
        logger.info("\n" + "=" * 60)
        logger.info("REDIS SESSION AUTHENTICATION TEST SUMMARY")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get("success"))
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            logger.info("\nFAILED TESTS:")
            for test_name, result in self.test_results.items():
                if not result.get("success"):
                    logger.info(f"  ❌ {test_name}: {result.get('message')}")
        
        logger.info("\nPASSED TESTS:")
        for test_name, result in self.test_results.items():
            if result.get("success"):
                logger.info(f"  ✅ {test_name}: {result.get('message')}")
        
        # Export detailed results to JSON
        results_file = "redis_session_test_results.json"
        try:
            with open(results_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "summary": {
                        "total_tests": total_tests,
                        "passed_tests": passed_tests,
                        "failed_tests": failed_tests,
                        "success_rate": (passed_tests/total_tests)*100
                    },
                    "results": self.test_results
                }, f, indent=2, default=str)
            logger.info(f"\nDetailed results exported to: {results_file}")
        except Exception as e:
            logger.error(f"Failed to export results: {e}")


def main():
    """Main test execution"""
    print("FortiGate Redis Session Authentication Test Suite")
    print("=" * 60)
    
    # Environment check
    required_env_vars = [
        "FORTIGATE_HOST",
        "FORTIGATE_USERNAME", 
        "FORTIGATE_PASSWORD_FILE"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please set these in your environment or .env file")
        sys.exit(1)
    
    # Check if password file exists
    password_file = os.getenv("FORTIGATE_PASSWORD_FILE")
    if password_file and not os.path.exists(password_file):
        print(f"❌ Password file not found: {password_file}")
        sys.exit(1)
    
    print("✅ Environment variables configured")
    print()
    
    # Run tests
    test_suite = RedisSessionTestSuite()
    test_suite.run_all_tests()


if __name__ == "__main__":
    main()