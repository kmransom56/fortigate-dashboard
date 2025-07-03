#!/usr/bin/env python3
"""
Performance Testing Script for FortiSwitch Monitor
Compares original vs optimized implementation performance
"""

import asyncio
import time
import statistics
import sys
import os
import logging
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
import json

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Test configuration
TEST_ITERATIONS = 5
CONCURRENT_USERS = [1, 5, 10, 20]
API_TIMEOUT = 30


class PerformanceTestSuite:
    """Comprehensive performance testing suite."""
    
    def __init__(self):
        self.results = {
            "original": {},
            "optimized": {},
            "comparison": {}
        }
    
    async def test_original_fortiswitch_service(self) -> Dict[str, Any]:
        """Test the original FortiSwitch service performance."""
        try:
            from app.services.fortiswitch_service import get_fortiswitches
            
            logger.info("Testing original FortiSwitch service...")
            
            times = []
            for i in range(TEST_ITERATIONS):
                start_time = time.time()
                
                # Run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    result = await loop.run_in_executor(executor, get_fortiswitches)
                
                elapsed = time.time() - start_time
                times.append(elapsed)
                
                logger.info(f"Original iteration {i+1}: {elapsed:.2f}s")
                
                # Small delay to avoid overwhelming the API
                await asyncio.sleep(2)
            
            return {
                "avg_time": statistics.mean(times),
                "min_time": min(times),
                "max_time": max(times),
                "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
                "total_requests": TEST_ITERATIONS,
                "success_rate": 100.0
            }
            
        except Exception as e:
            logger.error(f"Error testing original service: {e}")
            return {
                "avg_time": float('inf'),
                "min_time": float('inf'),
                "max_time": float('inf'),
                "std_dev": 0,
                "total_requests": 0,
                "success_rate": 0.0,
                "error": str(e)
            }
    
    async def test_optimized_fortiswitch_service(self) -> Dict[str, Any]:
        """Test the optimized FortiSwitch service performance."""
        try:
            from app.services.fortiswitch_service_optimized import get_fortiswitches_optimized
            
            logger.info("Testing optimized FortiSwitch service...")
            
            times = []
            for i in range(TEST_ITERATIONS):
                start_time = time.time()
                
                result = await get_fortiswitches_optimized()
                
                elapsed = time.time() - start_time
                times.append(elapsed)
                
                logger.info(f"Optimized iteration {i+1}: {elapsed:.2f}s")
                
                # Small delay to avoid overwhelming the API
                await asyncio.sleep(2)
            
            return {
                "avg_time": statistics.mean(times),
                "min_time": min(times),
                "max_time": max(times),
                "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
                "total_requests": TEST_ITERATIONS,
                "success_rate": 100.0
            }
            
        except Exception as e:
            logger.error(f"Error testing optimized service: {e}")
            return {
                "avg_time": float('inf'),
                "min_time": float('inf'),
                "max_time": float('inf'),
                "std_dev": 0,
                "total_requests": 0,
                "success_rate": 0.0,
                "error": str(e)
            }
    
    async def test_mac_normalization_performance(self) -> Dict[str, Any]:
        """Test MAC address normalization performance."""
        try:
            from app.services.fortiswitch_service import normalize_mac
            from app.services.fortiswitch_service_optimized import normalize_mac_optimized
            
            # Test data - various MAC address formats
            test_macs = [
                "00:11:22:33:44:55",
                "00-11-22-33-44-55", 
                "0011.2233.4455",
                "001122334455",
                "00:11:22:33:44:55",
                "AA:BB:CC:DD:EE:FF",
                "aa:bb:cc:dd:ee:ff",
                "invalid-mac",
                "",
                None
            ] * 1000  # Test with 10,000 MAC addresses
            
            logger.info("Testing MAC normalization performance...")
            
            # Test original implementation
            start_time = time.time()
            for mac in test_macs:
                if mac:
                    normalize_mac(mac)
            original_time = time.time() - start_time
            
            # Test optimized implementation
            start_time = time.time()
            for mac in test_macs:
                if mac:
                    normalize_mac_optimized(mac)
            optimized_time = time.time() - start_time
            
            improvement = ((original_time - optimized_time) / original_time) * 100
            
            return {
                "original": {
                    "total_time": original_time,
                    "per_mac": original_time / len([m for m in test_macs if m])
                },
                "optimized": {
                    "total_time": optimized_time,
                    "per_mac": optimized_time / len([m for m in test_macs if m])
                },
                "improvement": improvement
            }
            
        except Exception as e:
            logger.error(f"Error testing MAC normalization: {e}")
            return {"error": str(e)}
    
    async def test_concurrent_load(self, num_users: int) -> Dict[str, Any]:
        """Test concurrent load performance."""
        try:
            from app.services.fortiswitch_service_optimized import get_fortiswitches_optimized
            
            logger.info(f"Testing concurrent load with {num_users} users...")
            
            async def single_request():
                start_time = time.time()
                result = await get_fortiswitches_optimized()
                return time.time() - start_time, len(result) if isinstance(result, list) else 0
            
            # Run concurrent requests
            start_time = time.time()
            tasks = [single_request() for _ in range(num_users)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Process results
            successful_requests = [r for r in results if isinstance(r, tuple)]
            failed_requests = [r for r in results if isinstance(r, Exception)]
            
            if successful_requests:
                times = [r[0] for r in successful_requests]
                device_counts = [r[1] for r in successful_requests]
                
                return {
                    "num_users": num_users,
                    "total_time": total_time,
                    "avg_response_time": statistics.mean(times),
                    "min_response_time": min(times),
                    "max_response_time": max(times),
                    "success_rate": (len(successful_requests) / num_users) * 100,
                    "requests_per_second": num_users / total_time,
                    "avg_devices_found": statistics.mean(device_counts) if device_counts else 0,
                    "failed_requests": len(failed_requests)
                }
            else:
                return {
                    "num_users": num_users,
                    "total_time": total_time,
                    "success_rate": 0.0,
                    "failed_requests": len(failed_requests),
                    "error": "All requests failed"
                }
                
        except Exception as e:
            logger.error(f"Error testing concurrent load: {e}")
            return {
                "num_users": num_users,
                "error": str(e),
                "success_rate": 0.0
            }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all performance tests."""
        logger.info("Starting comprehensive performance test suite...")
        
        # Test individual service performance
        logger.info("=" * 60)
        logger.info("Testing Individual Service Performance")
        logger.info("=" * 60)
        
        self.results["original"]["fortiswitch"] = await self.test_original_fortiswitch_service()
        self.results["optimized"]["fortiswitch"] = await self.test_optimized_fortiswitch_service()
        
        # Test MAC normalization performance
        logger.info("=" * 60)
        logger.info("Testing MAC Normalization Performance")
        logger.info("=" * 60)
        
        self.results["mac_normalization"] = await self.test_mac_normalization_performance()
        
        # Test concurrent load
        logger.info("=" * 60)
        logger.info("Testing Concurrent Load Performance")
        logger.info("=" * 60)
        
        self.results["concurrent_load"] = {}
        for num_users in CONCURRENT_USERS:
            self.results["concurrent_load"][f"{num_users}_users"] = await self.test_concurrent_load(num_users)
            await asyncio.sleep(5)  # Cool-down between tests
        
        # Calculate comparisons
        self.calculate_performance_improvements()
        
        return self.results
    
    def calculate_performance_improvements(self):
        """Calculate performance improvements and generate summary."""
        try:
            # FortiSwitch service improvement
            orig_time = self.results["original"]["fortiswitch"]["avg_time"]
            opt_time = self.results["optimized"]["fortiswitch"]["avg_time"]
            
            if orig_time != float('inf') and opt_time != float('inf'):
                improvement = ((orig_time - opt_time) / orig_time) * 100
                self.results["comparison"]["fortiswitch_improvement"] = {
                    "original_avg_time": orig_time,
                    "optimized_avg_time": opt_time,
                    "improvement_percent": improvement,
                    "speedup_factor": orig_time / opt_time if opt_time > 0 else float('inf')
                }
            
            # MAC normalization improvement
            if "mac_normalization" in self.results and "improvement" in self.results["mac_normalization"]:
                self.results["comparison"]["mac_normalization_improvement"] = self.results["mac_normalization"]["improvement"]
            
            # Concurrent load summary
            self.results["comparison"]["concurrent_performance"] = {}
            for load_test in self.results["concurrent_load"]:
                result = self.results["concurrent_load"][load_test]
                if "success_rate" in result and result["success_rate"] > 0:
                    self.results["comparison"]["concurrent_performance"][load_test] = {
                        "avg_response_time": result.get("avg_response_time", 0),
                        "requests_per_second": result.get("requests_per_second", 0),
                        "success_rate": result["success_rate"]
                    }
                    
        except Exception as e:
            logger.error(f"Error calculating improvements: {e}")
    
    def generate_report(self) -> str:
        """Generate a comprehensive performance test report."""
        report = []
        report.append("=" * 80)
        report.append("FORTISWITCH MONITOR - PERFORMANCE TEST REPORT")
        report.append("=" * 80)
        report.append(f"Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Test Iterations: {TEST_ITERATIONS}")
        report.append("")
        
        # FortiSwitch Service Performance
        report.append("1. FORTISWITCH SERVICE PERFORMANCE")
        report.append("-" * 40)
        
        if "fortiswitch_improvement" in self.results["comparison"]:
            comp = self.results["comparison"]["fortiswitch_improvement"]
            report.append(f"Original Average Time: {comp['original_avg_time']:.2f}s")
            report.append(f"Optimized Average Time: {comp['optimized_avg_time']:.2f}s")
            report.append(f"Performance Improvement: {comp['improvement_percent']:.1f}%")
            report.append(f"Speedup Factor: {comp['speedup_factor']:.1f}x")
        else:
            report.append("Unable to calculate FortiSwitch service improvements")
        
        report.append("")
        
        # MAC Normalization Performance
        report.append("2. MAC NORMALIZATION PERFORMANCE")
        report.append("-" * 40)
        
        if "mac_normalization_improvement" in self.results["comparison"]:
            improvement = self.results["comparison"]["mac_normalization_improvement"]
            report.append(f"MAC Normalization Improvement: {improvement:.1f}%")
        else:
            report.append("Unable to calculate MAC normalization improvements")
        
        report.append("")
        
        # Concurrent Load Performance
        report.append("3. CONCURRENT LOAD PERFORMANCE")
        report.append("-" * 40)
        
        if "concurrent_performance" in self.results["comparison"]:
            for load_test, result in self.results["comparison"]["concurrent_performance"].items():
                users = load_test.replace("_users", "")
                report.append(f"{users} Concurrent Users:")
                report.append(f"  Average Response Time: {result['avg_response_time']:.2f}s")
                report.append(f"  Requests per Second: {result['requests_per_second']:.1f}")
                report.append(f"  Success Rate: {result['success_rate']:.1f}%")
                report.append("")
        
        # Summary
        report.append("4. SUMMARY")
        report.append("-" * 40)
        
        if "fortiswitch_improvement" in self.results["comparison"]:
            comp = self.results["comparison"]["fortiswitch_improvement"]
            if comp["improvement_percent"] > 50:
                report.append("✅ EXCELLENT: >50% performance improvement achieved")
            elif comp["improvement_percent"] > 25:
                report.append("✅ GOOD: 25-50% performance improvement achieved")
            elif comp["improvement_percent"] > 0:
                report.append("⚠️  MODERATE: Some performance improvement achieved")
            else:
                report.append("❌ POOR: No significant performance improvement")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


async def main():
    """Main function to run performance tests."""
    print("FortiSwitch Monitor - Performance Test Suite")
    print("=" * 60)
    
    # Initialize test suite
    test_suite = PerformanceTestSuite()
    
    try:
        # Run all tests
        results = await test_suite.run_all_tests()
        
        # Generate and save report
        report = test_suite.generate_report()
        print(report)
        
        # Save detailed results to JSON
        with open("performance_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save report to file
        with open("performance_test_report.txt", "w") as f:
            f.write(report)
        
        print(f"\n📊 Detailed results saved to: performance_test_results.json")
        print(f"📄 Report saved to: performance_test_report.txt")
        
        # Exit with appropriate code
        if "fortiswitch_improvement" in results["comparison"]:
            improvement = results["comparison"]["fortiswitch_improvement"]["improvement_percent"]
            if improvement > 25:
                print(f"\n🎉 SUCCESS: {improvement:.1f}% performance improvement achieved!")
                sys.exit(0)
            else:
                print(f"\n⚠️  WARNING: Only {improvement:.1f}% improvement achieved")
                sys.exit(1)
        else:
            print("\n❌ FAILED: Unable to measure performance improvements")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        print(f"\n❌ FAILED: Performance test encountered an error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())