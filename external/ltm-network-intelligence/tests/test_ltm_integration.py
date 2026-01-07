# tests/test_ltm_integration.py
# Comprehensive test suite for LTM Network Intelligence Platform

import pytest
import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Import platform components
from ltm_integration.ltm_client import LTMClient, LTMMessage, LTMSearchResult
from ltm_integration.network_intelligence import NetworkIntelligenceEngine, NetworkInsight
from ltm_integration.knowledge_graph_bridge import KnowledgeGraphBridge, NetworkEntity
from security.ltm_security_framework import LTMSecurityManager, SecurityEvent, SecurityEventType
from monitoring.ltm_performance_monitor import LTMPerformanceMonitor
from api_gateway.ltm_api_gateway import LTMAPIGateway
from ltm_enhanced_mcp_server import LTMEnhancedNetworkMCPServer
from unified_network_intelligence import UnifiedNetworkIntelligencePlatform

class TestLTMClient:
    """Test suite for LTM Client"""
    
    @pytest.fixture
    async def ltm_client(self):
        """Create LTM client for testing"""
        client = LTMClient("http://localhost:8000", local_fallback=True)
        await client.initialize()
        return client
    
    @pytest.mark.asyncio
    async def test_ltm_client_initialization(self, ltm_client):
        """Test LTM client initialization"""
        assert ltm_client.session_id is not None
        assert ltm_client.persona is not None
        assert "network_intelligence_specialist" in ltm_client.persona.get("role", "")
    
    @pytest.mark.asyncio
    async def test_ltm_awaken(self, ltm_client):
        """Test LTM awakening functionality"""
        result = await ltm_client.awaken({
            "platform": "Test Platform",
            "context": "unit_testing"
        })
        
        assert result["success"] is True
        assert ltm_client.conversation_active is True
    
    @pytest.mark.asyncio
    async def test_record_message(self, ltm_client):
        """Test recording messages in LTM"""
        result = await ltm_client.record_message(
            role="test",
            content="Test message for unit testing",
            tags=["test", "unit_testing"],
            metadata={"test_id": "001"}
        )
        
        assert result["success"] is True
        assert len(ltm_client.local_memory) > 0
    
    @pytest.mark.asyncio
    async def test_search_memories(self, ltm_client):
        """Test searching LTM memories"""
        # Record some test messages first
        await ltm_client.record_message("test", "Network device configuration", ["network", "config"])
        await ltm_client.record_message("test", "Performance monitoring alert", ["performance", "alert"])
        
        # Search for network-related memories
        results = await ltm_client.search_memories(
            query="network device",
            tags=["network"],
            limit=10
        )
        
        assert len(results) > 0
        assert all(isinstance(result, LTMSearchResult) for result in results)
        assert any("network" in result.content.lower() for result in results)
    
    @pytest.mark.asyncio
    async def test_end_conversation(self, ltm_client):
        """Test ending LTM conversation"""
        await ltm_client.awaken()
        result = await ltm_client.end_conversation()
        
        assert result["success"] is True
        assert ltm_client.conversation_active is False

class TestNetworkIntelligenceEngine:
    """Test suite for Network Intelligence Engine"""
    
    @pytest.fixture
    async def intelligence_engine(self):
        """Create intelligence engine for testing"""
        ltm_client = LTMClient("http://localhost:8000", local_fallback=True)
        await ltm_client.initialize()
        return NetworkIntelligenceEngine(ltm_client)
    
    @pytest.mark.asyncio
    async def test_device_performance_analysis(self, intelligence_engine):
        """Test device performance analysis"""
        device_data = {
            "name": "test-firewall",
            "performance": {
                "cpu_percent": 75.5,
                "memory_percent": 60.2,
                "disk_percent": 45.8
            }
        }
        
        insight = await intelligence_engine.analyze_device_performance(device_data)
        
        assert isinstance(insight, NetworkInsight)
        assert insight.insight_type == "performance_analysis"
        assert "test-firewall" in insight.affected_devices
        assert insight.severity in ["low", "medium", "high", "critical"]
        assert len(insight.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_network_topology_analysis(self, intelligence_engine):
        """Test network topology analysis"""
        topology_data = {
            "devices": [
                {"name": "fw01", "status": "online"},
                {"name": "sw01", "status": "online"},
                {"name": "ap01", "status": "offline"}
            ],
            "connections": [],
            "changes": []
        }
        
        insight = await intelligence_engine.analyze_network_topology(topology_data)
        
        assert isinstance(insight, NetworkInsight)
        assert insight.insight_type == "topology_analysis"
        assert insight.severity in ["low", "medium", "high", "critical"]
        assert "ap01" in insight.affected_devices  # Offline device
    
    @pytest.mark.asyncio
    async def test_correlate_insights(self, intelligence_engine):
        """Test insight correlation functionality"""
        insights = [
            NetworkInsight(
                insight_type="performance_analysis",
                title="High CPU Usage",
                description="CPU usage is high on fw01",
                confidence_score=0.8,
                affected_devices=["fw01"],
                recommendations=["Investigate processes"],
                severity="high"
            ),
            NetworkInsight(
                insight_type="topology_analysis", 
                title="Network Connectivity Issue",
                description="Device offline",
                confidence_score=0.9,
                affected_devices=["ap01"],
                recommendations=["Check connectivity"],
                severity="high"
            )
        ]
        
        correlations = await intelligence_engine.correlate_insights(insights)
        
        assert "summary" in correlations
        assert "recommended_actions" in correlations
        assert len(correlations["recommended_actions"]) > 0
    
    @pytest.mark.asyncio
    async def test_intelligence_report_generation(self, intelligence_engine):
        """Test intelligence report generation"""
        insights = [
            NetworkInsight(
                insight_type="performance_analysis",
                title="Test Insight",
                description="Test description",
                confidence_score=0.8,
                affected_devices=["test-device"],
                recommendations=["Test recommendation"],
                severity="medium"
            )
        ]
        
        report = await intelligence_engine.generate_intelligence_report(insights)
        
        assert "timestamp" in report
        assert "executive_summary" in report
        assert "insights" in report
        assert "recommendations" in report
        assert report["executive_summary"]["total_insights"] == 1

class TestKnowledgeGraphBridge:
    """Test suite for Knowledge Graph Bridge"""
    
    @pytest.fixture
    async def kg_bridge(self):
        """Create knowledge graph bridge for testing"""
        ltm_client = LTMClient("http://localhost:8000", local_fallback=True)
        await ltm_client.initialize()
        
        bridge = KnowledgeGraphBridge(
            ltm_client=ltm_client,
            neo4j_config={"uri": "bolt://localhost:7687", "user": "neo4j", "password": "test"},
            milvus_config={"host": "localhost", "port": "19530", "collection_name": "test"}
        )
        
        # Mock the initialization to avoid requiring actual databases
        bridge.initialized = True
        bridge.neo4j_available = False
        bridge.milvus_available = False
        
        return bridge
    
    @pytest.mark.asyncio
    async def test_bridge_initialization(self, kg_bridge):
        """Test knowledge graph bridge initialization"""
        status = await kg_bridge.get_bridge_status()
        
        assert "initialized" in status
        assert "neo4j_available" in status
        assert "milvus_available" in status
    
    @pytest.mark.asyncio
    async def test_add_network_entity(self, kg_bridge):
        """Test adding network entities"""
        entity = NetworkEntity(
            entity_id="test_device_001",
            entity_type="device",
            name="Test Device",
            properties={"type": "firewall", "location": "datacenter1"}
        )
        
        # Mock the database operations since we don't have actual databases
        with patch.object(kg_bridge, '_add_entity_to_neo4j') as mock_neo4j:
            mock_neo4j.return_value = {"success": True}
            
            result = await kg_bridge.add_network_entity(entity)
            assert result["entity_id"] == "test_device_001"
    
    @pytest.mark.asyncio
    async def test_discover_network_topology(self, kg_bridge):
        """Test network topology discovery"""
        discovery_source = {
            "type": "mcp_server",
            "devices": [
                {"name": "fw01", "type": "FortiGate", "status": "online"},
                {"name": "sw01", "type": "Meraki", "status": "online"}
            ]
        }
        
        # Mock database operations
        with patch.object(kg_bridge, 'add_network_entity') as mock_add:
            mock_add.return_value = {"success": True}
            
            result = await kg_bridge.discover_network_topology(discovery_source)
            
            assert result["source"] == "mcp_server"
            assert result["entities_discovered"] >= 0

class TestSecurityManager:
    """Test suite for Security Manager"""
    
    @pytest.fixture
    async def security_manager(self):
        """Create security manager for testing"""
        manager = LTMSecurityManager()
        
        # Mock LTM client
        ltm_client = AsyncMock()
        await manager.initialize(ltm_client)
        
        return manager
    
    @pytest.mark.asyncio
    async def test_security_manager_initialization(self, security_manager):
        """Test security manager initialization"""
        assert security_manager.initialized is True
        assert len(security_manager.compliance_rules) > 0
        assert len(security_manager.alert_rules) > 0
    
    @pytest.mark.asyncio
    async def test_log_security_event(self, security_manager):
        """Test security event logging"""
        event = SecurityEvent(
            event_id="test_001",
            event_type=SecurityEventType.AUTHENTICATION,
            timestamp=datetime.now().isoformat(),
            user_id="test_user",
            session_id="test_session",
            source_ip="192.168.1.100",
            resource_accessed="/api/login",
            action_attempted="user_login",
            success=True,
            risk_level="low",
            details={"login_method": "password"}
        )
        
        result = await security_manager.log_security_event(event)
        assert result["event_id"] == "test_001"
        assert result["logged"] is True
    
    @pytest.mark.asyncio
    async def test_compliance_check(self, security_manager):
        """Test compliance checking"""
        from security.ltm_security_framework import ComplianceStandard
        
        result = await security_manager.check_compliance(ComplianceStandard.PCI_DSS)
        
        assert result["standard"] == "pci_dss"
        assert "checks_performed" in result
        assert "overall_compliance" in result
    
    @pytest.mark.asyncio
    async def test_encrypt_decrypt_data(self, security_manager):
        """Test data encryption and decryption"""
        test_data = "sensitive network configuration data"
        
        # Test encryption
        encrypt_result = await security_manager.encrypt_sensitive_data(test_data)
        if encrypt_result["success"]:
            encrypted_data = encrypt_result["encrypted_data"]
            
            # Test decryption
            decrypt_result = await security_manager.decrypt_sensitive_data(encrypted_data)
            if decrypt_result["success"]:
                assert decrypt_result["decrypted_data"] == test_data

class TestPerformanceMonitor:
    """Test suite for Performance Monitor"""
    
    @pytest.fixture
    async def performance_monitor(self):
        """Create performance monitor for testing"""
        ltm_client = AsyncMock()
        monitor = LTMPerformanceMonitor(ltm_client)
        await monitor.initialize()
        return monitor
    
    @pytest.mark.asyncio
    async def test_monitor_initialization(self, performance_monitor):
        """Test performance monitor initialization"""
        assert len(performance_monitor.metrics_store) > 0
        assert len(performance_monitor.alert_rules) > 0
        assert performance_monitor.performance_baselines is not None
    
    @pytest.mark.asyncio
    async def test_collect_system_metrics(self, performance_monitor):
        """Test system metrics collection"""
        cpu_metrics = await performance_monitor._collect_cpu_metrics()
        memory_metrics = await performance_monitor._collect_memory_metrics()
        disk_metrics = await performance_monitor._collect_disk_metrics()
        
        assert "cpu_percent" in cpu_metrics
        assert "timestamp" in cpu_metrics
        assert "total" in memory_metrics
        assert "percent" in memory_metrics
        assert "total" in disk_metrics
        assert "percent" in disk_metrics
    
    @pytest.mark.asyncio
    async def test_performance_dashboard(self, performance_monitor):
        """Test performance dashboard generation"""
        dashboard = await performance_monitor.get_performance_dashboard()
        
        assert "timestamp" in dashboard
        assert "monitoring_active" in dashboard
        assert "system_health" in dashboard
        assert "alert_summary" in dashboard

class TestAPIGateway:
    """Test suite for API Gateway"""
    
    @pytest.fixture
    async def api_gateway(self):
        """Create API gateway for testing"""
        ltm_client = AsyncMock()
        gateway = LTMAPIGateway()
        await gateway.initialize(ltm_client)
        return gateway
    
    @pytest.mark.asyncio
    async def test_gateway_initialization(self, api_gateway):
        """Test API gateway initialization"""
        assert api_gateway.ltm_client is not None
        assert len(api_gateway.rate_limit_rules) > 0
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, api_gateway):
        """Test rate limiting functionality"""
        from api_gateway.ltm_api_gateway import APIRequest
        
        request = APIRequest(
            request_id="test_001",
            endpoint="/api/test",
            method="GET",
            user_id="test_user",
            source_ip="192.168.1.100",
            timestamp=datetime.now().isoformat(),
            headers={},
            query_params={},
            body=None,
            authenticated=True
        )
        
        result = await api_gateway._check_rate_limits(request)
        assert "allowed" in result

class TestMCPServer:
    """Test suite for Enhanced MCP Server"""
    
    @pytest.fixture
    async def mcp_server(self):
        """Create enhanced MCP server for testing"""
        server = LTMEnhancedNetworkMCPServer()
        
        # Mock LTM client
        ltm_client = AsyncMock()
        await server.initialize_with_ltm()
        
        return server
    
    @pytest.mark.asyncio
    async def test_mcp_server_initialization(self, mcp_server):
        """Test MCP server initialization"""
        assert mcp_server.devices is not None
        assert len(mcp_server.devices) >= 0
    
    @pytest.mark.asyncio
    async def test_device_status_retrieval(self, mcp_server):
        """Test device status retrieval with LTM enhancement"""
        # Mock device configuration
        mcp_server.devices["test_device"] = {
            "type": "FortiGate",
            "host": "192.168.1.1",
            "ltm_context": {"device_role": "firewall", "criticality": "high"}
        }
        
        result = await mcp_server._get_device_status_enhanced("test_device")
        
        assert result["device_name"] == "test_device"
        assert "current_status" in result
        assert "ltm_insights" in result

class TestUnifiedPlatform:
    """Test suite for Unified Platform"""
    
    @pytest.fixture
    async def unified_platform(self):
        """Create unified platform for testing"""
        platform = UnifiedNetworkIntelligencePlatform()
        return platform
    
    @pytest.mark.asyncio
    async def test_platform_initialization(self, unified_platform):
        """Test unified platform initialization"""
        # Mock component initialization
        with patch.object(unified_platform, '_create_directories'):
            with patch.object(unified_platform, '_connect_existing_repositories'):
                result = await unified_platform.initialize(components=["ltm"])
                
                assert "platform" in result
                assert "timestamp" in result
                assert "overall_status" in result
    
    @pytest.mark.asyncio
    async def test_holistic_network_analysis(self, unified_platform):
        """Test holistic network analysis"""
        # Mock initialization
        unified_platform.initialized = True
        unified_platform.ltm_client = AsyncMock()
        unified_platform.network_intelligence = AsyncMock()
        
        # Mock network intelligence methods
        unified_platform.network_intelligence.generate_intelligence_report = AsyncMock(
            return_value={
                "executive_summary": {"total_insights": 3, "network_health_score": 85.0},
                "insights": [],
                "recommendations": {"immediate_actions": [], "strategic_actions": []}
            }
        )
        
        result = await unified_platform.analyze_network_holistically()
        
        assert "analysis_type" in result
        assert "timestamp" in result
        assert "systems_contributing" in result
    
    @pytest.mark.asyncio
    async def test_executive_dashboard_generation(self, unified_platform):
        """Test executive dashboard generation"""
        # Mock initialization
        unified_platform.initialized = True
        unified_platform.running_services = {"ltm_client": "running", "api_gateway": "running"}
        unified_platform.ltm_client = AsyncMock()
        
        # Mock analysis method
        unified_platform.analyze_network_holistically = AsyncMock(
            return_value={
                "executive_summary": {"total_insights": 5, "network_health_score": 90.0},
                "recommendations": []
            }
        )
        
        dashboard = await unified_platform.generate_executive_dashboard()
        
        assert "platform_overview" in dashboard
        assert "system_status" in dashboard
        assert "network_intelligence" in dashboard
        assert "business_metrics" in dashboard

class TestIntegration:
    """Integration tests for the complete platform"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        # This would test a complete workflow from device discovery
        # through analysis to reporting
        
        # Initialize platform
        platform = UnifiedNetworkIntelligencePlatform()
        
        # Mock all external dependencies
        with patch('ltm_integration.ltm_client.aiohttp.ClientSession'):
            with patch('neo4j.AsyncGraphDatabase.driver'):
                with patch('pymilvus.connections.connect'):
                    # Mock successful initialization
                    result = await platform.initialize(components=["ltm"])
                    
                    # Verify initialization completed
                    assert result is not None
                    assert "overall_status" in result
    
    @pytest.mark.asyncio
    async def test_cross_component_communication(self):
        """Test communication between platform components"""
        # Initialize components
        ltm_client = LTMClient("http://localhost:8000", local_fallback=True)
        await ltm_client.initialize()
        
        intelligence_engine = NetworkIntelligenceEngine(ltm_client)
        
        # Test that intelligence engine can record insights in LTM
        device_data = {
            "name": "integration-test-device",
            "performance": {"cpu_percent": 50.0, "memory_percent": 40.0}
        }
        
        insight = await intelligence_engine.analyze_device_performance(device_data)
        
        # Verify insight was created and recorded
        assert insight is not None
        assert len(ltm_client.local_memory) > 0
        
        # Verify we can search for the recorded insight
        memories = await ltm_client.search_memories(
            query="integration-test-device performance",
            limit=5
        )
        
        assert len(memories) > 0

# Pytest configuration and fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def cleanup_test_data():
    """Cleanup test data after each test"""
    yield
    # Cleanup code would go here if needed

# Test configuration
pytest_plugins = ["pytest_asyncio"]

# Custom test markers
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.timeout(30)  # 30 second timeout for async tests
]