from bs4 import BeautifulSoup
import json

# Path to the scraped HTML file
SCRAPED_HTML_PATH = "../../scraped_map.html"

# Example parser for FortiGate topology HTML
    # Try to parse actual HTML, fallback to demo data if not found
    try:
        with open(SCRAPED_HTML_PATH, "r", encoding="utf-8") as f:
            html = f.read()
        soup = BeautifulSoup(html, "html.parser")
        devices = []
        connections = []
        # Example selectors, adjust for your HTML
        for i, device in enumerate(soup.select(".device-node")):
            device_type = device.get("data-type", "endpoint")
            color = {
                "fortigate": "#2196f3",
                "fortiswitch": "#ff9800",
                "endpoint": "#4caf50",
                "server": "#9c27b0"
            }.get(device_type, "#2196f3")
            device_count = int(device.get("data-count", 1))
            devices.append({
                "id": device.get("id", f"device_{i}"),
                "type": device_type,
                "name": device.get_text(strip=True),
                "position": {
                    "x": int(device.get("data-x", 100 + i * 200)),
                    "y": int(device.get("data-y", 100 + i * 150)),
                },
                "details": {
                    "deviceCount": device_count,
                    "color": color
                }
            })
        for conn in soup.select(".connection-link"):
            connections.append({
                "from": conn.get("data-from"),
                "to": conn.get("data-to")
            })
        if devices:
            return {"devices": devices, "connections": connections}
    except Exception:
        pass
    # Fallback demo data
    devices = [
        {
            "id": "fortigate_main",
            "type": "fortigate",
            "name": "FortiGate",
            "position": {"x": 400, "y": 100},
            "details": {"deviceCount": 1, "color": "#2196f3"}
        },
        {
            "id": "switch_1",
            "type": "fortiswitch",
            "name": "Switch 1",
            "position": {"x": 300, "y": 300},
            "details": {"deviceCount": 3, "color": "#ff9800"}
        },
        {
            "id": "switch_2",
            "type": "fortiswitch",
            "name": "Switch 2",
            "position": {"x": 500, "y": 300},
            "details": {"deviceCount": 6, "color": "#ff9800"}
        },
        {
            "id": "endpoint_1",
            "type": "endpoint",
            "name": "Endpoint",
            "position": {"x": 400, "y": 500},
            "details": {"deviceCount": 12, "color": "#4caf50"}
        }
    ]
    connections = [
        {"from": "fortigate_main", "to": "switch_1"},
        {"from": "fortigate_main", "to": "switch_2"},
        {"from": "switch_1", "to": "endpoint_1"},
        {"from": "switch_2", "to": "endpoint_1"}
    ]
    return {"devices": devices, "connections": connections}
