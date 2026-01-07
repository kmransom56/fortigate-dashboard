"""
Docker container tests for the Network Device MCP Server
"""
import pytest
import docker
import requests
import time
from unittest.mock import patch


@pytest.mark.docker
class TestDockerContainer:
    """Test Docker container functionality"""

    @pytest.fixture(scope="class")
    def docker_client(self):
        """Docker client fixture"""
        return docker.from_env()

    @pytest.fixture(scope="class")
    def container(self, docker_client):
        """Container fixture"""
        # Build the image
        image = docker_client.images.build(
            path=".",
            dockerfile="Dockerfile",
            tag="network-mcp-server:test"
        )[0]

        # Run the container
        container = docker_client.containers.run(
            image.id,
            ports={'12000/tcp': None},  # Let Docker assign random port
            environment={
                'FMG_IP': '127.0.0.1',
                'FMG_USERNAME': 'test',
                'FMG_PASSWORD': 'test',
                'ADOM_NAME': 'root'
            },
            detach=True,
            name="test-network-mcp-server"
        )

        # Wait for container to be ready
        time.sleep(15)

        yield container

        # Cleanup
        container.stop()
        container.remove()

    def test_container_health_check(self, container):
        """Test container health check endpoint"""
        # Get container port
        container.reload()
        port = container.ports['12000/tcp'][0]['HostPort']

        # Test health endpoint
        response = requests.get(f'http://localhost:{port}/health', timeout=10)
        assert response.status_code == 200

        health_data = response.json()
        assert health_data["status"] == "healthy"

    def test_container_api_endpoints(self, container):
        """Test container API endpoints"""
        container.reload()
        port = container.ports['12000/tcp'][0]['HostPort']

        # Test API documentation
        response = requests.get(f'http://localhost:{port}/api', timeout=10)
        assert response.status_code == 200

        api_data = response.json()
        assert "version" in api_data
        assert "new_features" in api_data

    def test_container_brands_endpoint(self, container):
        """Test container brands endpoint"""
        container.reload()
        port = container.ports['12000/tcp'][0]['HostPort']

        response = requests.get(f'http://localhost:{port}/api/brands', timeout=10)
        assert response.status_code == 200

        brands_data = response.json()
        assert brands_data["success"] is True
        assert "brands" in brands_data

    def test_container_fortimanager_endpoint(self, container):
        """Test container FortiManager endpoint"""
        container.reload()
        port = container.ports['12000/tcp'][0]['HostPort']

        response = requests.get(f'http://localhost:{port}/api/fortimanager', timeout=10)
        assert response.status_code == 200

        fm_data = response.json()
        assert fm_data["success"] is True
        assert "data" in fm_data

    def test_container_adom_discovery(self, container):
        """Test container ADOM discovery"""
        container.reload()
        port = container.ports['12000/tcp'][0]['HostPort']

        # Test ADOM discovery for BWW
        response = requests.get(f'http://localhost:{port}/api/fortimanager/BWW/adoms', timeout=10)
        assert response.status_code == 200

        adom_data = response.json()
        # Should either succeed or provide suggestions
        assert "adom_results" in adom_data or "suggested_adoms" in adom_data

    def test_container_error_handling(self, container):
        """Test container error handling"""
        container.reload()
        port = container.ports['12000/tcp'][0]['HostPort']

        # Test invalid brand
        response = requests.get(f'http://localhost:{port}/api/brands/INVALID/overview', timeout=10)
        assert response.status_code == 200

        error_data = response.json()
        assert error_data["success"] is False
        assert "error" in error_data

    def test_container_performance(self, container):
        """Test container performance requirements"""
        container.reload()
        port = container.ports['12000/tcp'][0]['HostPort']

        # Test response times
        endpoints = [
            f'http://localhost:{port}/health',
            f'http://localhost:{port}/api/brands',
            f'http://localhost:{port}/api/fortimanager'
        ]

        for endpoint in endpoints:
            start_time = time.time()
            response = requests.get(endpoint, timeout=10)
            end_time = time.time()

            assert response.status_code == 200
            response_time = end_time - start_time

            # Should respond within 3 seconds (slower in container)
            assert response_time < 3.0, f"Container endpoint {endpoint} took {response_time:.2f}s"

    def test_container_memory_usage(self, container):
        """Test container memory usage"""
        container.reload()

        # Check container stats
        stats = container.stats(stream=False)

        # Memory usage should be reasonable
        memory_usage = stats['memory_stats']['usage']
        memory_limit = stats['memory_stats']['limit']

        # Should use less than 50% of available memory
        memory_percentage = (memory_usage / memory_limit) * 100
        assert memory_percentage < 50, f"Container using {memory_percentage:.1f}% of memory"

    def test_container_logs_output(self, container):
        """Test container logs contain expected output"""
        container.reload()

        # Get recent logs
        logs = container.logs(tail=50).decode('utf-8')

        # Should contain startup messages
        assert 'Network Management Platform' in logs
        assert 'ADOM SUPPORT VERSION' in logs
        assert 'Web Dashboard' in logs
        assert 'localhost:12000' in logs

    def test_container_environment_variables(self, container):
        """Test container environment variable handling"""
        container.reload()
        port = container.ports['12000/tcp'][0]['HostPort']

        # Test that environment variables are being used
        response = requests.get(f'http://localhost:{port}/health', timeout=10)
        health_data = response.json()

        # Should indicate MCP is not available (since we're using test credentials)
        assert "mcp_available" in health_data

    def test_container_restart_behavior(self, docker_client, container):
        """Test container restart behavior"""
        container.reload()
        port = container.ports['12000/tcp'][0]['HostPort']

        # Stop container
        container.stop()
        time.sleep(2)

        # Start container again
        container.start()
        time.sleep(15)

        # Should be healthy again
        response = requests.get(f'http://localhost:{port}/health', timeout=10)
        assert response.status_code == 200

        health_data = response.json()
        assert health_data["status"] == "healthy"
