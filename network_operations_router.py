"""
Unified Network Operations API Router
Integrates topology visualization, switch discovery, and OSI troubleshooting
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime
import asyncio

# Import our services
from topology_visualization import TopologyVisualizationService, NetworkNode, NetworkLink
from switch_discovery import SwitchDiscoveryService, ManagedSwitch
from osi_troubleshooting_integration import (
    OSITroubleshootingOrchestrator,
    FortiGateOSIIntegration,
    TroubleshootingIssue
)


router = APIRouter(prefix="/api/network", tags=["network"])


# ==================== Topology Endpoints ====================

@router.get("/topology/full")
async def get_full_topology():
    """Get complete network topology for visualization"""
    service = TopologyVisualizationService(
        neo4j_uri="bolt://neo4j:7687",
        neo4j_user="neo4j",
        neo4j_password="neo4j_password"
    )
    
    try:
        topology = await service.get_topology_graph()
        return JSONResponse(content=topology)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.get("/topology/device/{device_id}")
async def get_device_topology(device_id: str, depth: int = 2):
    """Get topology around a specific device"""
    service = TopologyVisualizationService(
        neo4j_uri="bolt://neo4j:7687",
        neo4j_user="neo4j",
        neo4j_password="neo4j_password"
    )
    
    try:
        neighbors = await service.get_device_neighbors(device_id, depth)
        return JSONResponse(content=neighbors)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.get("/topology/path/{source_id}/{target_id}")
async def get_network_path(source_id: str, target_id: str):
    """Find path between two devices"""
    service = TopologyVisualizationService(
        neo4j_uri="bolt://neo4j:7687",
        neo4j_user="neo4j",
        neo4j_password="neo4j_password"
    )
    
    try:
        path = await service.find_path(source_id, target_id)
        return JSONResponse(content=path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.post("/topology/rebuild")
async def rebuild_topology(background_tasks: BackgroundTasks):
    """Rebuild topology from FortiGate data (runs in background)"""
    async def rebuild_task():
        service = TopologyVisualizationService(
            neo4j_uri="bolt://neo4j:7687",
            neo4j_user="neo4j",
            neo4j_password="neo4j_password"
        )
        
        try:
            # Clear existing topology
            await service.clear_topology()
            
            # Get fresh FortiGate data
            # TODO: Replace with actual FortiGate API call
            fortigate_data = {
                "hostname": "FG-PRIMARY",
                "ip_address": "192.168.0.254",
                "model": "FortiGate-100F",
                "serial": "FG100F3G12345678",
                "switches": [],  # Populated from switch discovery
                "detected_devices": []
            }
            
            await service.build_topology_from_fortigate(fortigate_data)
        finally:
            await service.close()
    
    background_tasks.add_task(rebuild_task)
    return {"status": "rebuilding", "message": "Topology rebuild started in background"}


# ==================== Switch Discovery Endpoints ====================

@router.get("/switches")
async def get_all_switches():
    """Get all managed switches"""
    service = SwitchDiscoveryService(
        fortigate_host="192.168.0.254",
        fortigate_port=10443
    )
    
    try:
        switches = await service.discover_switches()
        return JSONResponse(content=[s.model_dump() for s in switches])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/switches/{switch_id}")
async def get_switch_details(switch_id: str):
    """Get detailed information for a specific switch"""
    service = SwitchDiscoveryService(
        fortigate_host="192.168.0.254",
        fortigate_port=10443
    )
    
    try:
        switches = await service.discover_switches()
        switch = next((s for s in switches if s.serial == switch_id), None)
        
        if not switch:
            raise HTTPException(status_code=404, detail="Switch not found")
        
        return JSONResponse(content=switch.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/switches/{switch_id}/health")
async def get_switch_health(switch_id: str):
    """Get health metrics for a specific switch"""
    service = SwitchDiscoveryService(
        fortigate_host="192.168.0.254",
        fortigate_port=10443
    )
    
    try:
        health = await service.monitor_switch_health(switch_id)
        return JSONResponse(content=health)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/switches/{switch_id}/configure")
async def configure_switch(switch_id: str, template: str = "standard"):
    """Auto-configure a switch using a template"""
    service = SwitchDiscoveryService(
        fortigate_host="192.168.0.254",
        fortigate_port=10443
    )
    
    try:
        result = await service.auto_configure_switch(switch_id, template)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/switches/report/summary")
async def get_switches_report():
    """Generate comprehensive switches report"""
    service = SwitchDiscoveryService(
        fortigate_host="192.168.0.254",
        fortigate_port=10443
    )
    
    try:
        switches = await service.discover_switches()
        report = await service.generate_switch_report(switches)
        return JSONResponse(content=report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security/rogue-devices")
async def scan_rogue_devices():
    """Scan for unauthorized devices on the network"""
    service = SwitchDiscoveryService(
        fortigate_host="192.168.0.254",
        fortigate_port=10443
    )
    
    try:
        rogues = await service.scan_for_rogue_devices()
        return JSONResponse(content={"count": len(rogues), "devices": rogues})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== OSI Troubleshooting Endpoints ====================

@router.get("/troubleshooting/analyze")
async def analyze_network_health():
    """Run OSI troubleshooting analysis on entire network"""
    orchestrator = OSITroubleshootingOrchestrator()
    integration = FortiGateOSIIntegration(orchestrator)
    
    try:
        # Get FortiGate and switch data
        switch_service = SwitchDiscoveryService(
            fortigate_host="192.168.0.254",
            fortigate_port=10443
        )
        
        switches = await switch_service.discover_switches()
        switches_data = [s.model_dump() for s in switches]
        
        fortigate_data = {
            "hostname": "FG-PRIMARY",
            "interfaces": [],
            "route_count": 150
        }
        
        # Run analysis
        result = await integration.analyze_fortigate_network(switches_data, fortigate_data)
        
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/troubleshooting/device/{device_id}")
async def analyze_device(device_id: str):
    """Run OSI troubleshooting on a specific device"""
    orchestrator = OSITroubleshootingOrchestrator()
    
    try:
        # Get device data
        switch_service = SwitchDiscoveryService(
            fortigate_host="192.168.0.254",
            fortigate_port=10443
        )
        
        switches = await switch_service.discover_switches()
        device = next((s for s in switches if s.serial == device_id), None)
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Analyze device
        issues = await orchestrator.analyze_device(device.model_dump())
        
        return JSONResponse(content={
            "device_id": device_id,
            "device_name": device.name,
            "issues": [issue.model_dump() for issue in issues]
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/troubleshooting/remediation-plan")
async def get_remediation_plan():
    """Get prioritized remediation plan for all issues"""
    orchestrator = OSITroubleshootingOrchestrator()
    integration = FortiGateOSIIntegration(orchestrator)
    
    try:
        # Get full analysis
        switch_service = SwitchDiscoveryService(
            fortigate_host="192.168.0.254",
            fortigate_port=10443
        )
        
        switches = await switch_service.discover_switches()
        switches_data = [s.model_dump() for s in switches]
        
        fortigate_data = {"hostname": "FG-PRIMARY", "interfaces": [], "route_count": 150}
        
        result = await integration.analyze_fortigate_network(switches_data, fortigate_data)
        
        return JSONResponse(content=result["remediation_plan"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Unified Dashboard Endpoints ====================

@router.get("/dashboard/overview")
async def get_dashboard_overview():
    """Get unified dashboard overview with all key metrics"""
    try:
        # Run all services in parallel
        switch_service = SwitchDiscoveryService(
            fortigate_host="192.168.0.254",
            fortigate_port=10443
        )
        
        topology_service = TopologyVisualizationService(
            neo4j_uri="bolt://neo4j:7687",
            neo4j_user="neo4j",
            neo4j_password="neo4j_password"
        )
        
        orchestrator = OSITroubleshootingOrchestrator()
        integration = FortiGateOSIIntegration(orchestrator)
        
        # Gather all data
        switches = await switch_service.discover_switches()
        report = await switch_service.generate_switch_report(switches)
        
        topology = await topology_service.get_topology_graph()
        health_analysis = await topology_service.analyze_network_health()
        
        fortigate_data = {"hostname": "FG-PRIMARY", "interfaces": [], "route_count": 150}
        osi_analysis = await integration.analyze_fortigate_network(
            [s.model_dump() for s in switches],
            fortigate_data
        )
        
        await topology_service.close()
        
        return JSONResponse(content={
            "timestamp": datetime.utcnow().isoformat(),
            "switches": report["summary"],
            "topology": {
                "node_count": topology["metadata"]["node_count"],
                "link_count": topology["metadata"]["link_count"]
            },
            "health": {
                "network_health": health_analysis,
                "osi_health": osi_analysis["health"]
            },
            "issues": {
                "total": osi_analysis["health"]["total_issues"],
                "critical": osi_analysis["health"]["severity_breakdown"]["critical"],
                "high": osi_analysis["health"]["severity_breakdown"]["high"]
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/enterprise")
async def get_enterprise_metrics():
    """Get enterprise-scale metrics for 370K devices across 20K+ locations"""
    return JSONResponse(content={
        "scale": {
            "total_devices": 370000,
            "locations": 20247,
            "organizations": 7,
            "device_types": {
                "fortigates": 20247,
                "fortiswitches": 45000,
                "access_points": 85000,
                "clients": 219753
            }
        },
        "infrastructure": {
            "redis_cluster": "6 nodes",
            "postgres_cluster": "primary + 2 replicas",
            "neo4j_cluster": "3 core nodes",
            "monitoring": "prometheus + grafana"
        },
        "market_opportunity": {
            "validated_market_size": "$2.8B",
            "saas_pricing": "$199-999/month",
            "target_arr": "$180K-2.4M",
            "deployment": "de-risked side hustle until $100K ARR"
        },
        "competitive_advantage": {
            "cost_savings": "60-80% vs SolarWinds/Cisco DNA Center",
            "agents": 14,
            "tools": 13,
            "framework": "AutoGen",
            "grant_deadline": "2024-12-15"
        }
    })


# Export router
__all__ = ["router"]
