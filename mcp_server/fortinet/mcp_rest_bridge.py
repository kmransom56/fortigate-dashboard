#!/usr/bin/env python3
"""
MCP to REST API Bridge
Exposes your Fortinet MCP server as REST endpoints for curl access
"""

from flask import Flask, request, jsonify
import sys
import os
import json
from datetime import datetime

# Add MCP server to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fortinet_server_enhanced import fg_api, api_parser, discovered_endpoints

app = Flask(__name__)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        status = fg_api.test_connection()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'fortigate_connection': status,
            'total_endpoints': len(discovered_endpoints)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/endpoints', methods=['GET'])
def list_endpoints():
    """List all discovered endpoints"""
    category = request.args.get('category', 'all')
    
    if category == 'all':
        endpoints = discovered_endpoints
    else:
        endpoints = {k: v for k, v in discovered_endpoints.items() 
                    if v.get('category') == category}
    
    return jsonify({
        'total': len(endpoints),
        'category': category,
        'endpoints': endpoints
    })

@app.route('/api/fortigate/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def fortigate_proxy(endpoint):
    """Proxy requests to FortiGate API"""
    try:
        method = request.method
        data = request.get_json() if request.is_json else None
        
        result = fg_api._make_request(method, endpoint, data)
        
        return jsonify({
            'endpoint': endpoint,
            'method': method,
            'timestamp': datetime.now().isoformat(),
            'result': result
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'endpoint': endpoint,
            'method': method,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/devices', methods=['GET'])
def get_detected_devices():
    """Get detected devices (your original curl functionality)"""
    try:
        devices = fg_api._make_request("GET", "monitor/switch-controller/detected-device")
        return jsonify({
            'endpoint': 'monitor/switch-controller/detected-device',
            'timestamp': datetime.now().isoformat(),
            'devices': devices
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """Get FortiGate system status"""
    try:
        status = fg_api._make_request("GET", "monitor/system/status")
        return jsonify({
            'endpoint': 'monitor/system/status',
            'timestamp': datetime.now().isoformat(),
            'status': status
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/dynamic/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def dynamic_endpoint(endpoint):
    """Dynamically call any discovered endpoint"""
    try:
        # Find the endpoint in discovered endpoints
        matching_endpoints = [k for k, v in discovered_endpoints.items() 
                             if v.get('path') == endpoint]
        
        if not matching_endpoints:
            return jsonify({
                'error': f'Endpoint {endpoint} not found in discovered endpoints',
                'available_endpoints': list(discovered_endpoints.keys())[:10]
            }), 404
        
        method = request.method
        data = request.get_json() if request.is_json else None
        
        result = fg_api._make_request(method, endpoint, data)
        
        return jsonify({
            'endpoint': endpoint,
            'method': method,
            'discovered': True,
            'timestamp': datetime.now().isoformat(),
            'result': result
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'endpoint': endpoint,
            'method': method,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get endpoint categories"""
    categories = {}
    for key, info in discovered_endpoints.items():
        category = info.get('category', 'uncategorized')
        if category not in categories:
            categories[category] = []
        categories[category].append({
            'key': key,
            'path': info.get('path'),
            'method': info.get('method')
        })
    
    return jsonify({
        'total_categories': len(categories),
        'categories': categories
    })

if __name__ == '__main__':
    print("🚀 Starting Fortinet MCP REST Bridge")
    print("📊 Available endpoints:")
    print(f"   GET  /api/health - Health check")
    print(f"   GET  /api/endpoints - List all discovered endpoints")
    print(f"   GET  /api/devices - Your original curl functionality")
    print(f"   GET  /api/system/status - FortiGate system status")
    print(f"   ALL  /api/fortigate/<endpoint> - Proxy to FortiGate")
    print(f"   ALL  /api/dynamic/<endpoint> - Dynamic endpoint calling")
    print(f"   GET  /api/categories - Endpoint categories")
    print(f"🌐 Server starting on http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)