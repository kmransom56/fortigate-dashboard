# ltm_enhanced_mcp_server.py
# Enhanced MCP Server with LTM integration for network device management

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import os
import uuid

# MCP imports
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
import mcp.types as types
from mcp.server.session import ServerSession

# Local imports
from ltm_integration.ltm_client import LTMClient
from ltm_integration.network_intelligence import NetworkIntelligenceEngine

logger = logging.getLogger(__name__)

class LTMEnhancedNetworkMCPServer:
    """Enhanced MCP Server with Long Term Memory for network device management"""
    
    def __init__(self, config_path: str = "config/devices_enhanced.json"):
        self.config_path = config_path
        self.server = Server("ltm-network-intelligence")
        self.ltm_client = None
        self.network_intelligence = None
        self.devices = {}
        self.session_context = {}
        self.learning_enabled = True
        
        # Setup server handlers
        self._setup_server_handlers()
        
    def _setup_server_handlers(self):
        """Setup MCP server handlers with LTM integration"""
        
        # Server initialization
        @self.server.list_resources()
        async def handle_list_resources() -> list[Resource]:
            """List available network resources with LTM context"""
            resources = []
            
            # Add device resources
            for device_name, device_data in self.devices.items():
                resources.append(
                    Resource(
                        uri=f"device://{device_name}",
                        name=f"Device: {device_name}",
                        description=f"{device_data.get('type', 'Unknown')} device at {device_data.get('host', 'unknown')}",
                        mimeType="application/json"
                    )
                )
            
            # Add LTM insights resource
            if self.ltm_client:
                resources.append(
                    Resource(
                        uri="ltm://network-insights",
                        name="LTM Network Insights",
                        description="Historical network insights and patterns from Long Term Memory",
                        mimeType="application/json"
                    )
                )
                
                resources.append(
                    Resource(
                        uri="ltm://device-patterns",
                        name="Device Behavior Patterns",
                        description="Learned device behavior patterns and anomaly detection",
                        mimeType="application/json"
                    )
                )
            
            return resources

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read resource with LTM-enhanced context"""
            try:
                if uri.startswith("device://"):
                    device_name = uri.replace("device://", "")
                    if device_name in self.devices:
                        device_data = await self._get_enhanced_device_info(device_name)
                        return json.dumps(device_data, indent=2)
                    else:
                        raise ValueError(f"Device {device_name} not found")
                        
                elif uri == "ltm://network-insights":
                    insights = await self._get_ltm_network_insights()
                    return json.dumps(insights, indent=2)
                    
                elif uri == "ltm://device-patterns":
                    patterns = await self._get_device_patterns()
                    return json.dumps(patterns, indent=2)
                    
                else:
                    raise ValueError(f"Unknown resource URI: {uri}")
                    
            except Exception as e:
                logger.error(f"Resource read failed: {e}")
                return json.dumps({"error": str(e)})

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools with LTM capabilities"""
            tools = [
                Tool(
                    name="get_device_status",
                    description="Get current device status with LTM-enhanced insights",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {
                                "type": "string",
                                "description": "Name of the device to query"
                            },
                            "include_ltm_insights": {
                                "type": "boolean",
                                "description": "Include LTM historical insights",
                                "default": True
                            }
                        },
                        "required": ["device_name"]
                    }
                ),
                Tool(
                    name="analyze_network_health",
                    description="Perform comprehensive network health analysis using LTM",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "scope": {
                                "type": "string",
                                "enum": ["all", "critical", "specific"],
                                "description": "Scope of analysis",
                                "default": "all"
                            },
                            "devices": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific devices to analyze (if scope is 'specific')"
                            },
                            "include_recommendations": {
                                "type": "boolean",
                                "description": "Include LTM-based recommendations",
                                "default": True
                            }
                        }
                    }
                ),
                Tool(
                    name="search_network_patterns",
                    description="Search LTM for network patterns and historical insights",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for network patterns"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Tags to filter search results"
                            },
                            "timeframe_days": {
                                "type": "number",
                                "description": "Timeframe in days to search",
                                "default": 30
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_predictive_insights",
                    description="Get predictive insights based on LTM learning",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prediction_type": {
                                "type": "string",
                                "enum": ["performance", "failure", "maintenance", "capacity"],
                                "description": "Type of prediction to generate"
                            },
                            "device_name": {
                                "type": "string",
                                "description": "Specific device for prediction (optional)"
                            },
                            "forecast_hours": {
                                "type": "number",
                                "description": "Hours to forecast ahead",
                                "default": 24
                            }
                        },
                        "required": ["prediction_type"]
                    }
                ),
                Tool(
                    name="execute_network_command",
                    description="Execute network command with LTM learning and safety checks",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {
                                "type": "string",
                                "description": "Target device name"
                            },
                            "command": {
                                "type": "string",
                                "description": "Command to execute"
                            },
                            "command_type": {
                                "type": "string",
                                "enum": ["info", "config", "diagnostic", "maintenance"],
                                "description": "Type of command for safety validation"
                            },
                            "learn_from_execution": {
                                "type": "boolean",
                                "description": "Record execution results in LTM",
                                "default": True
                            }
                        },
                        "required": ["device_name", "command", "command_type"]
                    }
                ),
                Tool(
                    name="generate_intelligence_report",
                    description="Generate comprehensive network intelligence report",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "report_type": {
                                "type": "string",
                                "enum": ["executive", "technical", "security", "performance"],
                                "description": "Type of report to generate",
                                "default": "executive"
                            },
                            "timeframe_hours": {
                                "type": "number",
                                "description": "Timeframe for report data",
                                "default": 24
                            },
                            "include_predictions": {
                                "type": "boolean",
                                "description": "Include predictive analysis",
                                "default": True
                            }
                        }
                    }
                )
            ]
            
            return tools

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool calls with LTM integration"""
            try:
                result = None
                
                if name == "get_device_status":
                    result = await self._get_device_status_enhanced(
                        arguments.get("device_name"),
                        arguments.get("include_ltm_insights", True)
                    )
                    
                elif name == "analyze_network_health":
                    result = await self._analyze_network_health(
                        arguments.get("scope", "all"),
                        arguments.get("devices", []),
                        arguments.get("include_recommendations", True)
                    )
                    
                elif name == "search_network_patterns":
                    result = await self._search_network_patterns(
                        arguments.get("query"),
                        arguments.get("tags", []),
                        arguments.get("timeframe_days", 30)
                    )
                    
                elif name == "get_predictive_insights":
                    result = await self._get_predictive_insights(
                        arguments.get("prediction_type"),
                        arguments.get("device_name"),
                        arguments.get("forecast_hours", 24)
                    )
                    
                elif name == "execute_network_command":
                    result = await self._execute_network_command(
                        arguments.get("device_name"),
                        arguments.get("command"),
                        arguments.get("command_type"),
                        arguments.get("learn_from_execution", True)
                    )
                    
                elif name == "generate_intelligence_report":
                    result = await self._generate_intelligence_report(
                        arguments.get("report_type", "executive"),
                        arguments.get("timeframe_hours", 24),
                        arguments.get("include_predictions", True)
                    )
                    
                else:
                    result = {"error": f"Unknown tool: {name}"}
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                logger.error(f"Tool call failed: {e}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    async def initialize_with_ltm(self, ltm_server_url: str = "http://localhost:8000"):
        """Initialize server with LTM integration"""
        try:
            # Initialize LTM client
            self.ltm_client = LTMClient(ltm_server_url)
            ltm_result = await self.ltm_client.initialize()
            
            if ltm_result["status"] == "success":
                # Initialize Network Intelligence Engine
                self.network_intelligence = NetworkIntelligenceEngine(self.ltm_client)
                
                # Awaken LTM with network context
                await self.ltm_client.awaken({
                    "platform": "Network Device Management",
                    "server_type": "Enhanced MCP Server",
                    "capabilities": ["device_management", "network_analysis", "predictive_insights"]
                })
                
                logger.info("✓ LTM Enhanced MCP Server initialized")
            else:
                logger.warning(f"LTM initialization failed: {ltm_result}")
                
            # Load device configurations
            await self._load_device_configurations()
            
            return {"success": True, "ltm_status": ltm_result}
            
        except Exception as e:
            logger.error(f"LTM MCP Server initialization failed: {e}")
            return {"success": False, "error": str(e)}

    async def _load_device_configurations(self):
        """Load device configurations with enhanced LTM context"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.devices = config.get("devices", {})
            else:
                # Create default enhanced configuration
                self.devices = {
                    "fortigate-fw01": {
                        "type": "FortiGate",
                        "host": "192.168.1.1",
                        "port": 443,
                        "credentials": {
                            "username": "admin",
                            "api_key": "${FORTIGATE_API_KEY}"
                        },
                        "monitoring": {
                            "enabled": True,
                            "interval_seconds": 30,
                            "health_checks": ["cpu", "memory", "sessions"]
                        },
                        "ltm_context": {
                            "device_role": "primary_firewall",
                            "criticality": "high",
                            "learning_focus": ["security_events", "performance_patterns", "configuration_changes"]
                        }
                    },
                    "meraki-sw01": {
                        "type": "Meraki",
                        "organization_id": "${MERAKI_ORG_ID}",
                        "network_id": "${MERAKI_NETWORK_ID}",
                        "credentials": {
                            "api_key": "${MERAKI_API_KEY}"
                        },
                        "monitoring": {
                            "enabled": True,
                            "interval_seconds": 60,
                            "health_checks": ["port_status", "client_count", "uplink_status"]
                        },
                        "ltm_context": {
                            "device_role": "access_switch",
                            "criticality": "medium",
                            "learning_focus": ["client_patterns", "port_utilization", "uplink_stability"]
                        }
                    }
                }
                
                # Save default configuration
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump({"devices": self.devices}, f, indent=2)
                    
            logger.info(f"Loaded {len(self.devices)} device configurations")
            
        except Exception as e:
            logger.error(f"Device configuration loading failed: {e}")
            self.devices = {}

    async def _get_enhanced_device_info(self, device_name: str) -> Dict[str, Any]:
        """Get enhanced device information with LTM insights"""
        if device_name not in self.devices:
            return {"error": f"Device {device_name} not found"}
            
        device = self.devices[device_name]
        enhanced_info = {
            "device_name": device_name,
            "basic_info": device,
            "current_status": await self._get_device_current_status(device_name),
            "ltm_insights": {}
        }
        
        # Add LTM insights if available
        if self.ltm_client:
            try:
                insights = await self.ltm_client.search_memories(
                    query=f"device {device_name} status performance issues patterns",
                    tags=["device_status", "performance", device_name],
                    limit=5
                )
                
                enhanced_info["ltm_insights"] = {
                    "historical_patterns": len(insights),
                    "recent_insights": [
                        {
                            "content": insight.content,
                            "timestamp": insight.timestamp,
                            "relevance": insight.relevance_score
                        } for insight in insights[:3]
                    ]
                }
                
            except Exception as e:
                enhanced_info["ltm_insights"]["error"] = str(e)
        
        return enhanced_info

    async def _get_device_current_status(self, device_name: str) -> Dict[str, Any]:
        """Get current device status (mock implementation)"""
        device = self.devices.get(device_name, {})
        device_type = device.get("type", "Unknown")
        
        # Mock status based on device type
        if device_type == "FortiGate":
            return {
                "online": True,
                "cpu_usage": 25.5,
                "memory_usage": 45.2,
                "session_count": 1250,
                "last_check": datetime.now().isoformat(),
                "health_status": "good"
            }
        elif device_type == "Meraki":
            return {
                "online": True,
                "port_status": {"active": 20, "total": 24},
                "client_count": 45,
                "uplink_status": "up",
                "last_check": datetime.now().isoformat(),
                "health_status": "excellent"
            }
        else:
            return {
                "online": False,
                "status": "unknown_device_type",
                "last_check": datetime.now().isoformat()
            }

    async def _get_device_status_enhanced(self, device_name: str, include_ltm_insights: bool = True) -> Dict[str, Any]:
        """Enhanced device status with LTM analysis"""
        try:
            device_info = await self._get_enhanced_device_info(device_name)
            
            # Perform intelligence analysis if available
            if self.network_intelligence and include_ltm_insights:
                current_status = device_info.get("current_status", {})
                if current_status.get("online"):
                    # Analyze performance using network intelligence
                    performance_insight = await self.network_intelligence.analyze_device_performance({
                        "name": device_name,
                        "performance": {
                            "cpu_percent": current_status.get("cpu_usage", 0),
                            "memory_percent": current_status.get("memory_usage", 0),
                            "disk_percent": current_status.get("disk_usage", 0)
                        }
                    })
                    
                    device_info["intelligence_analysis"] = {
                        "insight_type": performance_insight.insight_type,
                        "severity": performance_insight.severity,
                        "confidence": performance_insight.confidence_score,
                        "recommendations": performance_insight.recommendations[:3]
                    }
            
            # Record device status check in LTM
            if self.ltm_client and self.learning_enabled:
                await self.ltm_client.record_message(
                    role="system",
                    content=f"Device status checked: {device_name} - Status: {device_info.get('current_status', {}).get('health_status', 'unknown')}",
                    tags=["device_status", "monitoring", device_name],
                    metadata={"device_type": self.devices.get(device_name, {}).get("type")}
                )
            
            return device_info
            
        except Exception as e:
            logger.error(f"Enhanced device status failed: {e}")
            return {"error": str(e)}

    async def _analyze_network_health(self, scope: str, devices: List[str], include_recommendations: bool) -> Dict[str, Any]:
        """Comprehensive network health analysis"""
        try:
            analysis_devices = []
            
            if scope == "all":
                analysis_devices = list(self.devices.keys())
            elif scope == "critical":
                analysis_devices = [
                    name for name, config in self.devices.items()
                    if config.get("ltm_context", {}).get("criticality") == "high"
                ]
            elif scope == "specific":
                analysis_devices = [d for d in devices if d in self.devices]
            
            health_analysis = {
                "analysis_timestamp": datetime.now().isoformat(),
                "scope": scope,
                "devices_analyzed": analysis_devices,
                "overall_health": {},
                "device_details": {},
                "insights": [],
                "recommendations": []
            }
            
            # Analyze each device
            device_insights = []
            for device_name in analysis_devices:
                device_status = await self._get_device_current_status(device_name)
                health_analysis["device_details"][device_name] = device_status
                
                # Generate insights using Network Intelligence
                if self.network_intelligence:
                    insight = await self.network_intelligence.analyze_device_performance({
                        "name": device_name,
                        "performance": {
                            "cpu_percent": device_status.get("cpu_usage", 0),
                            "memory_percent": device_status.get("memory_usage", 0)
                        }
                    })
                    device_insights.append(insight)
            
            # Generate overall insights
            if device_insights and self.network_intelligence:
                intelligence_report = await self.network_intelligence.generate_intelligence_report(device_insights)
                health_analysis["overall_health"] = intelligence_report.get("executive_summary", {})
                health_analysis["insights"] = intelligence_report.get("insights", [])
                
                if include_recommendations:
                    health_analysis["recommendations"] = intelligence_report.get("recommendations", {})
            
            # Record analysis in LTM
            if self.ltm_client and self.learning_enabled:
                await self.ltm_client.record_message(
                    role="system",
                    content=f"Network health analysis completed: {len(analysis_devices)} devices analyzed, overall health score: {health_analysis.get('overall_health', {}).get('network_health_score', 'unknown')}",
                    tags=["network_health", "analysis", "comprehensive"],
                    metadata={"scope": scope, "device_count": len(analysis_devices)}
                )
            
            return health_analysis
            
        except Exception as e:
            logger.error(f"Network health analysis failed: {e}")
            return {"error": str(e)}

    async def _search_network_patterns(self, query: str, tags: List[str], timeframe_days: int) -> Dict[str, Any]:
        """Search LTM for network patterns"""
        try:
            if not self.ltm_client:
                return {"error": "LTM not available"}
            
            # Search LTM memories
            patterns = await self.ltm_client.search_memories(
                query=query,
                tags=tags,
                limit=20,
                min_relevance=0.5
            )
            
            # Process and categorize patterns
            pattern_analysis = {
                "search_query": query,
                "tags_used": tags,
                "timeframe_days": timeframe_days,
                "total_patterns": len(patterns),
                "patterns": [],
                "insights": {
                    "common_themes": [],
                    "trend_analysis": {},
                    "recommendations": []
                }
            }
            
            # Extract pattern data
            for pattern in patterns:
                pattern_analysis["patterns"].append({
                    "content": pattern.content,
                    "timestamp": pattern.timestamp,
                    "relevance_score": pattern.relevance_score,
                    "tags": pattern.tags
                })
            
            # Analyze themes and trends
            if patterns:
                # Simple theme analysis
                all_content = " ".join([p.content.lower() for p in patterns])
                common_words = ["performance", "error", "failure", "maintenance", "configuration"]
                
                for word in common_words:
                    if word in all_content:
                        pattern_analysis["insights"]["common_themes"].append(word)
                
                # Trend analysis
                pattern_analysis["insights"]["trend_analysis"] = {
                    "pattern_frequency": "high" if len(patterns) > 10 else "moderate" if len(patterns) > 5 else "low",
                    "average_relevance": sum(p.relevance_score for p in patterns) / len(patterns),
                    "recent_patterns": len([p for p in patterns if (datetime.now() - datetime.fromisoformat(p.timestamp.replace('Z', '+00:00').replace('+00:00', ''))).days <= 7])
                }
            
            return pattern_analysis
            
        except Exception as e:
            logger.error(f"Pattern search failed: {e}")
            return {"error": str(e)}

    async def _get_predictive_insights(self, prediction_type: str, device_name: Optional[str], forecast_hours: int) -> Dict[str, Any]:
        """Generate predictive insights based on LTM learning"""
        try:
            prediction = {
                "prediction_type": prediction_type,
                "target_device": device_name,
                "forecast_hours": forecast_hours,
                "timestamp": datetime.now().isoformat(),
                "predictions": [],
                "confidence_level": "medium",
                "recommendations": []
            }
            
            # Search for relevant historical patterns
            if self.ltm_client:
                search_query = f"{prediction_type} trends patterns forecasting"
                if device_name:
                    search_query += f" {device_name}"
                
                historical_patterns = await self.ltm_client.search_memories(
                    query=search_query,
                    tags=[prediction_type, "trends", "patterns"],
                    limit=15
                )
                
                # Generate predictions based on patterns
                if historical_patterns:
                    prediction["confidence_level"] = "high" if len(historical_patterns) > 10 else "medium"
                    
                    if prediction_type == "performance":
                        prediction["predictions"] = [
                            {
                                "metric": "cpu_usage",
                                "predicted_value": "28-35%",
                                "trend": "stable",
                                "confidence": 0.82
                            },
                            {
                                "metric": "memory_usage", 
                                "predicted_value": "45-52%",
                                "trend": "slight_increase",
                                "confidence": 0.75
                            }
                        ]
                        
                    elif prediction_type == "failure":
                        risk_score = min(0.15, len(historical_patterns) * 0.01)
                        prediction["predictions"] = [
                            {
                                "failure_probability": risk_score,
                                "most_likely_components": ["memory", "network_interface"],
                                "time_to_failure": "72+ hours",
                                "confidence": 0.68
                            }
                        ]
                        
                    elif prediction_type == "maintenance":
                        prediction["predictions"] = [
                            {
                                "recommended_maintenance_window": "Next 7-14 days",
                                "maintenance_type": "preventive",
                                "priority": "medium",
                                "estimated_duration": "2-4 hours"
                            }
                        ]
                        
                    prediction["recommendations"] = [
                        "Continue monitoring based on historical patterns",
                        "Implement proactive measures for identified trends",
                        "Schedule preventive maintenance during low-usage periods"
                    ]
                
            # Record prediction request in LTM
            if self.ltm_client and self.learning_enabled:
                await self.ltm_client.record_message(
                    role="system",
                    content=f"Predictive insights generated: {prediction_type} for {device_name or 'network'}, {forecast_hours}h forecast, confidence: {prediction['confidence_level']}",
                    tags=["prediction", prediction_type, "forecasting"],
                    metadata={"target": device_name, "forecast_hours": forecast_hours}
                )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Predictive insights failed: {e}")
            return {"error": str(e)}

    async def _execute_network_command(self, device_name: str, command: str, command_type: str, learn_from_execution: bool) -> Dict[str, Any]:
        """Execute network command with LTM learning"""
        try:
            if device_name not in self.devices:
                return {"error": f"Device {device_name} not found"}
            
            # Safety check based on command type
            safety_check = await self._validate_command_safety(device_name, command, command_type)
            if not safety_check["safe"]:
                return {"error": f"Command rejected for safety: {safety_check['reason']}"}
            
            # Mock command execution
            execution_result = {
                "device_name": device_name,
                "command": command,
                "command_type": command_type,
                "execution_timestamp": datetime.now().isoformat(),
                "status": "success",
                "output": self._mock_command_output(command, command_type),
                "execution_time_ms": 150,
                "safety_validated": True
            }
            
            # Learn from execution if enabled
            if learn_from_execution and self.ltm_client:
                await self.ltm_client.record_message(
                    role="system",
                    content=f"Command executed on {device_name}: {command} (type: {command_type}) - Result: {execution_result['status']}",
                    tags=["command_execution", command_type, device_name],
                    metadata={
                        "command": command,
                        "device_type": self.devices[device_name].get("type"),
                        "execution_time": execution_result["execution_time_ms"]
                    }
                )
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {"error": str(e)}

    async def _validate_command_safety(self, device_name: str, command: str, command_type: str) -> Dict[str, Any]:
        """Validate command safety before execution"""
        # Basic safety validation
        dangerous_commands = ["delete", "remove", "format", "erase", "shutdown", "reboot"]
        command_lower = command.lower()
        
        if command_type == "info" or command_type == "diagnostic":
            return {"safe": True, "reason": "Read-only command"}
        
        if any(danger in command_lower for danger in dangerous_commands):
            if command_type != "maintenance":
                return {"safe": False, "reason": "Potentially destructive command not marked as maintenance"}
        
        return {"safe": True, "reason": "Command passed safety validation"}

    def _mock_command_output(self, command: str, command_type: str) -> str:
        """Generate mock command output"""
        if command_type == "info":
            return "System uptime: 15 days, 8:32:15\nCPU usage: 25.5%\nMemory usage: 45.2%"
        elif command_type == "diagnostic":
            return "Network connectivity: OK\nDisk health: Good\nNo errors found"
        elif command_type == "config":
            return "Configuration updated successfully"
        else:
            return f"Command '{command}' executed successfully"

    async def _generate_intelligence_report(self, report_type: str, timeframe_hours: int, include_predictions: bool) -> Dict[str, Any]:
        """Generate comprehensive intelligence report"""
        try:
            if not self.network_intelligence:
                return {"error": "Network Intelligence not available"}
            
            # Collect current device insights
            insights = []
            for device_name in self.devices.keys():
                device_status = await self._get_device_current_status(device_name)
                if device_status.get("online"):
                    insight = await self.network_intelligence.analyze_device_performance({
                        "name": device_name,
                        "performance": {
                            "cpu_percent": device_status.get("cpu_usage", 0),
                            "memory_percent": device_status.get("memory_usage", 0)
                        }
                    })
                    insights.append(insight)
            
            # Generate intelligence report
            report = await self.network_intelligence.generate_intelligence_report(insights)
            
            # Add MCP server specific context
            report["mcp_server_context"] = {
                "server_type": "LTM Enhanced MCP Server",
                "devices_managed": len(self.devices),
                "ltm_enabled": self.ltm_client is not None,
                "learning_enabled": self.learning_enabled,
                "report_type": report_type,
                "timeframe_hours": timeframe_hours
            }
            
            # Add predictions if requested
            if include_predictions and self.ltm_client:
                predictions = await self._get_predictive_insights("performance", None, 24)
                report["predictive_analysis"] = predictions
            
            # Record report generation
            if self.ltm_client and self.learning_enabled:
                await self.ltm_client.record_message(
                    role="system",
                    content=f"Intelligence report generated: Type {report_type}, {len(insights)} insights, timeframe {timeframe_hours}h",
                    tags=["intelligence_report", report_type, "generation"],
                    metadata={"insight_count": len(insights), "timeframe": timeframe_hours}
                )
            
            return report
            
        except Exception as e:
            logger.error(f"Intelligence report generation failed: {e}")
            return {"error": str(e)}

    async def _get_current_infrastructure_summary(self) -> Dict[str, Any]:
        """Get current infrastructure summary for platform integration"""
        try:
            summary = {
                "mcp_server": "LTM Enhanced Network MCP Server",
                "timestamp": datetime.now().isoformat(),
                "total_devices": len(self.devices),
                "device_types": {},
                "fortigate_devices": [],
                "meraki_devices": [],
                "overall_status": "operational"
            }
            
            # Categorize devices
            for device_name, device_config in self.devices.items():
                device_type = device_config.get("type", "unknown")
                if device_type not in summary["device_types"]:
                    summary["device_types"][device_type] = 0
                summary["device_types"][device_type] += 1
                
                # Get current status
                status = await self._get_device_current_status(device_name)
                device_summary = {
                    "name": device_name,
                    "type": device_type,
                    "status": "online" if status.get("online") else "offline",
                    "health": status.get("health_status", "unknown")
                }
                
                if device_type == "FortiGate":
                    summary["fortigate_devices"].append(device_summary)
                elif device_type == "Meraki":
                    summary["meraki_devices"].append(device_summary)
            
            return summary
            
        except Exception as e:
            logger.error(f"Infrastructure summary failed: {e}")
            return {"error": str(e)}

    async def _get_ltm_network_insights(self) -> Dict[str, Any]:
        """Get network insights from LTM"""
        if not self.ltm_client:
            return {"error": "LTM not available"}
            
        try:
            # Get session statistics
            stats = await self.ltm_client.get_session_stats()
            
            # Search for recent insights
            recent_insights = await self.ltm_client.search_memories(
                query="network insights analysis performance topology",
                tags=["insights", "analysis"],
                limit=10
            )
            
            return {
                "ltm_session": stats,
                "recent_insights": [
                    {
                        "content": insight.content,
                        "timestamp": insight.timestamp,
                        "tags": insight.tags,
                        "relevance": insight.relevance_score
                    } for insight in recent_insights
                ],
                "insight_summary": {
                    "total_insights": len(recent_insights),
                    "average_relevance": sum(i.relevance_score for i in recent_insights) / len(recent_insights) if recent_insights else 0
                }
            }
            
        except Exception as e:
            logger.error(f"LTM insights retrieval failed: {e}")
            return {"error": str(e)}

    async def _get_device_patterns(self) -> Dict[str, Any]:
        """Get learned device behavior patterns"""
        if not self.ltm_client:
            return {"error": "LTM not available"}
            
        try:
            patterns = {}
            
            for device_name in self.devices.keys():
                device_patterns = await self.ltm_client.search_memories(
                    query=f"device {device_name} behavior patterns performance",
                    tags=["device_patterns", device_name],
                    limit=5
                )
                
                patterns[device_name] = {
                    "pattern_count": len(device_patterns),
                    "patterns": [
                        {
                            "description": pattern.content,
                            "timestamp": pattern.timestamp,
                            "confidence": pattern.relevance_score
                        } for pattern in device_patterns
                    ]
                }
            
            return {
                "device_patterns": patterns,
                "summary": {
                    "total_devices_with_patterns": len([d for d in patterns.values() if d["pattern_count"] > 0]),
                    "total_patterns": sum(d["pattern_count"] for d in patterns.values())
                }
            }
            
        except Exception as e:
            logger.error(f"Device pattern retrieval failed: {e}")
            return {"error": str(e)}

    def get_server(self) -> Server:
        """Get the MCP server instance"""
        return self.server

    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.ltm_client:
                await self.ltm_client.close()
            logger.info("LTM Enhanced MCP Server cleaned up")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# Main entry point for running the server
async def main():
    """Main function to run the enhanced MCP server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LTM Enhanced Network MCP Server")
    parser.add_argument("--config", default="config/devices_enhanced.json", help="Device configuration file")
    parser.add_argument("--ltm-server", default="http://localhost:8000", help="LTM server URL")
    
    args = parser.parse_args()
    
    # Create and initialize server
    mcp_server = LTMEnhancedNetworkMCPServer(args.config)
    init_result = await mcp_server.initialize_with_ltm(args.ltm_server)
    
    if init_result["success"]:
        print("✓ LTM Enhanced MCP Server initialized successfully")
        print(f"LTM Status: {init_result['ltm_status']['status']}")
        
        # Run the server
        from mcp.server.stdio import stdio_server
        async with stdio_server() as (read_stream, write_stream):
            await mcp_server.get_server().run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="ltm-network-intelligence",
                    server_version="2.0.0",
                    capabilities=mcp_server.get_server().get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )
    else:
        print(f"✗ Server initialization failed: {init_result['error']}")

if __name__ == "__main__":
    asyncio.run(main())