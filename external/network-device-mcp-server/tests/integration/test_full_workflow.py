"""
Integration tests for the complete Network Device MCP Server workflow
"""
import pytest
import json
import time
from unittest.mock import patch, MagicMock


@pytest.mark.integration
class TestFullWorkflow:
    """Integration tests for complete workflows"""

    def test_complete_brand_overview_workflow(self, client):
        """Test complete workflow from brands list to device details"""
        # Step 1: Get list of brands
        brands_response = client.get('/api/brands')
        assert brands_response.status_code == 200
        brands_data = json.loads(brands_response.data)
        assert brands_data["success"] is True

        # Step 2: Get overview for first brand
        first_brand = brands_data["brands"][0]
        brand_code = first_brand["code"]

        overview_response = client.get(f'/api/brands/{brand_code}/overview')
        assert overview_response.status_code == 200
        overview_data = json.loads(overview_response.data)
        assert overview_data["success"] is True

        # Step 3: Verify overview contains expected data
        brand_summary = overview_data["data"]["brand_summary"]
        assert brand_summary["brand_code"] == brand_code
        assert "total_stores" in brand_summary
        assert "device_prefix" in brand_summary

        # Step 4: Test ADOM discovery for this brand
        adom_response = client.get(f'/api/fortimanager/{brand_code}/adoms')
        assert adom_response.status_code == 200
        adom_data = json.loads(adom_response.data)

        # Should either succeed with MCP or provide suggestions without MCP
        assert "adom_results" in adom_data or "suggested_adoms" in adom_data

    def test_device_pagination_workflow(self, client):
        """Test device pagination workflow"""
        # Test getting devices with pagination
        response = client.get('/api/fortimanager/BWW/devices?limit=5&offset=0')

        assert response.status_code == 200
        data = json.loads(response.data)

        # Check pagination structure
        assert "pagination" in data
        pagination = data["pagination"]

        assert "has_more" in pagination
        assert "next_offset" in pagination
        assert "prev_offset" in pagination
        assert data["offset"] == 0
        assert data["showing_devices"] <= 5

    def test_error_handling_workflow(self, client):
        """Test error handling throughout the application"""
        # Test invalid brand
        response = client.get('/api/brands/INVALID/overview')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is False
        assert "error" in data

        # Test invalid FortiManager
        response = client.get('/api/fortimanager/INVALID/devices')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is False
        assert "error" in data

        # Test search without query
        response = client.get('/api/fortimanager/BWW/devices/search')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is False
        assert "error" in data

    @patch('src.rest_api_server_adom_support.MCP_AVAILABLE', True)
    @patch('src.rest_api_server_adom_support.config')
    @patch('src.rest_api_server_adom_support.fm_manager')
    def test_mcp_integration_workflow(self, mock_fm_manager, mock_config, client):
        """Test complete workflow with MCP integration"""
        # Mock FortiManager configuration
        mock_config.get_fortimanager_by_name.return_value = {
            "host": "10.128.145.4",
            "username": "test_user",
            "password": "test_pass"
        }

        # Mock device data
        mock_devices = [
            {"name": "BWW-001", "serial": "FGT60E123456", "status": "online", "version": "7.2.0"},
            {"name": "BWW-002", "serial": "FGT60E123457", "status": "offline", "version": "7.2.0"}
        ]
        mock_fm_manager.get_managed_devices.return_value = mock_devices

        # Step 1: Test ADOM discovery
        adom_response = client.get('/api/fortimanager/BWW/adoms')
        assert adom_response.status_code == 200
        adom_data = json.loads(adom_response.data)
        assert adom_data["success"] is True

        # Step 2: Test device listing with real data
        device_response = client.get('/api/fortimanager/BWW/devices?adom=root')
        assert device_response.status_code == 200
        device_data = json.loads(device_response.data)
        assert device_data["success"] is True
        assert "devices" in device_data

        # Verify mock was called
        mock_fm_manager.get_managed_devices.assert_called()

    def test_health_and_monitoring_workflow(self, client):
        """Test health check and monitoring functionality"""
        # Test health endpoint
        response = client.get('/health')
        assert response.status_code == 200
        health_data = json.loads(response.data)

        assert health_data["status"] == "healthy"
        assert "mcp_available" in health_data
        assert "features" in health_data
        assert len(health_data["features"]) > 0

        # Test API documentation
        response = client.get('/api')
        assert response.status_code == 200
        api_data = json.loads(response.data)

        assert "version" in api_data
        assert "new_features" in api_data
        assert "ADOM Support" in api_data["new_features"]["ADOM Support"]

    def test_data_consistency_workflow(self, client):
        """Test data consistency across different endpoints"""
        # Get brands data
        brands_response = client.get('/api/brands')
        brands_data = json.loads(brands_response.data)

        # Get FortiManager data
        fm_response = client.get('/api/fortimanager')
        fm_data = json.loads(fm_response.data)

        # Check consistency between endpoints
        brands_total = sum(brand["device_count"] for brand in brands_data["brands"])
        fm_total = fm_data["data"]["total_estimated_devices"]

        # Totals should be consistent (allowing for some variance)
        assert abs(brands_total - fm_total) < 100  # Within 100 devices tolerance

    def test_performance_requirements(self, client):
        """Test that endpoints meet performance requirements"""
        import time

        endpoints = [
            '/health',
            '/api/brands',
            '/api/fortimanager',
            '/api/brands/BWW/overview'
        ]

        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()

            assert response.status_code == 200
            response_time = end_time - start_time

            # Should respond within 2 seconds
            assert response_time < 2.0, f"Endpoint {endpoint} took {response_time:.2f}s"

    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests"""
        import concurrent.futures
        import threading

        def make_request():
            response = client.get('/health')
            return response.status_code

        # Make multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]

        # All requests should succeed
        assert all(status == 200 for status in results)

    def test_memory_usage_stability(self, client):
        """Test memory usage stability over multiple requests"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Make multiple requests
        for _ in range(50):
            client.get('/health')
            client.get('/api/brands')

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024, f"Memory increase too high: {memory_increase} bytes"

    def test_api_response_times(self, client):
        """Test API response times for different endpoints"""
        import time

        test_cases = [
            ('Health Check', '/health', 0.5),
            ('Brands List', '/api/brands', 1.0),
            ('Brand Overview', '/api/brands/BWW/overview', 1.0),
            ('FortiManager List', '/api/fortimanager', 1.0),
            ('ADOM Discovery', '/api/fortimanager/BWW/adoms', 2.0),
        ]

        for test_name, endpoint, max_time in test_cases:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()

            assert response.status_code == 200, f"{test_name} failed"
            response_time = end_time - start_time

            assert response_time < max_time, f"{test_name} took {response_time:.2f}s (max: {max_time}s)"

    def test_api_rate_limiting_simulation(self, client):
        """Test API behavior under load (simulated rate limiting)"""
        import time

        # Make rapid requests
        start_time = time.time()
        responses = []

        for _ in range(20):
            response = client.get('/health')
            responses.append(response.status_code)
            time.sleep(0.01)  # Small delay to avoid overwhelming

        end_time = time.time()
        total_time = end_time - start_time

        # All requests should succeed
        assert all(status == 200 for status in responses)

        # Should complete within reasonable time
        assert total_time < 5.0, f"20 requests took {total_time:.2f}s"

    def test_cross_endpoint_data_validation(self, client):
        """Test data consistency across different endpoints"""
        # Get data from multiple endpoints
        brands_response = client.get('/api/brands')
        fm_response = client.get('/api/fortimanager')

        brands_data = json.loads(brands_response.data)
        fm_data = json.loads(fm_response.data)

        # Extract brand information
        brands = {brand["code"]: brand for brand in brands_data["brands"]}
        fm_instances = {fm["name"]: fm for fm in fm_data["data"]["fortimanager_instances"]}

        # Validate consistency
        for brand_code, brand in brands.items():
            if brand_code in fm_instances:
                fm = fm_instances[brand_code]
                assert brand["fortimanager"] == fm["host"]
                assert brand["device_count"] == fm["estimated_devices"]

    def test_error_recovery_workflow(self, client):
        """Test error recovery and graceful degradation"""
        # Test with invalid requests
        invalid_responses = [
            client.get('/api/brands/INVALID/overview'),
            client.get('/api/fortimanager/INVALID/devices'),
            client.get('/api/fortimanager/BWW/devices/search'),  # Missing query
        ]

        for response in invalid_responses:
            assert response.status_code == 200  # Should return 200 with error in JSON
            data = json.loads(response.data)
            assert data["success"] is False
            assert "error" in data

    def test_api_documentation_accuracy(self, client):
        """Test that API documentation matches actual endpoints"""
        # Get API documentation
        response = client.get('/api')
        assert response.status_code == 200
        api_docs = json.loads(response.data)

        # Test documented endpoints
        documented_endpoints = [
            '/api/brands',
            '/api/fortimanager',
            '/health'
        ]

        for endpoint in documented_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Documented endpoint {endpoint} not available"

        # Test documented examples
        example_endpoints = [
            '/api/fortimanager/bww/devices?adom=root',
            '/api/fortimanager/arbys/adoms',
        ]

        for endpoint in example_endpoints:
            # Should not return 404
            response = client.get(endpoint)
            assert response.status_code != 404, f"Example endpoint {endpoint} not found"
