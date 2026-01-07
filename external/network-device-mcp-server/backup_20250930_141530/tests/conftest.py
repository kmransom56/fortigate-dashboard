"""
Pytest configuration and shared fixtures for Network Device MCP Server tests
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
import sys

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from flask import Flask
from src.rest_api_server_adom_support import app as flask_app


@pytest.fixture
def app():
    """Flask application fixture"""
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key"
    })

    yield flask_app


@pytest.fixture
def client(app):
    """Flask test client fixture"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Flask test runner fixture"""
    return app.test_cli_runner()


@pytest.fixture
def temp_env_file():
    """Temporary environment file fixture"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("FMG_IP=127.0.0.1\n")
        f.write("FMG_USERNAME=test\n")
        f.write("FMG_PASSWORD=test\n")
        f.write("ADOM_NAME=root\n")
        f.write("DEBUG=true\n")
        temp_file = f.name

    yield temp_file

    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def sample_brand_data():
    """Sample brand data fixture"""
    return {
        "code": "BWW",
        "name": "Buffalo Wild Wings",
        "device_count": 678,
        "status": "active",
        "fortimanager": "10.128.145.4"
    }


@pytest.fixture
def sample_fortimanager_data():
    """Sample FortiManager data fixture"""
    return {
        "name": "BWW",
        "host": "10.128.145.4",
        "description": "Buffalo Wild Wings FortiManager",
        "status": "configured",
        "estimated_devices": 678,
        "common_adoms": ["root", "BWW_Stores", "global", "bww", "bww_adom", "buffalo"]
    }


@pytest.fixture
def sample_device_data():
    """Sample device data fixture"""
    return {
        "name": "BWW-00123",
        "serial": "FGT60E123456",
        "status": "online",
        "version": "7.2.0",
        "last_seen": "2024-08-27T14:20:00Z",
        "ha_status": "standalone",
        "location": "Store 123",
        "ip": "10.128.144.123"
    }


@pytest.fixture
def mock_mcp_available():
    """Mock MCP availability fixture"""
    with pytest.MonkeyPatch().context() as m:
        m.setattr('src.rest_api_server_adom_support.MCP_AVAILABLE', True)
        yield


@pytest.fixture
def mock_mcp_unavailable():
    """Mock MCP unavailability fixture"""
    with pytest.MonkeyPatch().context() as m:
        m.setattr('src.rest_api_server_adom_support.MCP_AVAILABLE', False)
        yield


@pytest.fixture
def mock_fortimanager_config():
    """Mock FortiManager configuration fixture"""
    mock_config = {
        "host": "10.128.145.4",
        "username": "test_user",
        "password": "test_pass"
    }
    return mock_config


@pytest.fixture
def mock_device_list():
    """Mock device list fixture"""
    return [
        {"name": "BWW-001", "serial": "FGT60E123456", "status": "online", "version": "7.2.0"},
        {"name": "BWW-002", "serial": "FGT60E123457", "status": "offline", "version": "7.2.0"},
        {"name": "BWW-003", "serial": "FGT60E123458", "status": "online", "version": "7.2.0"}
    ]


@pytest.fixture
def api_response_template():
    """Template for API responses"""
    return {
        "success": True,
        "data": {},
        "message": "Success"
    }


@pytest.fixture
def error_response_template():
    """Template for error responses"""
    return {
        "success": False,
        "error": "Test error message",
        "code": "TEST_ERROR"
    }


@pytest.fixture
def test_database():
    """Test database fixture (if needed for future database tests)"""
    # This would set up a test database if the application used one
    # For now, it's a placeholder for future database testing
    return None


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup fixture that runs after each test"""
    yield

    # Add any cleanup logic here
    # For example, cleaning up temporary files, resetting mocks, etc.


@pytest.fixture
def performance_thresholds():
    """Performance threshold configuration"""
    return {
        "health_endpoint": 0.5,  # seconds
        "api_endpoint": 1.0,     # seconds
        "adom_discovery": 2.0,   # seconds
        "device_listing": 2.0,   # seconds
    }


@pytest.fixture
def load_test_config():
    """Configuration for load testing"""
    return {
        "concurrent_users": 10,
        "requests_per_user": 20,
        "max_response_time": 3.0,
        "acceptable_failure_rate": 0.05  # 5%
    }


# Pytest hooks for additional configuration
def pytest_configure(config):
    """Configure pytest with custom markers and settings"""
    # Register custom markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "docker: Docker tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "auth: Authentication tests")
    config.addinivalue_line("markers", "network: Network related tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Add markers based on file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "api" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        elif "docker" in str(item.fspath):
            item.add_marker(pytest.mark.docker)


# Utility functions for tests
def create_test_request_context(endpoint, method='GET', data=None):
    """Create a test request context"""
    with flask_app.test_request_context(endpoint, method=method, data=data):
        yield


def validate_json_response(response, required_fields=None):
    """Validate JSON response structure"""
    assert response.content_type == 'application/json'

    try:
        data = json.loads(response.data)
    except json.JSONDecodeError:
        pytest.fail("Response is not valid JSON")

    if required_fields:
        for field in required_fields:
            assert field in data, f"Required field '{field}' missing from response"

    return data


def measure_response_time(response_func, *args, **kwargs):
    """Measure response time for a function"""
    import time

    start_time = time.time()
    result = response_func(*args, **kwargs)
    end_time = time.time()

    return result, end_time - start_time
