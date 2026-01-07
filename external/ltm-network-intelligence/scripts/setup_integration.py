#!/usr/bin/env python3
# scripts/setup_integration.py
# Automated integration setup script for existing repositories

import os
import json
import sys
import asyncio
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LTMIntegrationSetup:
    """Automated setup for LTM platform integration with existing repositories"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path).resolve()
        self.repositories = {
            # Core Network Management Tools
            "network-ai-troubleshooter": {
                "expected_files": ["troubleshooter.py", "network_analyzer.py", "ai_agent.py"],
                "integration_mode": "bridge",
                "modifications": ["add_ltm_client", "enhance_troubleshooting", "bridge_knowledge_graph"],
                "priority": "high"
            },
            "network-device-mcp-server": {
                "expected_files": ["mcp_server.py", "device_manager.py", "fortigate_tools.py"],
                "integration_mode": "enhance", 
                "modifications": ["extend_mcp_server", "add_ltm_learning", "enhance_tools"],
                "priority": "high"
            },
            "FortiGate-Enterprise-Platform": {
                "expected_files": ["main.py", "policy_manager.py", "dashboard.py"],
                "integration_mode": "bridge",
                "modifications": ["add_ltm_bridge", "enhance_policy_management", "integrate_intelligence"],
                "priority": "high"
            },
            "ai-research-platform": {
                "expected_files": ["research_platform.py", "model_trainer.py", "data_processor.py"],
                "integration_mode": "bridge",
                "modifications": ["connect_research_models", "enhance_training", "integrate_insights"],
                "priority": "high"
            },
            "network_device_utils": {
                "expected_files": ["device_connector.py", "configuration_manager.py", "monitoring_utils.py"],
                "integration_mode": "import",
                "modifications": ["enhance_utilities", "add_ltm_logging", "integrate_monitoring"],
                "priority": "medium"
            },
            
            # Fortinet Management Tools
            "fortinet-manager": {
                "expected_files": ["manager.py", "fortigate_api.py", "main.py"],
                "integration_mode": "bridge",
                "modifications": ["add_ltm_integration", "enhance_management", "add_intelligence"],
                "priority": "high"
            },
            "fortinet-manager-analyzer-tool": {
                "expected_files": ["analyzer.py", "main.py", "fortinet_api.py"],
                "integration_mode": "bridge",
                "modifications": ["enhance_analysis", "add_ltm_learning", "integrate_patterns"],
                "priority": "medium"
            },
            "fortinet-manager-realtime-web": {
                "expected_files": ["app.py", "main.py", "realtime_monitor.py"],
                "integration_mode": "bridge",
                "modifications": ["add_ltm_realtime", "enhance_monitoring", "integrate_alerts"],
                "priority": "medium"
            },
            "fortigate-dashboard": {
                "expected_files": ["dashboard.py", "app.py", "main.py"],
                "integration_mode": "bridge",
                "modifications": ["enhance_dashboard", "add_ltm_insights", "integrate_analytics"],
                "priority": "medium"
            },
            "fortigate-network-monitor": {
                "expected_files": ["monitor.py", "network_scanner.py", "main.py"],
                "integration_mode": "bridge",
                "modifications": ["enhance_monitoring", "add_ltm_patterns", "integrate_alerts"],
                "priority": "medium"
            },
            "firewall_optimizer": {
                "expected_files": ["optimizer.py", "rule_analyzer.py", "main.py"],
                "integration_mode": "bridge",
                "modifications": ["enhance_optimization", "add_ltm_learning", "integrate_recommendations"],
                "priority": "medium"
            },
            
            # Meraki Management Tools  
            "meraki_management_application": {
                "expected_files": ["app.py", "meraki_api.py", "main.py"],
                "integration_mode": "bridge",
                "modifications": ["add_ltm_integration", "enhance_management", "add_intelligence"],
                "priority": "high"
            },
            "meraki-explorer": {
                "expected_files": ["explorer.py", "meraki_client.py", "main.py"],
                "integration_mode": "bridge", 
                "modifications": ["enhance_exploration", "add_ltm_discovery", "integrate_mapping"],
                "priority": "medium"
            },
            "cisco-meraki-cli": {
                "expected_files": ["cli.py", "meraki_commands.py", "main.py"],
                "integration_mode": "enhance",
                "modifications": ["enhance_cli", "add_ltm_commands", "integrate_intelligence"],
                "priority": "medium"
            },
            "cisco-meraki-cli-enhanced": {
                "expected_files": ["enhanced_cli.py", "meraki_api.py", "main.py"],
                "integration_mode": "enhance",
                "modifications": ["further_enhance_cli", "add_ltm_advanced", "integrate_analytics"],
                "priority": "medium"
            },
            
            # Network Analysis and Monitoring
            "ai-network-management-system": {
                "expected_files": ["ai_manager.py", "network_analyzer.py", "main.py"],
                "integration_mode": "bridge",
                "modifications": ["integrate_ai_systems", "enhance_management", "add_ltm_coordination"],
                "priority": "high"
            },
            "restaurant-network-noc": {
                "expected_files": ["noc.py", "monitor.py", "main.py"],
                "integration_mode": "bridge",
                "modifications": ["enhance_noc", "add_ltm_insights", "integrate_specialized_monitoring"],
                "priority": "low"
            },
            "network-device-mapper-tool": {
                "expected_files": ["mapper.py", "network_discovery.py", "main.py"],
                "integration_mode": "bridge",
                "modifications": ["enhance_mapping", "add_ltm_topology", "integrate_knowledge_graph"],
                "priority": "medium"
            },
            "network-inventory-tool": {
                "expected_files": ["inventory.py", "device_scanner.py", "main.py"],
                "integration_mode": "bridge",
                "modifications": ["enhance_inventory", "add_ltm_tracking", "integrate_asset_management"],
                "priority": "medium"
            },
            "port_scanner": {
                "expected_files": ["scanner.py", "port_analyzer.py", "main.py"],
                "integration_mode": "import",
                "modifications": ["enhance_scanning", "add_ltm_results", "integrate_security_analysis"],
                "priority": "low"
            },
            
            # Configuration and Utilities
            "network-config-parser-tool": {
                "expected_files": ["parser.py", "config_analyzer.py", "main.py"],
                "integration_mode": "import",
                "modifications": ["enhance_parsing", "add_ltm_patterns", "integrate_config_intelligence"],
                "priority": "medium"
            },
            "ztp": {
                "expected_files": ["ztp.py", "provisioning.py", "main.py"],
                "integration_mode": "bridge",
                "modifications": ["enhance_ztp", "add_ltm_provisioning", "integrate_automated_setup"],
                "priority": "medium"
            },
            "cert-manager": {
                "expected_files": ["cert_manager.py", "ssl_handler.py", "main.py"],
                "integration_mode": "import",
                "modifications": ["enhance_cert_management", "add_ltm_tracking", "integrate_security"],
                "priority": "low"
            },
            
            # MCP Servers
            "mcp-servers": {
                "expected_files": ["server.py", "mcp_handler.py", "main.py"],
                "integration_mode": "enhance",
                "modifications": ["enhance_mcp_servers", "add_ltm_coordination", "integrate_multi_server"],
                "priority": "medium"
            },
            
            # AI and Automation Tools
            "fortinet-ai-agent-core": {
                "expected_files": ["ai_agent.py", "fortinet_integration.py", "main.py"],
                "integration_mode": "bridge",
                "modifications": ["integrate_ai_agents", "enhance_fortinet_ai", "add_ltm_coordination"],
                "priority": "high"
            },
            "autogen": {
                "expected_files": ["autogen.py", "agent_manager.py", "main.py"],
                "integration_mode": "bridge",
                "modifications": ["integrate_autogen", "add_ltm_agents", "enhance_automation"],
                "priority": "medium"
            }
        }
        
    def scan_for_repositories(self, search_paths: List[str] = None) -> Dict[str, str]:
        """Scan for existing repositories in common locations"""
        if search_paths is None:
            search_paths = [
                str(self.base_path.parent),
                str(self.base_path.parent / "repositories"),
                str(Path.home() / "repositories"),
                str(Path.home() / "projects"),
                "/opt/repositories"
            ]
        
        found_repositories = {}
        
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
                
            logger.info(f"Scanning {search_path} for repositories...")
            
            for item in os.listdir(search_path):
                item_path = os.path.join(search_path, item)
                
                if not os.path.isdir(item_path):
                    continue
                    
                # Check if this matches any of our target repositories
                for repo_name, repo_config in self.repositories.items():
                    if repo_name.lower() in item.lower() or any(part in item.lower() for part in repo_name.split("-")):
                        # Verify it's actually the right repository by checking for expected files
                        if self.verify_repository_structure(item_path, repo_config["expected_files"]):
                            found_repositories[repo_name] = item_path
                            logger.info(f"✓ Found {repo_name} at {item_path}")
                            break
        
        return found_repositories

    def verify_repository_structure(self, repo_path: str, expected_files: List[str]) -> bool:
        """Verify repository has expected structure"""
        found_files = 0
        
        for root, dirs, files in os.walk(repo_path):
            for expected_file in expected_files:
                if expected_file in files:
                    found_files += 1
                    
        # Consider it a match if we find at least 50% of expected files
        return found_files >= len(expected_files) * 0.5

    def create_integration_config(self, found_repositories: Dict[str, str]) -> Dict[str, any]:
        """Create integration configuration"""
        config = {
            "integrations": {
                "existing_repositories": {}
            }
        }
        
        for repo_name, repo_path in found_repositories.items():
            config["integrations"]["existing_repositories"][repo_name.replace("-", "_")] = {
                "path": repo_path,
                "integration_mode": self.repositories[repo_name]["integration_mode"],
                "status": "discovered",
                "modifications_needed": self.repositories[repo_name]["modifications"]
            }
        
        return config

    def backup_repository(self, repo_path: str, backup_suffix: str = "_backup_ltm") -> str:
        """Create backup of repository before modification"""
        backup_path = repo_path + backup_suffix
        
        if os.path.exists(backup_path):
            logger.warning(f"Backup already exists at {backup_path}")
            return backup_path
            
        logger.info(f"Creating backup of {repo_path} -> {backup_path}")
        
        try:
            shutil.copytree(repo_path, backup_path)
            logger.info(f"✓ Backup created at {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def create_integration_files(self, repo_name: str, repo_path: str) -> bool:
        """Create integration files for a repository"""
        try:
            integration_dir = os.path.join(repo_path, "ltm_integration")
            os.makedirs(integration_dir, exist_ok=True)
            
            # Create integration bridge file
            bridge_file = self.generate_integration_bridge(repo_name)
            with open(os.path.join(integration_dir, "ltm_bridge.py"), 'w') as f:
                f.write(bridge_file)
            
            # Create configuration file
            config_file = self.generate_integration_config(repo_name)
            with open(os.path.join(integration_dir, "integration_config.json"), 'w') as f:
                f.write(json.dumps(config_file, indent=2))
            
            # Create initialization script
            init_script = self.generate_initialization_script(repo_name)
            with open(os.path.join(integration_dir, "initialize_ltm.py"), 'w') as f:
                f.write(init_script)
            
            # Create __init__.py
            with open(os.path.join(integration_dir, "__init__.py"), 'w') as f:
                f.write(f'# LTM Integration for {repo_name}\n')
                f.write('from .ltm_bridge import *\n')
            
            logger.info(f"✓ Created integration files for {repo_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create integration files for {repo_name}: {e}")
            return False

    def generate_integration_bridge(self, repo_name: str) -> str:
        """Generate integration bridge code for repository"""
        
        if repo_name == "netai-troubleshooter":
            return '''
# ltm_integration/ltm_bridge.py
# LTM Integration Bridge for netai-troubleshooter

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ltm-platform'))

from ltm_integration import LTMClient, NetworkIntelligenceEngine
from ltm_integration.knowledge_graph_bridge import KnowledgeGraphBridge

class NetAITroubleshooterLTMBridge:
    """LTM Bridge for netai-troubleshooter integration"""
    
    def __init__(self, ltm_server_url="http://localhost:8000"):
        self.ltm_client = LTMClient(ltm_server_url)
        self.network_intelligence = None
        self.kg_bridge = None
        
    async def initialize(self):
        """Initialize LTM bridge"""
        await self.ltm_client.initialize()
        await self.ltm_client.awaken({
            "platform": "NetAI Troubleshooter",
            "capabilities": ["neo4j", "milvus", "llm_analysis", "troubleshooting"]
        })
        
        self.network_intelligence = NetworkIntelligenceEngine(self.ltm_client)
        
    async def enhance_troubleshooting(self, issue_description, existing_analysis):
        """Enhance troubleshooting with LTM insights"""
        
        # Search for similar issues in LTM
        similar_issues = await self.ltm_client.search_memories(
            query=f"network troubleshooting {issue_description}",
            tags=["troubleshooting", "network", "diagnosis"],
            limit=10
        )
        
        # Combine with existing analysis
        enhanced_analysis = {
            "original_analysis": existing_analysis,
            "ltm_insights": [
                {
                    "content": issue.content,
                    "relevance": issue.relevance_score,
                    "timestamp": issue.timestamp
                } for issue in similar_issues
            ],
            "recommendations": []
        }
        
        # Generate enhanced recommendations
        if similar_issues:
            enhanced_analysis["recommendations"].extend([
                "Review similar historical issues for patterns",
                "Apply solutions that worked for similar problems",
                "Consider preventive measures based on past incidents"
            ])
        
        # Record this troubleshooting session
        await self.ltm_client.record_message(
            role="troubleshooter",
            content=f"Network issue analyzed: {issue_description}",
            tags=["troubleshooting", "analysis", "network"],
            metadata=enhanced_analysis
        )
        
        return enhanced_analysis
        
    async def bridge_neo4j_data(self, neo4j_results):
        """Bridge Neo4j data to LTM platform"""
        if self.kg_bridge:
            await self.kg_bridge.discover_network_topology({
                "type": "neo4j_import",
                "topology_data": neo4j_results
            })
'''
        
        elif repo_name == "network-device-mcp-server":
            return '''
# ltm_integration/ltm_bridge.py
# LTM Integration Bridge for network-device-mcp-server

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ltm-platform'))

from ltm_enhanced_mcp_server import LTMEnhancedNetworkMCPServer

class NetworkDeviceMCPLTMBridge(LTMEnhancedNetworkMCPServer):
    """Enhanced MCP Server with LTM integration for existing network-device-mcp-server"""
    
    def __init__(self, existing_server, config_path="config/devices_enhanced.json"):
        super().__init__(config_path)
        self.existing_server = existing_server
        
    async def initialize_with_existing_server(self):
        """Initialize LTM integration while preserving existing server functionality"""
        
        # Initialize LTM components
        await super().initialize_with_ltm()
        
        # Migrate existing device configurations
        if hasattr(self.existing_server, 'devices'):
            for device_name, device_config in self.existing_server.devices.items():
                # Enhance device config with LTM context
                enhanced_config = self.enhance_device_config(device_config)
                self.devices[device_name] = enhanced_config
        
        # Preserve existing tools while adding LTM enhancements
        await self.migrate_existing_tools()
        
    def enhance_device_config(self, device_config):
        """Enhance existing device configuration with LTM context"""
        enhanced = device_config.copy()
        enhanced["ltm_context"] = {
            "device_role": self.infer_device_role(device_config),
            "criticality": self.infer_criticality(device_config),
            "learning_focus": ["performance", "configuration", "security"]
        }
        return enhanced
        
    def infer_device_role(self, config):
        """Infer device role from configuration"""
        device_type = config.get("type", "").lower()
        if "firewall" in device_type or "fortigate" in device_type:
            return "security_appliance"
        elif "switch" in device_type or "meraki" in device_type:
            return "network_infrastructure" 
        else:
            return "network_device"
            
    def infer_criticality(self, config):
        """Infer device criticality from configuration"""
        # Simple heuristic - can be enhanced based on actual configuration
        return "high" if config.get("primary", False) else "medium"
        
    async def migrate_existing_tools(self):
        """Migrate existing MCP tools to LTM-enhanced versions"""
        # This would be customized based on the specific tools in the existing server
        pass
'''
        
        elif repo_name == "FortiGate-Enterprise-Platform":
            return '''
# ltm_integration/ltm_bridge.py  
# LTM Integration Bridge for FortiGate-Enterprise-Platform

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ltm-platform'))

from ltm_integration import LTMClient
from ltm_integration.knowledge_graph_bridge import KnowledgeGraphBridge, NetworkEntity

class FortiGateEnterpriseLTMBridge:
    """LTM Bridge for FortiGate Enterprise Platform"""
    
    def __init__(self, ltm_server_url="http://localhost:8000"):
        self.ltm_client = LTMClient(ltm_server_url)
        self.kg_bridge = None
        
    async def initialize(self):
        """Initialize LTM bridge for FortiGate platform"""
        await self.ltm_client.initialize()
        await self.ltm_client.awaken({
            "platform": "FortiGate Enterprise Platform",
            "capabilities": ["policy_management", "security_analysis", "enterprise_deployment"]
        })
        
    async def enhance_policy_creation(self, policy_data, creation_result):
        """Enhance policy creation with LTM learning"""
        
        # Record policy creation for learning
        await self.ltm_client.record_message(
            role="policy_manager",
            content=f"FortiGate policy created: {policy_data.get('name')} - Action: {policy_data.get('action')}",
            tags=["fortigate", "policy", "security", policy_data.get("action", "unknown")],
            metadata={
                "policy_data": policy_data,
                "creation_result": creation_result
            }
        )
        
        # Add to knowledge graph if available
        if self.kg_bridge:
            policy_entity = NetworkEntity(
                entity_id=f"fortigate_policy_{creation_result.get('id', 'unknown')}",
                entity_type="security_policy",
                name=policy_data.get("name", "unnamed_policy"),
                properties=policy_data
            )
            await self.kg_bridge.add_network_entity(policy_entity)
        
        return creation_result
        
    async def analyze_security_patterns(self):
        """Analyze security patterns using LTM"""
        
        # Search for security-related patterns
        security_patterns = await self.ltm_client.search_memories(
            query="fortigate security policy patterns analysis",
            tags=["security", "policy", "patterns", "fortigate"],
            limit=20
        )
        
        pattern_analysis = {
            "total_patterns": len(security_patterns),
            "common_policies": [],
            "security_trends": [],
            "recommendations": []
        }
        
        # Analyze patterns (simplified)
        for pattern in security_patterns:
            if "policy" in pattern.content.lower():
                pattern_analysis["common_policies"].append({
                    "description": pattern.content[:100],
                    "relevance": pattern.relevance_score
                })
        
        if pattern_analysis["common_policies"]:
            pattern_analysis["recommendations"].extend([
                "Review common policy patterns for optimization opportunities",
                "Consider standardizing frequently used policy configurations",
                "Implement automated policy validation based on historical patterns"
            ])
        
        return pattern_analysis
'''
        
        else:
            # Generic integration bridge
            return f'''
# ltm_integration/ltm_bridge.py
# LTM Integration Bridge for {repo_name}

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ltm-platform'))

from ltm_integration import LTMClient

class {repo_name.replace("-", "").title()}LTMBridge:
    """Generic LTM Bridge for {repo_name}"""
    
    def __init__(self, ltm_server_url="http://localhost:8000"):
        self.ltm_client = LTMClient(ltm_server_url)
        
    async def initialize(self):
        """Initialize LTM bridge"""
        await self.ltm_client.initialize()
        await self.ltm_client.awaken({{
            "platform": "{repo_name}",
            "capabilities": ["network_management", "monitoring", "analysis"]
        }})
        
    async def record_activity(self, activity_type, description, metadata=None):
        """Record activity in LTM for learning"""
        await self.ltm_client.record_message(
            role="system",
            content=f"{activity_type}: {{description}}",
            tags=["{repo_name.replace('-', '_')}", activity_type],
            metadata=metadata or {{}}
        )
'''

    def generate_integration_config(self, repo_name: str) -> Dict[str, any]:
        """Generate integration configuration for repository"""
        return {
            "integration_name": f"{repo_name}_ltm_integration",
            "integration_version": "2.0.0",
            "ltm_platform_path": "../../../ltm-platform",
            "ltm_server_url": "http://localhost:8000",
            "integration_mode": self.repositories[repo_name]["integration_mode"],
            "features": {
                "ltm_learning": True,
                "knowledge_graph": repo_name in ["netai-troubleshooter", "FortiGate-Enterprise-Platform"],
                "performance_monitoring": True,
                "security_integration": "FortiGate" in repo_name
            },
            "configuration": {
                "learning_enabled": True,
                "auto_record_activities": True,
                "intelligent_insights": True
            }
        }

    def generate_initialization_script(self, repo_name: str) -> str:
        """Generate initialization script for repository integration"""
        return f'''#!/usr/bin/env python3
# ltm_integration/initialize_ltm.py
# Initialization script for {repo_name} LTM integration

import asyncio
import sys
import os
import json
from pathlib import Path

# Add LTM platform to path
ltm_platform_path = Path(__file__).parent.parent.parent.parent / "ltm-platform"
sys.path.insert(0, str(ltm_platform_path))

from ltm_bridge import {repo_name.replace("-", "").title()}LTMBridge

async def initialize_ltm_integration():
    """Initialize LTM integration for {repo_name}"""
    
    print(f"Initializing LTM integration for {repo_name}...")
    
    try:
        # Load integration configuration
        config_path = Path(__file__).parent / "integration_config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Initialize LTM bridge
        bridge = {repo_name.replace("-", "").title()}LTMBridge(
            ltm_server_url=config["ltm_server_url"]
        )
        
        await bridge.initialize()
        
        print("✓ LTM integration initialized successfully")
        print(f"✓ Connected to LTM server at {{config['ltm_server_url']}}")
        print("✓ Ready to enhance {repo_name} with LTM capabilities")
        
        return bridge
        
    except Exception as e:
        print(f"✗ LTM integration initialization failed: {{e}}")
        raise

async def test_ltm_integration():
    """Test LTM integration functionality"""
    
    print("Testing LTM integration...")
    
    bridge = await initialize_ltm_integration()
    
    # Test basic LTM functionality
    if hasattr(bridge, 'ltm_client'):
        stats = await bridge.ltm_client.get_session_stats()
        print(f"✓ LTM session active: {{stats['conversation_active']}}")
        print(f"✓ LTM mode: {{stats['mode']}}")
    
    print("✓ LTM integration test completed")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description=f"Initialize LTM integration for {repo_name}")
    parser.add_argument("--test", action="store_true", help="Run integration tests")
    
    args = parser.parse_args()
    
    if args.test:
        asyncio.run(test_ltm_integration())
    else:
        asyncio.run(initialize_ltm_integration())
'''

    def modify_existing_files(self, repo_name: str, repo_path: str) -> bool:
        """Modify existing files to integrate with LTM (minimal changes)"""
        try:
            # Create a integration wrapper instead of modifying original files
            wrapper_file = os.path.join(repo_path, f"ltm_enhanced_{repo_name.replace('-', '_')}.py")
            
            wrapper_content = f'''#!/usr/bin/env python3
# LTM Enhanced wrapper for {repo_name}
# This file provides LTM integration without modifying original source code

import asyncio
import sys
import os
from pathlib import Path

# Add current directory to path for original imports
sys.path.insert(0, str(Path(__file__).parent))

# Import LTM integration
from ltm_integration.ltm_bridge import {repo_name.replace("-", "").title()}LTMBridge

class LTMEnhanced{repo_name.replace("-", "").title()}:
    """LTM Enhanced version of {repo_name}"""
    
    def __init__(self):
        self.ltm_bridge = None
        self.original_functionality = None
        
    async def initialize(self):
        """Initialize both original functionality and LTM integration"""
        
        # Initialize LTM bridge
        self.ltm_bridge = {repo_name.replace("-", "").title()}LTMBridge()
        await self.ltm_bridge.initialize()
        
        # Initialize original functionality
        # TODO: Import and initialize your original main class/functions here
        print("Original {repo_name} functionality initialized")
        
        print("✓ LTM Enhanced {repo_name} ready")
        
    async def run(self):
        """Run the enhanced version with LTM integration"""
        await self.initialize()
        
        # Your main application loop here
        print("Running LTM Enhanced {repo_name}...")
        
        # Keep running (customize based on your application)
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down LTM Enhanced {repo_name}...")

if __name__ == "__main__":
    enhanced_app = LTMEnhanced{repo_name.replace("-", "").title()}()
    asyncio.run(enhanced_app.run())
'''
            
            with open(wrapper_file, 'w') as f:
                f.write(wrapper_content)
            
            # Make it executable
            os.chmod(wrapper_file, 0o755)
            
            logger.info(f"✓ Created LTM enhanced wrapper for {repo_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create wrapper for {repo_name}: {e}")
            return False

    def create_requirements_file(self, repo_path: str):
        """Create requirements.txt for LTM integration"""
        requirements_content = """# LTM Integration Requirements
aiohttp>=3.8.0
asyncio-mqtt>=0.11.0
fastapi>=0.68.0
uvicorn>=0.15.0
pydantic>=1.8.0
python-jose>=3.3.0
python-multipart>=0.0.5
aioredis>=2.0.0
asyncpg>=0.24.0
cryptography>=3.4.0
prometheus-client>=0.11.0
psutil>=5.8.0
neo4j>=4.3.0
pymilvus>=2.0.0
sentence-transformers>=2.0.0
numpy>=1.21.0
"""
        
        requirements_path = os.path.join(repo_path, "ltm_integration", "requirements.txt")
        with open(requirements_path, 'w') as f:
            f.write(requirements_content)
            
        logger.info(f"✓ Created requirements file at {requirements_path}")

    def create_docker_integration(self, repo_path: str, repo_name: str):
        """Create Docker integration files"""
        dockerfile_content = f'''# Dockerfile.ltm-integration
# Docker integration for {repo_name} with LTM platform

FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy LTM integration requirements
COPY ltm_integration/requirements.txt /app/ltm_integration/requirements.txt

# Install Python dependencies
RUN pip install -r ltm_integration/requirements.txt

# Copy application code
COPY . /app/

# Make integration script executable
RUN chmod +x ltm_integration/initialize_ltm.py

# Expose any necessary ports
EXPOSE 8000

# Default command
CMD ["python", "ltm_enhanced_{repo_name.replace('-', '_')}.py"]
'''
        
        dockerfile_path = os.path.join(repo_path, "Dockerfile.ltm-integration")
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
            
        # Create docker-compose integration
        compose_content = f'''version: '3.8'

services:
  {repo_name.replace('-', '_')}-ltm:
    build:
      context: .
      dockerfile: Dockerfile.ltm-integration
    environment:
      - LTM_SERVER_URL=http://ltm-platform:8000
      - NEO4J_URI=bolt://neo4j:7687
      - REDIS_URL=redis://redis:6379
    depends_on:
      - ltm-platform
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config
    networks:
      - ltm-network

networks:
  ltm-network:
    external: true
'''
        
        compose_path = os.path.join(repo_path, "docker-compose.ltm.yml")
        with open(compose_path, 'w') as f:
            f.write(compose_content)
            
        logger.info(f"✓ Created Docker integration files for {repo_name}")

    async def setup_repository_integration(self, repo_name: str, repo_path: str, backup: bool = True) -> bool:
        """Set up complete integration for a repository"""
        logger.info(f"Setting up LTM integration for {repo_name} at {repo_path}")
        
        try:
            # Create backup if requested
            if backup:
                self.backup_repository(repo_path)
            
            # Create integration files
            if not self.create_integration_files(repo_name, repo_path):
                return False
            
            # Create enhanced wrapper
            if not self.modify_existing_files(repo_name, repo_path):
                return False
            
            # Create requirements file
            self.create_requirements_file(repo_path)
            
            # Create Docker integration
            self.create_docker_integration(repo_path, repo_name)
            
            # Create integration documentation
            self.create_integration_docs(repo_path, repo_name)
            
            logger.info(f"✓ LTM integration setup completed for {repo_name}")
            return True
            
        except Exception as e:
            logger.error(f"Integration setup failed for {repo_name}: {e}")
            return False

    def create_integration_docs(self, repo_path: str, repo_name: str):
        """Create integration documentation"""
        docs_dir = os.path.join(repo_path, "ltm_integration", "docs")
        os.makedirs(docs_dir, exist_ok=True)
        
        readme_content = f'''# LTM Integration for {repo_name}

This directory contains the LTM (Long Term Memory) integration for {repo_name}.

## Quick Start

1. **Initialize LTM Integration**:
   ```bash
   python ltm_integration/initialize_ltm.py
   ```

2. **Run Enhanced Version**:
   ```bash
   python ltm_enhanced_{repo_name.replace('-', '_')}.py
   ```

3. **Test Integration**:
   ```bash
   python ltm_integration/initialize_ltm.py --test
   ```

## Files

- `ltm_bridge.py` - Main integration bridge
- `initialize_ltm.py` - Initialization script
- `integration_config.json` - Configuration file
- `requirements.txt` - Python dependencies

## Docker Integration

Start with Docker Compose:

```bash
docker-compose -f docker-compose.ltm.yml up
```

## Configuration

Edit `integration_config.json` to customize:

- LTM server URL
- Learning preferences
- Feature toggles

## Integration Features

- **Memory Learning**: Activities are recorded in LTM
- **Intelligent Insights**: Historical patterns enhance current operations
- **Knowledge Graph**: Network topology and relationships (if enabled)
- **Performance Monitoring**: System metrics and alerts
- **Security Integration**: Audit logging and compliance (if enabled)

## Troubleshooting

1. **LTM Connection Issues**:
   ```bash
   curl -X GET "http://localhost:8000/health"
   ```

2. **Check Integration Status**:
   ```bash
   python ltm_integration/initialize_ltm.py --test
   ```

3. **View Logs**:
   ```bash
   tail -f logs/ltm_integration.log
   ```

For more information, see the main LTM platform documentation.
'''
        
        readme_path = os.path.join(docs_dir, "README.md")
        with open(readme_path, 'w') as f:
            f.write(readme_content)
            
        logger.info(f"✓ Created integration documentation for {repo_name}")

    async def run_integration_setup(self, repositories: Dict[str, str] = None, 
                                  create_backup: bool = True, interactive: bool = False) -> Dict[str, bool]:
        """Run complete integration setup"""
        results = {}
        
        if repositories is None:
            repositories = self.scan_for_repositories()
        
        if not repositories:
            logger.warning("No repositories found for integration")
            return results
        
        logger.info(f"Found {len(repositories)} repositories for integration")
        
        for repo_name, repo_path in repositories.items():
            if interactive:
                response = input(f"Integrate {repo_name} at {repo_path}? (y/n/s=skip): ").lower()
                if response in ['n', 'no']:
                    continue
                elif response in ['s', 'skip']:
                    results[repo_name] = False
                    continue
            
            logger.info(f"Integrating {repo_name}...")
            success = await self.setup_repository_integration(repo_name, repo_path, create_backup)
            results[repo_name] = success
            
            if success:
                logger.info(f"✓ {repo_name} integration completed")
            else:
                logger.error(f"✗ {repo_name} integration failed")
        
        return results

    def generate_master_integration_config(self, results: Dict[str, bool]):
        """Generate master integration configuration for LTM platform"""
        config = {
            "integrations": {
                "existing_repositories": {}
            }
        }
        
        for repo_name, success in results.items():
            if success:
                # Find the repository path
                found_repos = self.scan_for_repositories()
                repo_path = found_repos.get(repo_name, f"../{repo_name}")
                
                config["integrations"]["existing_repositories"][repo_name.replace("-", "_")] = {
                    "path": repo_path,
                    "integration_mode": self.repositories[repo_name]["integration_mode"],
                    "status": "integrated",
                    "ltm_enhanced_wrapper": f"{repo_path}/ltm_enhanced_{repo_name.replace('-', '_')}.py"
                }
        
        # Save to LTM platform config
        platform_config_path = self.base_path / "config" / "integration_config.json"
        platform_config_path.parent.mkdir(exist_ok=True)
        
        with open(platform_config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"✓ Master integration config saved to {platform_config_path}")
        return config

async def main():
    parser = argparse.ArgumentParser(description="LTM Platform Integration Setup")
    parser.add_argument("--scan-paths", nargs="+", help="Paths to scan for repositories")
    parser.add_argument("--repositories", nargs="+", help="Specific repository paths to integrate")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating backups")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    
    args = parser.parse_args()
    
    setup = LTMIntegrationSetup()
    
    if args.dry_run:
        logger.info("DRY RUN - No changes will be made")
        found_repos = setup.scan_for_repositories(args.scan_paths)
        print("\nRepositories found for integration:")
        for repo_name, repo_path in found_repos.items():
            print(f"  {repo_name}: {repo_path}")
        return
    
    # Scan or use provided repositories
    if args.repositories:
        repositories = {}
        for repo_path in args.repositories:
            # Try to determine repository name from path
            repo_name = os.path.basename(repo_path)
            if repo_name in setup.repositories:
                repositories[repo_name] = repo_path
    else:
        repositories = setup.scan_for_repositories(args.scan_paths)
    
    if not repositories:
        logger.error("No repositories found or specified for integration")
        sys.exit(1)
    
    # Run integration setup
    results = await setup.run_integration_setup(
        repositories=repositories,
        create_backup=not args.no_backup,
        interactive=args.interactive
    )
    
    # Generate master config
    master_config = setup.generate_master_integration_config(results)
    
    # Print results
    print("\n" + "="*60)
    print("INTEGRATION SETUP RESULTS")
    print("="*60)
    
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    
    print(f"Successfully integrated: {successful}/{total} repositories")
    print()
    
    for repo_name, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  {repo_name}: {status}")
    
    print("\nNext Steps:")
    print("1. Review integration configurations in each repository")
    print("2. Test integrations: python ltm_integration/initialize_ltm.py --test")
    print("3. Start LTM platform: python unified_network_intelligence.py")
    print("4. Run enhanced repositories using ltm_enhanced_*.py scripts")
    
    if successful > 0:
        print(f"\n✓ Master integration config saved to config/integration_config.json")

if __name__ == "__main__":
    asyncio.run(main())