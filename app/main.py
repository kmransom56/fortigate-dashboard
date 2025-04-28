from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os

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
    switches = get_fortiswitches()
    return templates.TemplateResponse("switches.html", {"request": request, "switches": switches})
