#!/usr/bin/env python3
"""
REST API Wrapper for Network Device MCP Server
Designed for Restaurant Network Management (Arbys, BWW, Sonic)
This creates HTTP endpoints that Power Automate can easily call
"""

from flask import Flask, jsonify, request, abort
import asyncio
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from config import get_config
from platforms.fortimanager import FortiManagerManager
from platforms.meraki import MerakiManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Global instances
config = get_config()
fm_manager = FortiManagerManager()
meraki_manager = MerakiManager()

# Thread pool for async operations
executor = ThreadPoolExecutor(max_workers=4)

def run_async(coro):
    """Helper to run async functions in Flask routes"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# Health Check Endpoints
@app.route('/api/health')
def health_check():
    """Basic health check"""
    return jsonify({
        "status": "healthy",
        "service": "restaurant-network-mcp-api",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.route('/api/config/status')
def config_status():
    """Get configuration status"""
    try:
        validation = config.validate_config()
        return jsonify({
            "fortimanager_instances": len(config.fortimanager_instances),
            "fortigate_devices": len(config.fortigate_devices),
            "meraki_configured": config.has_meraki_config(),
            "validation": validation,
            "restaurants": [
                {"name": fm["name"], "host": fm["host"]} 
                for fm in config.fortimanager_instances
            ]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Restaurant Management Endpoints
@app.route('/api/restaurants')
def get_restaurants():
    """Get list of restaurant networks (FortiManager instances)"""
    try:
        restaurants = []
        for fm in config.fortimanager_instances:
            restaurants.append({
                "name": fm["name"],
                "host": fm["host"], 
                "brand": fm["name"],  # Arbys, BWW, Sonic
                "description": fm.get("description", f"{fm['name']} restaurant network")
            })
        
        return jsonify({
            "count": len(restaurants),
            "restaurants": restaurants
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/restaurant/<restaurant_name>')
def get_restaurant_info(restaurant_name):
    """Get information about a specific restaurant network"""
    try:
        fm_config = config.get_fortimanager_by_name(restaurant_name)
        if not fm_config:
            abort(404, description=f"Restaurant '{restaurant_name}' not found")
        
        return jsonify({
            "name": fm_config["name"],
            "host": fm_config["host"],
            "brand": fm_config["name"],
            "description": fm_config.get("description", "")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/restaurant/<restaurant_name>/devices')
def get_restaurant_devices(restaurant_name):
    """Get devices managed by a restaurant's FortiManager"""
    try:
        fm_config = config.get_fortimanager_by_name(restaurant_name)
        if not fm_config:
            abort(404, description=f"Restaurant '{restaurant_name}' not found")
        
        # Run async operation
        def get_devices():
            return run_async(fm_manager.get_managed_devices(
                fm_config["host"], fm_config["username"], fm_config["password"]
            ))
        
        devices = executor.submit(get_devices).result(timeout=30)
        
        # Categorize devices
        online_devices = [d for d in devices if d.get("status") == "online"]
        offline_devices = [d for d in devices if d.get("status") != "online"]
        
        return jsonify({
            "restaurant": restaurant_name,
            "host": fm_config["host"],
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_devices": len(devices),
                "online_devices": len(online_devices),
                "offline_devices": len(offline_devices)
            },
            "devices": devices,
            "offline_device_names": [d.get("name", "Unknown") for d in offline_devices]
        })
        
    except Exception as e:
        logger.error(f"Error getting devices for {restaurant_name}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/restaurant/<restaurant_name>/devices/status')
def get_restaurant_device_status(restaurant_name):
    """Get simplified device status for monitoring (Power Automate friendly)"""
    try:
        fm_config = config.get_fortimanager_by_name(restaurant_name)
        if not fm_config:
            abort(404, description=f"Restaurant '{restaurant_name}' not found")
        
        def get_devices():
            return run_async(fm_manager.get_managed_devices(
                fm_config["host"], fm_config["username"], fm_config["password"]
            ))
        
        devices = executor.submit(get_devices).result(timeout=30)
        
        # Simplified status for Power Automate
        status = {
            "restaurant": restaurant_name,
            "timestamp": datetime.now().isoformat(),
            "health": "healthy",
            "total_devices": len(devices),
            "online_devices": 0,
            "offline_devices": 0,
            "critical_offline": [],
            "warnings": []
        }
        
        for device in devices:
            if device.get("status") == "online":
                status["online_devices"] += 1
            else:
                status["offline_devices"] += 1
                device_name = device.get("name", "Unknown")
                status["critical_offline"].append(device_name)
        
        # Determine overall health
        if status["offline_devices"] > 0:
            status["health"] = "degraded" if status["offline_devices"] <= 2 else "critical"
        
        # Add warnings for common issues
        if status["offline_devices"] > 5:
            status["warnings"].append("High number of offline devices detected")
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting device status for {restaurant_name}: {e}")
        return jsonify({
            "restaurant": restaurant_name,
            "timestamp": datetime.now().isoformat(),
            "health": "error", 
            "error": str(e)
        }), 500

@app.route('/api/restaurant/<restaurant_name>/policies')
def get_restaurant_policies(restaurant_name):
    """Get policy packages for a restaurant"""
    try:
        fm_config = config.get_fortimanager_by_name(restaurant_name)
        if not fm_config:
            abort(404, description=f"Restaurant '{restaurant_name}' not found")
        
        adom = request.args.get('adom', 'root')
        
        def get_policies():
            return run_async(fm_manager.get_policy_packages(
                fm_config["host"], fm_config["username"], fm_config["password"], adom
            ))
        
        policies = executor.submit(get_policies).result(timeout=30)
        
        return jsonify({
            "restaurant": restaurant_name,
            "host": fm_config["host"],
            "adom": adom,
            "policy_count": len(policies),
            "policies": policies
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/restaurant/<restaurant_name>/deploy-policy', methods=['POST'])
def deploy_policy(restaurant_name):
    """Deploy policy package to restaurant devices"""
    try:
        fm_config = config.get_fortimanager_by_name(restaurant_name)
        if not fm_config:
            abort(404, description=f"Restaurant '{restaurant_name}' not found")
        
        data = request.get_json()
        if not data:
            abort(400, description="JSON payload required")
        
        package = data.get('package')
        devices = data.get('devices', [])
        adom = data.get('adom', 'root')
        
        if not package:
            abort(400, description="'package' field is required")
        
        def deploy():
            return run_async(fm_manager.install_policy_package(
                fm_config["host"], fm_config["username"], fm_config["password"],
                adom, package, devices
            ))
        
        result = executor.submit(deploy).result(timeout=60)
        
        return jsonify({
            "restaurant": restaurant_name,
            "host": fm_config["host"],
            "action": "policy_deployment",
            "package": package,
            "target_devices": devices,
            "adom": adom,
            "timestamp": datetime.now().isoformat(),
            "result": result
        })
        
    except Exception as e:
        logger.error(f"Error deploying policy for {restaurant_name}: {e}")
        return jsonify({"error": str(e)}), 500

# Multi-Restaurant Operations
@app.route('/api/all-restaurants/status')
def get_all_restaurant_status():
    """Get status summary for all restaurant networks"""
    try:
        all_status = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_restaurants": len(config.fortimanager_instances),
                "healthy": 0,
                "degraded": 0,
                "critical": 0,
                "errors": 0
            },
            "restaurants": []
        }
        
        def get_restaurant_status(fm_config):
            try:
                devices = run_async(fm_manager.get_managed_devices(
                    fm_config["host"], fm_config["username"], fm_config["password"]
                ))
                
                online = sum(1 for d in devices if d.get("status") == "online")
                offline = len(devices) - online
                
                if offline == 0:
                    health = "healthy"
                elif offline <= 2:
                    health = "degraded"
                else:
                    health = "critical"
                
                return {
                    "name": fm_config["name"],
                    "host": fm_config["host"],
                    "health": health,
                    "total_devices": len(devices),
                    "online_devices": online,
                    "offline_devices": offline
                }
                
            except Exception as e:
                return {
                    "name": fm_config["name"],
                    "host": fm_config["host"],
                    "health": "error",
                    "error": str(e)
                }
        
        # Get status for each restaurant
        for fm_config in config.fortimanager_instances:
            restaurant_status = get_restaurant_status(fm_config)
            all_status["restaurants"].append(restaurant_status)
            
            # Update summary counts
            health = restaurant_status["health"]
            if health in all_status["summary"]:
                all_status["summary"][health] += 1
        
        return jsonify(all_status)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/all-restaurants/deploy-policy', methods=['POST'])
def deploy_policy_all_restaurants():
    """Deploy policy package to all restaurant networks"""
    try:
        data = request.get_json()
        if not data:
            abort(400, description="JSON payload required")
        
        package = data.get('package')
        devices = data.get('devices', [])
        adom = data.get('adom', 'root')
        restaurants = data.get('restaurants', [])  # Empty means all
        
        if not package:
            abort(400, description="'package' field is required")
        
        # Determine target restaurants
        target_restaurants = config.fortimanager_instances
        if restaurants:
            target_restaurants = [
                fm for fm in config.fortimanager_instances 
                if fm["name"] in restaurants
            ]
        
        deployment_results = []
        
        for fm_config in target_restaurants:
            try:
                def deploy():
                    return run_async(fm_manager.install_policy_package(
                        fm_config["host"], fm_config["username"], fm_config["password"],
                        adom, package, devices
                    ))
                
                result = executor.submit(deploy).result(timeout=60)
                
                deployment_results.append({
                    "restaurant": fm_config["name"],
                    "host": fm_config["host"],
                    "status": "success",
                    "result": result
                })
                
            except Exception as e:
                deployment_results.append({
                    "restaurant": fm_config["name"],
                    "host": fm_config["host"],
                    "status": "error",
                    "error": str(e)
                })
        
        successful_deployments = sum(1 for r in deployment_results if r["status"] == "success")
        
        return jsonify({
            "action": "bulk_policy_deployment",
            "package": package,
            "target_devices": devices,
            "adom": adom,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_restaurants": len(deployment_results),
                "successful": successful_deployments,
                "failed": len(deployment_results) - successful_deployments
            },
            "results": deployment_results
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Meraki Endpoints (if configured)
@app.route('/api/meraki/organizations')
def get_meraki_organizations():
    """Get Meraki organizations"""
    try:
        if not config.has_meraki_config():
            abort(404, description="Meraki not configured")
        
        def get_orgs():
            return run_async(meraki_manager.get_organizations(config.meraki_api_key))
        
        orgs = executor.submit(get_orgs).result(timeout=30)
        
        return jsonify({
            "organization_count": len(orgs),
            "organizations": orgs
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/meraki/networks')
def get_meraki_networks():
    """Get Meraki networks"""
    try:
        if not config.has_meraki_config():
            abort(404, description="Meraki not configured")
        
        org_id = request.args.get('org_id', config.meraki_org_id)
        
        def get_networks():
            return run_async(meraki_manager.get_networks(config.meraki_api_key, org_id))
        
        networks = executor.submit(get_networks).result(timeout=30)
        
        return jsonify({
            "organization_id": org_id,
            "network_count": len(networks),
            "networks": networks
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found", "message": str(error.description)}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request", "message": str(error.description)}), 400

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print("🍽️  Restaurant Network Management API Server")
    print("=" * 45)
    print(f"FortiManager instances: {len(config.fortimanager_instances)}")
    for fm in config.fortimanager_instances:
        print(f"  - {fm['name']}: {fm['host']}")
    print(f"Meraki configured: {config.has_meraki_config()}")
    print()
    print("API Endpoints available:")
    print("  GET  /api/health - Health check")
    print("  GET  /api/restaurants - List all restaurants")
    print("  GET  /api/restaurant/<name>/devices - Get restaurant devices")
    print("  GET  /api/restaurant/<name>/devices/status - Device status summary")
    print("  POST /api/restaurant/<name>/deploy-policy - Deploy policy")
    print("  GET  /api/all-restaurants/status - All restaurant status")
    print("  POST /api/all-restaurants/deploy-policy - Bulk policy deployment")
    print()
    print("🔗 Power Automate Integration:")
    print("  Use these endpoints in HTTP connectors")
    print("  Monitor /api/all-restaurants/status for health checks")
    print("  Use /api/restaurant/<name>/deploy-policy for deployments")
    print()
    print("Starting server on http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
