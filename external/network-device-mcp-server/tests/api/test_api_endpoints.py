"""
API endpoint tests for the Network Device MCP Server
"""
import pytest
import json
from unittest.mock import patch, MagicMock


class TestAPIEndpoints:
    """Test cases for API endpoints"""

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get('/health')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
        assert "timestamp" in data
        assert "features" in data
        assert "mcp_available" in data

    def test_api_docs_endpoint(self, client):
        """Test API documentation endpoint"""
        response = client.get('/api')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert "name" in data
        assert "version" in data
        assert "description" in data
        assert "new_features" in data
        assert "updated_endpoints" in data
        assert "examples" in data

    def test_list_brands_endpoint(self, client):
        """Test list brands endpoint"""
        response = client.get('/api/brands')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert "brands" in data
        assert "total_brands" in data
        assert "total_devices" in data

        # Check brands array
        brands = data["brands"]
        assert len(brands) > 0

        # Check brand structure
        for brand in brands:
            assert "code" in brand
            assert "name" in brand
            assert "device_count" in brand
            assert "status" in brand
            assert "fortimanager" in brand

    def test_brand_overview_endpoint(self, client):
        """Test brand overview endpoint"""
        response = client.get('/api/brands/BWW/overview')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert "data" in data

        # Check response structure
        overview_data = data["data"]
        assert "brand_summary" in overview_data
        assert "infrastructure_status" in overview_data
        assert "security_overview" in overview_data
        assert "adom_options" in overview_data
        assert "next_steps" in overview_data

        # Check brand summary
        brand_summary = overview_data["brand_summary"]
        assert brand_summary["brand"] == "Buffalo Wild Wings"
        assert brand_summary["brand_code"] == "BWW"
        assert "device_prefix" in brand_summary
        assert "total_stores" in brand_summary

    def test_brand_overview_invalid_brand(self, client):
        """Test brand overview with invalid brand"""
        response = client.get('/api/brands/INVALID/overview')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is False
        assert "error" in data

    def test_store_security_endpoint(self, client):
        """Test store security endpoint"""
        response = client.get('/api/stores/BWW/00123/security')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["brand"] == "BWW"
        assert data["store_id"] == "00123"
        assert "security_status" in data

        # Check security status structure
        security_status = data["security_status"]
        assert "overall" in security_status
        assert "firewall" in security_status
        assert "last_policy_update" in security_status
        assert "threat_level" in security_status
        assert "recent_events" in security_status

    def test_fortimanager_list_endpoint(self, client):
        """Test FortiManager list endpoint"""
        response = client.get('/api/fortimanager')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert "data" in data

        # Check FortiManager instances
        fm_data = data["data"]
        assert "fortimanager_instances" in fm_data
        assert "total_count" in fm_data
        assert "total_estimated_devices" in fm_data

        # Check instances structure
        instances = fm_data["fortimanager_instances"]
        assert len(instances) > 0

        for instance in instances:
            assert "name" in instance
            assert "host" in instance
            assert "description" in instance
            assert "status" in instance
            assert "estimated_devices" in instance
            assert "common_adoms" in instance

    @patch('src.rest_api_server_adom_support.MCP_AVAILABLE', True)
    @patch('src.rest_api_server_adom_support.config')
    @patch('src.rest_api_server_adom_support.fm_manager')
    def test_adom_discovery_endpoint_with_mcp(self, mock_fm_manager, mock_config, client):
        """Test ADOM discovery endpoint with MCP available"""
        # Mock FortiManager config
        mock_config.get_fortimanager_by_name.return_value = {
            "host": "10.128.145.4",
            "username": "test_user",
            "password": "test_pass"
        }

        # Mock device data
        mock_devices = [
            {"name": "BWW-001", "serial": "FGT123", "status": "online"},
            {"name": "BWW-002", "serial": "FGT124", "status": "online"}
        ]
        mock_fm_manager.get_managed_devices.return_value = mock_devices

        response = client.get('/api/fortimanager/BWW/adoms')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert "adom_results" in data
        assert "recommendation" in data

        # Check ADOM results
        adom_results = data["adom_results"]
        assert len(adom_results) > 0

        for adom_result in adom_results:
            assert "adom" in adom_result
            assert "device_count" in adom_result
            assert "status" in adom_result
            assert "recommended" in adom_result

    def test_adom_discovery_endpoint_without_mcp(self, client):
        """Test ADOM discovery endpoint without MCP"""
        # Patch MCP_AVAILABLE to False
        with patch('src.rest_api_server_adom_support.MCP_AVAILABLE', False):
            response = client.get('/api/fortimanager/BWW/adoms')

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data["success"] is False
            assert "error" in data
            assert "suggested_adoms" in data

    def test_devices_endpoint_with_adom(self, client):
        """Test devices endpoint with ADOM parameter"""
        response = client.get('/api/fortimanager/BWW/devices?adom=BWW_Stores&limit=10')

        assert response.status_code == 200
        data = json.loads(response.data)

        # Should contain expected fields
        assert "fortimanager" in data
        assert "adom" in data
        assert "total_devices" in data
        assert "showing_devices" in data
        assert "devices" in data

        # Check pagination info
        assert "pagination" in data
        pagination = data["pagination"]
        assert "has_more" in pagination
        assert "next_offset" in pagination
        assert "prev_offset" in pagination

    def test_devices_endpoint_pagination(self, client):
        """Test devices endpoint pagination"""
        # Test with limit and offset
        response = client.get('/api/fortimanager/BWW/devices?limit=5&offset=10')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["offset"] == 10
        assert data["showing_devices"] <= 5  # Should respect limit

    def test_search_devices_endpoint(self, client):
        """Test device search endpoint"""
        response = client.get('/api/fortimanager/BWW/devices/search?q=IBR-BWW-001')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert "fortimanager" in data
        assert "adom" in data
        assert "search_query" in data
        assert "results" in data

    def test_search_devices_without_query(self, client):
        """Test device search without query parameter"""
        response = client.get('/api/fortimanager/BWW/devices/search')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is False
        assert "error" in data

    def test_invalid_fortimanager_name(self, client):
        """Test with invalid FortiManager name"""
        response = client.get('/api/fortimanager/INVALID/devices')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is False
        assert "error" in data

    @pytest.mark.parametrize("brand", ["BWW", "ARBYS", "SONIC"])
    def test_all_brand_overviews(self, client, brand):
        """Test overview endpoints for all brands"""
        response = client.get(f'/api/brands/{brand}/overview')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["data"]["brand_summary"]["brand_code"] == brand

    def test_api_response_content_types(self, client):
        """Test that API responses have correct content types"""
        # Test JSON endpoints
        json_endpoints = [
            '/health',
            '/api',
            '/api/brands',
            '/api/brands/BWW/overview',
            '/api/fortimanager'
        ]

        for endpoint in json_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            assert response.content_type == 'application/json'

    def test_api_error_responses(self, client):
        """Test API error response formats"""
        # Test 404 endpoint
        response = client.get('/nonexistent/endpoint')
        assert response.status_code == 404

        # Test invalid brand
        response = client.get('/api/brands/NONEXISTENT/overview')
        assert response.status_code == 200  # Flask returns 200 with error in JSON
        data = json.loads(response.data)
        assert data["success"] is False
        assert "error" in data
