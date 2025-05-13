from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os
from fastapi import FastAPI, Request, HTTPException
# Load environment variables from .env file
load_dotenv()

from app.api import fortigate  # your existing fortigate routes
from app.services.fortigate_service import get_interfaces  # to get interfaces for dashboard
from app.services.fortiswitch_service import get_fortiswitches  # to get FortiSwitch information

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="app/templates")

# Include Fortigate router
app.include_router(fortigate.router)

# 🏠 Route for Home "/"
@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 📊 Route for Dashboard "/dashboard"
@app.get("/dashboard", response_class=HTMLResponse)
async def show_dashboard(request: Request):
    interfaces = get_interfaces()
    return templates.TemplateResponse("dashboard.html", {"request": request, "interfaces": interfaces})

# 🔄 Route for FortiSwitch Dashboard "/switches"
@app.get("/switches", response_class=HTMLResponse)
async def show_switches(request: Request):
    # Simply return the fixed template - all data will be loaded via JavaScript
    return templates.TemplateResponse("switches.html", {"request": request})

# API endpoint for FortiSwitch data
@app.get("/api/switches")
async def get_switches_api():
    # Get FortiSwitch data
    switches_data = get_fortiswitches()
    
    # Process the data similar to the HTML route
    if isinstance(switches_data, dict) and 'success' in switches_data:
        if not switches_data.get('success', False):
            return {"success": False, "error": switches_data.get('message', 'Failed to retrieve FortiSwitch data')}
        switches = switches_data.get('switches', [])
    elif isinstance(switches_data, dict) and 'results' in switches_data:
        switches = switches_data['results']
    elif isinstance(switches_data, list):
        switches = switches_data
    else:
        switches = []
    
    # Process each switch to ensure it has the expected structure
    processed_switches = []
    for switch in switches:
        if not isinstance(switch, dict):
            continue
            
        switch_data = {
            'serial': switch.get('serial', 'Unknown'),
            'name': switch.get('name', switch.get('switch-id', 'Unknown')),
            'model': switch.get('model', switch.get('os_version', '').split('-')[0] if switch.get('os_version') else 'Unknown'),
            'status': 'online' if switch.get('status', '').lower() in ['connected', 'authorized/up', 'authorized'] else 'offline',
            'version': switch.get('version', switch.get('os_version', 'Unknown')),
            'ip': switch.get('ip', switch.get('connecting_from', 'Unknown')),
            'mac': switch.get('mac', 'Unknown'),
            'ports': [],
            'connected_devices': []
        }
        
        # Process ports and connected devices
        if 'ports' in switch and isinstance(switch['ports'], list):
            for port in switch['ports']:
                port_info = {
                    'name': port.get('interface', 'Unknown'),
                    'status': port.get('status', 'Unknown'),
                    'speed': port.get('speed', 0),
                    'duplex': port.get('duplex', 'Unknown'),
                    'vlan': port.get('vlan', 'Unknown')
                }
                switch_data['ports'].append(port_info)
                
                if port.get('status') == 'up':
                    device = {
                        'port': port.get('interface', 'Unknown'),
                        'device_name': f"Device on {port.get('interface', 'Unknown')}",
                        'device_mac': 'Unknown',
                        'device_ip': 'Unknown',
                        'device_type': 'Network Device',
                        'vendor': 'Unknown',
                        'vendor_icon': '',
                        'vendor_color': '#505050'
                    }
                    switch_data['connected_devices'].append(device)
        
        processed_switches.append(switch_data)
    
    return {"success": True, "switches": processed_switches}
 #🔄 Route for FortiSwitch IP Change Form "/switches/change-ip/{switch_serial}"
@app.get("/switches/change-ip/{switch_serial}", response_class=HTMLResponse)
async def show_switch_ip_change_form(request: Request, switch_serial: str):
    switches = get_fortiswitches()
    
    # Find the specific switch by serial number
    switch = next((s for s in switches if s.get('serial') == switch_serial), None)
    
    if not switch:
        raise HTTPException(status_code=404, detail=f"FortiSwitch with serial {switch_serial} not found")
    
    return templates.TemplateResponse("change_ip.html", {"request": request, "switch": switch})
@app.get("/debug/switches", response_class=HTMLResponse)
async def debug_switches(request: Request):
    switches = get_fortiswitches()
    return templates.TemplateResponse("simple.html", {"request": request, "switches": switches})

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

if __name__ == "__main__":
    main()