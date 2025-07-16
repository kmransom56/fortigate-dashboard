from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from app.api import fortigate  # your existing fortigate routes
from app.services.fortigate_service import (
    get_interfaces,
    get_cloud_status,
)  # to get interfaces and cloud status for dashboard
from app.services.fortiswitch_service import (
    get_fortiswitches,
)  # to get FortiSwitch information


# Helper to aggregate device details for dashboard
def get_all_device_details():
    switches = get_fortiswitches()
    devices = []
    for switch in switches:
        for port in switch.get("ports", []):
            for dev in port.get("connected_devices", []):
                # Add switch and port context to device
                dev_copy = dev.copy()
                dev_copy["switch_serial"] = switch.get("serial")
                dev_copy["switch_name"] = switch.get("name")
                dev_copy["port_name"] = port.get("name")
                # If icon_path not present, try to enrich from DB
                if not dev_copy.get("icon_path"):
                    from app.utils.icon_db import get_icon

                    icon_info = get_icon(manufacturer=dev_copy.get("manufacturer"))
                    if not icon_info:
                        icon_info = get_icon(device_type=dev_copy.get("device_type"))
                    if icon_info:
                        dev_copy["icon_path"] = icon_info["icon_path"]
                        dev_copy["icon_title"] = icon_info["title"]
                devices.append(dev_copy)
    return devices


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
    device_details = get_all_device_details()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "interfaces": interfaces,
            "device_details": device_details,
        },
    )


# API endpoint for cloud status
@app.get("/api/cloud_status")
async def api_cloud_status():
    status = get_cloud_status()
    return {"status": status}


# 🔄 Route for FortiSwitch Dashboard "/switches"
@app.get("/switches", response_class=HTMLResponse)
async def switches_page(request: Request):
    switches = get_fortiswitches()  # Pulls live data
    return templates.TemplateResponse(
        "switches.html", {"request": request, "switches": switches}
    )
