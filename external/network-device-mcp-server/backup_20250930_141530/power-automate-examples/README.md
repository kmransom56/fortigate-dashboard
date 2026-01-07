# Power Automate Integration Examples
# Restaurant Network Management (Arbys, BWW, Sonic)

## Overview

These examples show how to integrate your Network Device MCP Server with Power Automate for restaurant network management across your three FortiManager instances (Arbys, BWW, Sonic).

## Method 1: HTTP REST API Integration

### Setup: Create API Wrapper

First, create a simple Flask REST API that wraps your MCP tools:

```python
# api_wrapper.py - Run this as a service
from flask import Flask, jsonify, request
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

from config import get_config
from platforms.fortimanager import FortiManagerManager

app = Flask(__name__)
config = get_config()
fm_manager = FortiManagerManager()

@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy", "service": "restaurant-network-mcp"})

@app.route('/api/restaurants')
def get_restaurants():
    """Get list of restaurant networks"""
    restaurants = []
    for fm in config.fortimanager_instances:
        restaurants.append({
            "name": fm["name"],
            "host": fm["host"],
            "brand": fm["name"]  # Arbys, BWW, Sonic
        })
    return jsonify(restaurants)

@app.route('/api/restaurant/<restaurant_name>/devices')
def get_restaurant_devices(restaurant_name):
    """Get devices for a specific restaurant brand"""
    # This would call your MCP server tools
    fm_config = config.get_fortimanager_by_name(restaurant_name)
    if not fm_config:
        return jsonify({"error": "Restaurant not found"}), 404
    
    # In a real implementation, you'd call the async MCP tools
    return jsonify({
        "restaurant": restaurant_name,
        "host": fm_config["host"],
        "devices": []  # Would be populated by MCP call
    })

@app.route('/api/restaurant/<restaurant_name>/deploy-policy', methods=['POST'])
def deploy_policy(restaurant_name):
    """Deploy policy to restaurant locations"""
    data = request.json
    package = data.get('package')
    devices = data.get('devices', [])
    
    # This would call your MCP policy deployment tool
    return jsonify({
        "status": "deployment_started",
        "restaurant": restaurant_name,
        "package": package,
        "target_devices": len(devices)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

## Power Automate Flow Examples

### 1. Restaurant Network Health Monitor

**Trigger**: Recurrence (every 15 minutes)

**Steps**:
1. **HTTP Request**: `GET http://localhost:5000/api/restaurants`
2. **For each restaurant**:
   - **HTTP Request**: `GET http://localhost:5000/api/restaurant/{restaurant}/devices`
   - **Condition**: If any devices are offline
   - **Send email/Teams message**: Alert network team with restaurant and device details

**Business Value**: Proactive monitoring of network infrastructure across all restaurant locations

---

### 2. Policy Deployment Workflow

**Trigger**: SharePoint list item created (Policy Deployment Requests)

**SharePoint Columns**:
- Restaurant Brand (Choice: Arbys, BWW, Sonic, All)
- Policy Package Name (Text)
- Target Locations (Multi-choice)
- Requestor Email (Person)
- Priority (Choice: Low, Medium, High)

**Steps**:
1. **Get item details** from SharePoint
2. **Condition**: If Restaurant Brand = "All"
   - **For each brand** (Arbys, BWW, Sonic):
     - **HTTP Request**: `POST http://localhost:5000/api/restaurant/{brand}/deploy-policy`
   - **Else**: Deploy to specific brand only
3. **Update SharePoint item**: Status = "Deployed"
4. **Send email**: Confirmation to requestor with deployment details

**Business Value**: Centralized policy management across restaurant brands

---

### 3. Security Event Aggregation

**Trigger**: Recurrence (every 5 minutes)

**Steps**:
1. **For each FortiManager** (Arbys, BWW, Sonic):
   - **HTTP Request**: Get security events
   - **Parse JSON**: Extract high-priority events
2. **Condition**: If high-priority security events found
   - **Create item**: In Security Incidents SharePoint list
   - **Send Teams message**: To security channel with restaurant location
   - **Create ServiceNow incident**: If enabled

**Business Value**: Real-time security monitoring across all restaurant locations

---

### 4. Weekly Network Inventory Report

**Trigger**: Recurrence (weekly, Monday 8 AM)

**Steps**:
1. **Create Excel file**: Network Inventory Template
2. **For each restaurant brand**:
   - **HTTP Request**: Get device inventory
   - **Add rows to Excel**: Device details by brand
3. **Send email**: Excel attachment to management
4. **Save to SharePoint**: Document library with timestamp

**Business Value**: Regular inventory tracking and compliance reporting

---

## Method 2: File-Based Integration

### Setup: MCP Server writes status files

Create a scheduled script that exports data for Power Automate:

```python
# export_for_power_automate.py
import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys

sys.path.append("src")
from config import get_config
from platforms.fortimanager import FortiManagerManager

async def export_restaurant_status():
    config = get_config()
    fm_manager = FortiManagerManager()
    
    status_data = {
        "timestamp": datetime.now().isoformat(),
        "restaurants": []
    }
    
    for fm in config.fortimanager_instances:
        try:
            devices = await fm_manager.get_managed_devices(
                fm["host"], fm["username"], fm["password"]
            )
            
            restaurant_status = {
                "name": fm["name"],
                "host": fm["host"],
                "status": "online",
                "device_count": len(devices),
                "offline_devices": [
                    d["name"] for d in devices 
                    if d.get("status") != "online"
                ]
            }
            
            status_data["restaurants"].append(restaurant_status)
            
        except Exception as e:
            status_data["restaurants"].append({
                "name": fm["name"],
                "host": fm["host"],
                "status": "error",
                "error": str(e)
            })
    
    # Write to file that Power Automate monitors
    output_file = Path("C:/temp/restaurant_network_status.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(status_data, f, indent=2)
    
    print(f"Exported status for {len(status_data['restaurants'])} restaurants")

if __name__ == "__main__":
    asyncio.run(export_restaurant_status())
```

### Power Automate File Monitor Flow

**Trigger**: When a file is modified (C:/temp/restaurant_network_status.json)

**Steps**:
1. **Get file content**: Parse JSON status data
2. **For each restaurant**:
   - **Condition**: If status = "error" or offline_devices > 0
   - **Create alert**: Teams message or email with restaurant details
3. **Update dashboard**: SharePoint list with current status

---

## Method 3: Database Integration

### Setup: Export to SQL Server

```python
# export_to_database.py
import asyncio
import pyodbc
from datetime import datetime

async def export_to_sql():
    # Connection to SQL Server
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=your-sql-server;'
        'DATABASE=RestaurantNetworking;'
        'Trusted_Connection=yes;'
    )
    
    cursor = conn.cursor()
    
    # Export restaurant device status
    for fm in config.fortimanager_instances:
        devices = await get_devices(fm)  # Your MCP call
        
        for device in devices:
            cursor.execute("""
                INSERT INTO DeviceStatus 
                (Restaurant, DeviceName, Status, LastSeen, IPAddress)
                VALUES (?, ?, ?, ?, ?)
            """, fm["name"], device["name"], device["status"], 
                datetime.now(), device.get("ip"))
    
    conn.commit()
```

### Power Automate SQL Flow

**Trigger**: Recurrence (every hour)

**Steps**:
1. **Get rows**: From DeviceStatus table where LastSeen > 1 hour ago
2. **Condition**: If any devices are offline
3. **Create dashboard update**: Power BI or SharePoint
4. **Send escalation**: If critical devices offline > 4 hours

---

## Advanced Restaurant-Specific Workflows

### 5. Peak Hours Network Monitoring

Monitor network performance during restaurant peak hours:

**Trigger**: Recurrence (weekdays 11 AM - 2 PM, 5 PM - 9 PM)

**Business Logic**:
- Higher frequency monitoring during meal rushes
- Different alert thresholds for peak vs. off-peak
- Automatic escalation for POS system connectivity

### 6. New Store Rollout Automation

Automate network setup for new restaurant locations:

**Trigger**: SharePoint list item (New Store Openings)

**Steps**:
1. **Create FortiManager configuration**: For new location
2. **Deploy standard policies**: Based on restaurant brand
3. **Configure monitoring**: Add to health check schedules
4. **Generate documentation**: Network setup guide

### 7. Compliance Reporting

Generate PCI DSS compliance reports for restaurant payment systems:

**Trigger**: Monthly schedule

**Steps**:
1. **Audit security policies**: Across all locations
2. **Check PCI requirements**: Firewall rules, network segmentation
3. **Generate compliance report**: By restaurant brand
4. **Submit to compliance team**: Automated delivery

---

## Implementation Tips

### Security Considerations
- Use dedicated service accounts for API access
- Implement API key rotation in Power Automate
- Log all policy deployments for audit trails
- Restrict network access to MCP server

### Monitoring and Alerting
- Set up different alert levels (Info, Warning, Critical)
- Create escalation paths for different restaurant brands
- Monitor MCP server health and availability
- Track policy deployment success rates

### Performance Optimization
- Cache FortiManager responses to reduce API calls
- Use batched operations for bulk policy deployments  
- Implement retry logic for failed connections
- Schedule heavy operations during off-peak hours

### Business Continuity
- Create backup network configurations
- Automated failover procedures
- Emergency contact procedures by restaurant brand
- Disaster recovery testing schedules

---

## Getting Started

1. **Choose Integration Method**: Start with HTTP REST API for easiest testing
2. **Set up API wrapper**: Use the Flask example above
3. **Create simple flow**: Start with restaurant health monitoring
4. **Test with one brand**: Validate with Arbys first, then expand
5. **Add complexity**: Gradually add more sophisticated workflows

This integration gives you centralized visibility and control over network infrastructure across all your restaurant brands while maintaining the flexibility to handle brand-specific requirements.
